import torch
import torch.nn as nn
import torchvision.transforms as transforms
from torch.utils.data import Dataset, DataLoader
import numpy as np
import os
import cv2
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, confusion_matrix
import seaborn as sns

# ── Config ──────────────────────────────────────────────
IMG_SIZE    = 96
BATCH_SIZE  = 16
EPOCHS      = 20
DATASET_DIR = "../dataset"
MODEL_PATH  = "model.pth"

# ── Dataset ─────────────────────────────────────────────
class PersonDataset(Dataset):
    def __init__(self, folder, transform=None):
        self.data      = []
        self.labels    = []
        self.transform = transform

        for fname in os.listdir(folder):
            if not fname.lower().endswith(
                    (".jpg", ".jpeg", ".png")):
                continue
            if fname.startswith("person."):
                label = 1
            elif fname.startswith("non_person."):
                label = 0
            else:
                continue

            img = cv2.imread(os.path.join(folder, fname))
            if img is None:
                continue
            img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            self.data.append(img)
            self.labels.append(label)

        print(f"  person: {self.labels.count(1)}, "
              f"no_person: {self.labels.count(0)}")

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        img   = self.data[idx]
        label = self.labels[idx]
        if self.transform:
            img = self.transform(img)
        return img, label

# ── Transforms ──────────────────────────────────────────
train_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.RandomHorizontalFlip(),
    transforms.RandomRotation(10),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5],
                         [0.5, 0.5, 0.5])
])

test_transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.ToTensor(),
    transforms.Normalize([0.5, 0.5, 0.5],
                         [0.5, 0.5, 0.5])
])

# ── CNN Model ────────────────────────────────────────────
class PersonCNN(nn.Module):
    def __init__(self):
        super(PersonCNN, self).__init__()

        # Block 1: 96x96 → 48x48
        self.block1 = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.Conv2d(32, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.1)
        )

        # Block 2: 48x48 → 24x24
        self.block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.Conv2d(64, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.2)
        )

        # Block 3: 24x24 → 12x12
        self.block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.Conv2d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.3)
        )

        # Block 4: 12x12 → 6x6
        self.block4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Dropout2d(0.3)
        )

        # Classifier
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 6 * 6, 512),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(512, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, 1)
        )

    def forward(self, x):
        x = self.block1(x)
        x = self.block2(x)
        x = self.block3(x)
        x = self.block4(x)
        x = self.classifier(x)
        return x

# ── Load Data ────────────────────────────────────────────
print("Loading training data...")
train_dataset = PersonDataset(
    os.path.join(DATASET_DIR, "training"), train_transform)

print("Loading testing data...")
test_dataset = PersonDataset(
    os.path.join(DATASET_DIR, "testing"), test_transform)

train_loader = DataLoader(
    train_dataset, batch_size=BATCH_SIZE, shuffle=True)
test_loader  = DataLoader(
    test_dataset,  batch_size=BATCH_SIZE, shuffle=False)

# ── Setup ─────────────────────────────────────────────────
device = torch.device(
    "mps" if torch.backends.mps.is_available() else "cpu")
print(f"Device: {device}")

model     = PersonCNN().to(device)
criterion = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, patience=3, factor=0.5)

total_params = sum(p.numel() for p in model.parameters())
print(f"Total parameters: {total_params:,}")

# ── Train ─────────────────────────────────────────────────
train_accs, val_accs     = [], []
train_losses, val_losses = [], []
best_val_acc = 0

for epoch in range(EPOCHS):

    # Train phase
    model.train()
    all_preds, all_labels = [], []
    running_loss = 0

    for imgs, labels in train_loader:
        imgs   = imgs.to(device)
        labels = labels.float().to(device)

        optimizer.zero_grad()
        outputs = model(imgs).squeeze()
        loss    = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        preds = (torch.sigmoid(outputs) >= 0.5).long()
        all_preds    += preds.cpu().tolist()
        all_labels   += labels.cpu().long().tolist()
        running_loss += loss.item()

    train_acc  = accuracy_score(all_labels, all_preds)
    train_loss = running_loss / len(train_loader)

    # Val phase
    model.eval()
    val_preds, val_labels_list = [], []
    val_loss = 0

    with torch.no_grad():
        for imgs, labels in test_loader:
            imgs    = imgs.to(device)
            labels  = labels.float().to(device)
            outputs = model(imgs).squeeze()
            loss    = criterion(outputs, labels)
            preds   = (torch.sigmoid(outputs) >= 0.5).long()
            val_preds       += preds.cpu().tolist()
            val_labels_list += labels.cpu().long().tolist()
            val_loss        += loss.item()

    val_acc  = accuracy_score(val_labels_list, val_preds)
    val_loss = val_loss / len(test_loader)

    train_accs.append(train_acc)
    val_accs.append(val_acc)
    train_losses.append(train_loss)
    val_losses.append(val_loss)

    scheduler.step(val_loss)

    # Save best model
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), MODEL_PATH)
        saved = "✅ saved"
    else:
        saved = ""

    print(f"Epoch {epoch+1:2d}/{EPOCHS}  "
          f"Train: {train_acc*100:.1f}% (loss {train_loss:.3f})  "
          f"Val: {val_acc*100:.1f}% (loss {val_loss:.3f})  "
          f"{saved}")

print(f"\n🏆 Best Val Accuracy: {best_val_acc*100:.1f}%")

# ── Confusion Matrix ─────────────────────────────────────
model.load_state_dict(torch.load(MODEL_PATH))
model.eval()
final_preds, final_labels = [], []

with torch.no_grad():
    for imgs, labels in test_loader:
        imgs    = imgs.to(device)
        outputs = model(imgs).squeeze()
        preds   = (torch.sigmoid(outputs) >= 0.5).long()
        final_preds  += preds.cpu().tolist()
        final_labels += labels.tolist()

cm = confusion_matrix(final_labels, final_preds)
print(f"\nConfusion Matrix:")
print(f"               Pred No  Pred Yes")
print(f"Actual No    {cm[0][0]:6d}  {cm[0][1]:6d}")
print(f"Actual Yes   {cm[1][0]:6d}  {cm[1][1]:6d}")

# ── Plot ──────────────────────────────────────────────────
fig, axes = plt.subplots(1, 3, figsize=(15, 4))

axes[0].plot(train_accs, label="Train")
axes[0].plot(val_accs,   label="Val")
axes[0].set_title("Accuracy")
axes[0].set_xlabel("Epoch")
axes[0].legend()

axes[1].plot(train_losses, label="Train")
axes[1].plot(val_losses,   label="Val")
axes[1].set_title("Loss")
axes[1].set_xlabel("Epoch")
axes[1].legend()

sns.heatmap(cm, annot=True, fmt="d", ax=axes[2],
            xticklabels=["No Person", "Person"],
            yticklabels=["No Person", "Person"])
axes[2].set_title("Confusion Matrix")

plt.tight_layout()
plt.savefig("training_result.png")
plt.show()
print("Plot saved → training_result.png")