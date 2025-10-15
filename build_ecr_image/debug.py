import os
import sys
import torch
import yaml
from ultralytics import YOLO

print("=" * 50)
print("DEBUGGING SAGEMAKER ENVIRONMENT")
print("=" * 50)

# Check Python version
print(f"Python version: {sys.version}")

# Check PyTorch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")

# Check Ultralytics
try:
    from ultralytics import __version__

    print(f"Ultralytics version: {__version__}")
except:
    print("Could not get Ultralytics version")

# Check environment variables
print("\nSageMaker Environment Variables:")
for key, value in sorted(os.environ.items()):
    if key.startswith("SM_"):
        print(f"  {key}: {value}")

# Check directories
print("\nDirectory Structure:")
dirs_to_check = [
    "/opt/ml/input/data",
    "/opt/ml/input/data/train",
    "/opt/ml/input/data/validation",
    "/opt/ml/model",
    "/opt/ml/output",
]

for dir_path in dirs_to_check:
    if os.path.exists(dir_path):
        print(f"  {dir_path}: EXISTS")
        # List contents
        try:
            contents = os.listdir(dir_path)
            for item in contents[:5]:  # Show first 5 items
                print(f"    - {item}")
            if len(contents) > 5:
                print(f"    ... and {len(contents) - 5} more items")
        except:
            print(f"    Could not list contents")
    else:
        print(f"  {dir_path}: NOT FOUND")

# Try to load YOLO model
print("\nTesting YOLO model loading:")

try:
    model = YOLO("yolo11x.pt")  # Try smaller model first
    print("  Successfully loaded yolo11x.pt")
except Exception as e:
    print(f"  Failed to load model: {e}")


# try:
#     model = YOLO('yolo11n.pt')  # Try smaller model first
#     print("  Successfully loaded yolo11n.pt")
# except Exception as e:
#     print(f"  Failed to load model: {e}")

print("=" * 50)
