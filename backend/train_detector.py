import json
import logging
import time
from pathlib import Path

import timm
import torch
import torch.nn as nn
import torch.optim as optim
from PIL import Image
from torch.utils.data import DataLoader, Dataset, random_split
from torchvision import transforms

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("train")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATASET_DIR = Path("dataset_orig")
MODEL_PATH  = Path("detector_model.pth")
HISTORY_PATH = Path("training_history.json")

IMAGE_SIZE  = 224
BATCH_SIZE  = 16
EPOCHS      = 20
LR          = 5e-4
VAL_SPLIT   = 0.2
NUM_WORKERS = 0        # keep 0 to avoid multiprocessing issues
MIN_REAL_ACC = 40.0    # minimum real-class accuracy for a checkpoint to be saved


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class ImageDataset(Dataset):
    """Flat image dataset with binary labels (0 = real, 1 = fake)."""

    _EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

    def __init__(self, samples: list[tuple[Path, int]], transform) -> None:
        self.samples   = samples
        self.transform = transform

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        path, label = self.samples[idx]
        image = Image.open(path).convert("RGB")
        return self.transform(image), label


def _collect_samples(root: Path) -> list[tuple[Path, int]]:
    exts    = ImageDataset._EXTENSIONS
    samples = []
    for folder in root.iterdir():
        if not folder.is_dir():
            continue
        label = 0 if folder.name == "real" else 1
        samples.extend(
            (f, label) for f in folder.iterdir() if f.suffix.lower() in exts
        )
    real_n = sum(1 for _, l in samples if l == 0)
    fake_n = sum(1 for _, l in samples if l == 1)
    log.info("Dataset — real: %d  fake: %d  total: %d", real_n, fake_n, len(samples))
    return samples


# ---------------------------------------------------------------------------
# Transforms
# ---------------------------------------------------------------------------
_train_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.RandomHorizontalFlip(),
    transforms.ColorJitter(brightness=0.1, contrast=0.1),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

_val_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])


# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
def _build_model() -> nn.Module:
    """
    Load MobileNetV4-Conv-Small with ImageNet weights, freeze the backbone
    except for the last two child modules, and attach a binary classification
    head.
    """
    backbone = timm.create_model(
        "mobilenetv4_conv_small.e2400_r224_in1k",
        pretrained=True,
        num_classes=0,
    )

    for param in backbone.parameters():
        param.requires_grad = False

    # Unfreeze last 4 blocks for deeper fine-tuning
    for layer in list(backbone.children())[-4:]:
        for param in layer.parameters():
            param.requires_grad = True

    backbone.eval()
    with torch.no_grad():
        feat_dim = backbone(torch.zeros(1, 3, IMAGE_SIZE, IMAGE_SIZE)).shape[1]
    backbone.train()
    log.info("Backbone output dimension: %d", feat_dim)

    head = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(feat_dim, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(256, 64),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.1),
        nn.Linear(64, 1),
    )
    return nn.Sequential(backbone, head)


# ---------------------------------------------------------------------------
# Training loop
# ---------------------------------------------------------------------------
def _epoch_metrics(preds, labels):
    """Return (correct, real_correct, real_total, fake_correct, fake_total)."""
    correct      = (preds == labels).sum().item()
    real_mask    = (labels == 0).squeeze()
    fake_mask    = (labels == 1).squeeze()
    real_correct = (preds[real_mask] == labels[real_mask]).sum().item() if real_mask.any() else 0
    real_total   = real_mask.sum().item()
    fake_correct = (preds[fake_mask] == labels[fake_mask]).sum().item() if fake_mask.any() else 0
    fake_total   = fake_mask.sum().item()
    return correct, real_correct, real_total, fake_correct, fake_total


