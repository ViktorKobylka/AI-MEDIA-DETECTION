"""
CoAtNet-0 Training Script
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
from pathlib import Path
import time
import json
from tqdm import tqdm
import timm

# Configuration
config = {
    'data_dir': 'data/images/train',
    'batch_size': 32,
    'num_epochs': 10,
    'learning_rate': 1e-3,
    'num_workers': 4,
    'image_size': 224,
}

# Dataset
class DeepfakeDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = Path(data_dir)
        self.transform = transform
        self.images = []
        self.labels = []
        
        real_dir = self.data_dir / 'real'
        if real_dir.exists():
            real_images = list(real_dir.glob('*.jpg')) + list(real_dir.glob('*.png'))
            self.images.extend(real_images)
            self.labels.extend([0] * len(real_images))
        
        fake_dir = self.data_dir / 'fake'
        if fake_dir.exists():
            fake_images = list(fake_dir.glob('*.jpg')) + list(fake_dir.glob('*.png'))
            self.images.extend(fake_images)
            self.labels.extend([1] * len(fake_images))
        
        print(f"Dataset loaded: {self.labels.count(0)} real, {self.labels.count(1)} fake, {len(self)} total")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        img_path = self.images[idx]
        label = self.labels[idx]
        
        try:
            image = Image.open(img_path).convert('RGB')
        except:
            image = Image.new('RGB', (224, 224))
        
        if self.transform:
            image = self.transform(image)
        
        return image, label

# Model
class CoAtNetDetector(nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = timm.create_model('coatnet_0_rw_224', pretrained=True, num_classes=0)
        self.classifier = nn.Sequential(
            nn.Linear(self.backbone.num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 2)
        )
    
    def forward(self, x):
        return self.classifier(self.backbone(x))

# Training functions
def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0
    
    for images, labels in tqdm(loader, desc='Training', leave=False):
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        running_loss += loss.item()
        _, predicted = outputs.max(1)
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
    
    return running_loss / len(loader), 100. * correct / total

def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in tqdm(loader, desc='Validation', leave=False):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    return running_loss / len(loader), 100. * correct / total

# Main
def main():
    print("=" * 70)
    print("CoAtNet-0 Training")
    print("=" * 70)
    
    # Device
    if torch.backends.mps.is_available():
        device = torch.device('mps')
        print("\nDevice: Apple M1 GPU (MPS)")
    else:
        device = torch.device('cpu')
        print("\nDevice: CPU")
    
    # Transforms
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # Load data
    print(f"\nLoading dataset from {config['data_dir']}")
    full_dataset = DeepfakeDataset(config['data_dir'], transform=train_transform)
    
    train_size = int(0.8 * len(full_dataset))
    val_size = len(full_dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [train_size, val_size],
        generator=torch.Generator().manual_seed(42)
    )
    val_dataset.dataset.transform = val_transform
    
    print(f"Train: {train_size}, Validation: {val_size}")
    
    train_loader = DataLoader(train_dataset, batch_size=config['batch_size'], 
                             shuffle=True, num_workers=config['num_workers'])
    val_loader = DataLoader(val_dataset, batch_size=config['batch_size'],
                           shuffle=False, num_workers=config['num_workers'])
    
    # Build model
    print("\nBuilding model...")
    model = CoAtNetDetector().to(device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Total parameters: {total_params:,}")
    
    # Training setup
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=config['learning_rate'], weight_decay=0.01)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config['num_epochs'])
    
    # Training loop
    print(f"\nStarting training: {config['num_epochs']} epochs\n")
    
    best_val_acc = 0.0
    start_time = time.time()
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    print(f"{'Epoch':<8} {'Train Loss':<12} {'Train Acc':<12} {'Val Loss':<12} {'Val Acc':<12} {'LR':<12} {'Status'}")
    print("-" * 90)
    
    for epoch in range(config['num_epochs']):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc = validate(model, val_loader, criterion, device)
        scheduler.step()
        
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        status = ""
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_acc': val_acc,
                'history': history
            }, 'coatnet_best.pth')
            status = "saved"
        
        print(f"{epoch+1:<8} {train_loss:<12.4f} {train_acc:<12.2f} {val_loss:<12.4f} {val_acc:<12.2f} {optimizer.param_groups[0]['lr']:<12.6f} {status}")
    
    train_time = time.time() - start_time
    
    print("\n" + "=" * 70)
    print("Training complete")
    print("=" * 70)
    print(f"Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Total training time: {train_time/3600:.2f} hours")
    
    summary = {
        'model': 'CoAtNet-0',
        'best_val_acc': best_val_acc,
        'train_time_hours': train_time/3600,
        'history': history
    }
    
    with open('coatnet_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("\nOutput files:")
    print("  coatnet_best.pth")
    print("  coatnet_summary.json")

if __name__ == "__main__":
    main()