import sys
import json
import logging
from pathlib import Path

import torch
import torch.nn as nn
import timm
from torchvision import transforms
from PIL import Image

logging.basicConfig(level=logging.WARNING)

MODEL_PATH = Path("detector_model.pth")
IMAGE_SIZE = 224

_transform = transforms.Compose([
    transforms.Resize((IMAGE_SIZE, IMAGE_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])


def _build_model() -> nn.Module:
    """Construct the MobileNetV4 backbone with binary classification head."""
    backbone = timm.create_model(
        "mobilenetv4_conv_small.e2400_r224_in1k",
        pretrained=False,
        num_classes=0,
    )
    head = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(1280, 256),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.2),
        nn.Linear(256, 64),
        nn.ReLU(inplace=True),
        nn.Dropout(p=0.1),
        nn.Linear(64, 1),
    )
    return nn.Sequential(backbone, head)


class NNDetector:
    """
    Loads a trained MobileNetV4 checkpoint and runs inference on a single image.

    Parameters
    ----------
    model_path : Path or str, optional
        Path to the .pth checkpoint produced by train_detector.py.
        Defaults to ``detector_model.pth`` in the working directory.

    Raises
    ------
    FileNotFoundError
        If the checkpoint file does not exist.
    """

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        model_path = Path(model_path)
        if not model_path.exists():
            raise FileNotFoundError(
                f"Checkpoint not found at '{model_path}'. "
                "Run train_detector.py to produce the model weights."
            )

        self.device = torch.device("cpu")
        self._model = _build_model().to(self.device)

        checkpoint = torch.load(model_path, map_location="cpu")
        self._model.load_state_dict(checkpoint["model_state"])
        self._model.eval()

        self._meta = {
            "f1":       checkpoint.get("f1", None),
            "real_acc": checkpoint.get("real_acc", None),
            "fake_acc": checkpoint.get("fake_acc", None),
            "epoch":    checkpoint.get("epoch", None),
        }

    @property
    def training_metrics(self) -> dict:
        """Return validation metrics recorded at the best checkpoint epoch."""
        return self._meta

    @torch.no_grad()
    def predict(self, image_path: str) -> dict:
        """
        Classify a single image as real or AI-generated.

        Parameters
        ----------
        image_path : str
            Path to the image file (JPEG, PNG, WebP, etc.).

        Returns
        -------
        dict
            ``final_score``  – sigmoid probability in [0, 1]; values
                               closer to 1 indicate AI-generated content.
            ``prediction``   – ``"fake"`` if score >= 0.5, else ``"real"``.
            ``details``      – sub-scores for downstream logging.
        """
        img    = Image.open(image_path).convert("RGB")
        tensor = _transform(img).unsqueeze(0).to(self.device)
        logit  = self._model(tensor)
        score  = float(torch.sigmoid(logit).item())

        return {
            "final_score": round(score, 6),
            "prediction":  "fake" if score >= 0.5 else "real",
            "details": {
                "nn_score": round(score, 6),
            },
        }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python nn_detector.py <image_path>")
        sys.exit(1)

    detector = NNDetector()
    result   = detector.predict(sys.argv[1])
    print(json.dumps(result, indent=2))