def train() -> list[dict]:
    device  = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    log.info("Training device: %s", device)

    samples = _collect_samples(DATASET_DIR)
    n_val   = int(len(samples) * VAL_SPLIT)
    n_train = len(samples) - n_val

    full_ds  = ImageDataset(samples, _train_transform)
    train_ds, val_ds = random_split(
        full_ds, [n_train, n_val],
        generator=torch.Generator().manual_seed(42),
    )
    val_ds.dataset = ImageDataset(samples, _val_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE,
                              shuffle=True,  num_workers=NUM_WORKERS,
                              drop_last=True)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE,
                              shuffle=False, num_workers=NUM_WORKERS)

    log.info("Split — train: %d  val: %d", len(train_ds), len(val_ds))

    model = _build_model().to(device)

    n_real     = sum(1 for _, l in samples if l == 0)
    n_fake     = sum(1 for _, l in samples if l == 1)
    pos_weight = torch.tensor([n_real / n_fake], device=device)
    criterion  = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    optimizer  = optim.Adam(
        filter(lambda p: p.requires_grad, model.parameters()), lr=LR
    )
    scheduler  = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS, eta_min=1e-6)

    best_f1  = 0.0
    history  = []

    for epoch in range(1, EPOCHS + 1):
        t0 = time.time()

        # Training pass
        model.train()
        train_correct = train_total = 0
        for imgs, labels in train_loader:
            imgs   = imgs.to(device)
            labels = labels.float().unsqueeze(1).to(device)
            optimizer.zero_grad()
            logits = model(imgs)
            loss   = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            preds          = (torch.sigmoid(logits) >= 0.5).float()
            train_correct += (preds == labels).sum().item()
            train_total   += imgs.size(0)

        # Validation pass
        model.eval()
        val_correct = val_total = 0
        real_correct = real_total = fake_correct = fake_total = 0

        with torch.no_grad():
            for imgs, labels in val_loader:
                imgs   = imgs.to(device)
                labels = labels.float().unsqueeze(1).to(device)
                logits = model(imgs)
                preds  = (torch.sigmoid(logits) >= 0.5).float()
                val_correct += (preds == labels).sum().item()
                val_total   += imgs.size(0)
                c, rc, rt, fc, ft = _epoch_metrics(preds, labels)
                real_correct += rc; real_total += rt
                fake_correct += fc; fake_total += ft

        scheduler.step()

        train_acc = train_correct / train_total * 100
        val_acc   = val_correct   / val_total   * 100
        real_acc  = real_correct  / real_total  * 100 if real_total > 0 else 0.0
        fake_acc  = fake_correct  / fake_total  * 100 if fake_total > 0 else 0.0

        tp   = fake_correct
        fp   = real_total - real_correct
        fn   = fake_total - fake_correct
        prec = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

        log.info(
            "Epoch %2d/%d  train=%.1f%%  val=%.1f%%  "
            "real=%.1f%%  fake=%.1f%%  F1=%.1f%%  (%.0fs)",
            epoch, EPOCHS, train_acc, val_acc, real_acc, fake_acc, f1,
            time.time() - t0,
        )

        history.append({
            "epoch": epoch,
            "train_acc": round(train_acc, 2),
            "val_acc":   round(val_acc,   2),
            "real_acc":  round(real_acc,  2),
            "fake_acc":  round(fake_acc,  2),
            "f1":        round(f1,        2),
        })

        if f1 > best_f1 and real_acc >= MIN_REAL_ACC:
            best_f1 = f1
            torch.save({
                "model_state": model.state_dict(),
                "epoch":       epoch,
                "val_acc":     round(val_acc,  2),
                "real_acc":    round(real_acc, 2),
                "fake_acc":    round(fake_acc, 2),
                "f1":          round(f1,       2),
            }, MODEL_PATH)
            log.info(
                "  → checkpoint saved  F1=%.1f%%  real=%.1f%%  fake=%.1f%%",
                f1, real_acc, fake_acc,
            )

    log.info("Training complete — best F1: %.1f%%", best_f1)
    log.info("Checkpoint: %s", MODEL_PATH.resolve())

    # Find best epoch entry
    best_entry = max(history, key=lambda e: e["f1"])

    report = {
        "model":       "MobileNetV4-Conv-Small (timm/mobilenetv4_conv_small.e2400_r224_in1k)",
        "dataset_dir": str(DATASET_DIR),
        "dataset": {
            "real":  sum(1 for _, l in samples if l == 0),
            "fake":  sum(1 for _, l in samples if l == 1),
            "total": len(samples),
        },
        "hyperparameters": {
            "epochs":      EPOCHS,
            "batch_size":  BATCH_SIZE,
            "lr":          LR,
            "val_split":   VAL_SPLIT,
            "scheduler":   "CosineAnnealingLR",
            "unfrozen_blocks": 4,
            "optimizer":   "Adam",
            "image_size":  IMAGE_SIZE,
        },
        "best_checkpoint": {
            "epoch":    best_entry["epoch"],
            "val_acc":  best_entry["val_acc"],
            "real_acc": best_entry["real_acc"],
            "fake_acc": best_entry["fake_acc"],
            "f1":       best_entry["f1"],
        },
        "training_history": history,
    }

    HISTORY_PATH.write_text(json.dumps(report, indent=2))
    log.info("Training report saved to: %s", HISTORY_PATH.resolve())
    return history


if __name__ == "__main__":
    train()