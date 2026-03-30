import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image
import sys

# Paths
MODEL_PATH = "output/resnet_animal_behavior.pth"

# Classes (adjust these based on your dataset folders)
class_names = ["cat", "dog"]

# Preprocess for prediction
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225]),
])

# Load model architecture same as training
model = models.resnet50(pretrained=False)
num_features = model.fc.in_features
model.fc = nn.Sequential(
    nn.Linear(num_features, 128),
    nn.ReLU(),
    nn.Dropout(0.3),
    nn.Linear(128, len(class_names))
)

# Load trained weights
model.load_state_dict(torch.load(MODEL_PATH, map_location=torch.device("cpu")))
model.eval()

# Load test image
img_path = sys.argv[1]
img = Image.open(img_path).convert("RGB")
img_tensor = transform(img).unsqueeze(0)

# Predict
with torch.no_grad():
    outputs = model(img_tensor)
    _, predicted = torch.max(outputs, 1)

print(f"Predicted: {class_names[predicted.item()]}")
