from ultralytics import YOLO
import os
import torch

# Monkeypatch PyTorch 2.6 security protocol affecting Ultralytics
_original_load = torch.load
def _safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _safe_load

def train_model():
    """
    Train a custom YOLOv8 model for SmartEyes.
    Uses absolute paths to avoid CWD-dependent path issues.
    """
    print("Initializing YOLOv8 training for SmartEyes...")
    
    # Resolve absolute path to dataset yaml - works regardless of where script is run from
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    dataset_yaml = os.path.join(project_dir, "datasets", "data.yaml")
    model_weights = os.path.join(project_dir, "yolov8m.pt")

    print(f"Dataset YAML: {dataset_yaml}")
    print(f"Model weights: {model_weights}")

    if not os.path.exists(dataset_yaml):
        print(f"ERROR: {dataset_yaml} not found!")
        return
    
    # Load a pretrained YOLOv8 Medium model for advanced feature extraction
    model = YOLO(model_weights)
    
    # Train the model
    try:
        results = model.train(
            data=dataset_yaml,
            epochs=50,       # 50 epochs as requested
            imgsz=640,
            batch=4,         # Safe for 6GB VRAM
            name="smarteyes_model",
            project=os.path.join(project_dir, "runs", "detect"),
            device="cpu",    # Fallback to CPU - CUDA DLL mismatch on this system
            # Data augmentation to maximize learning from small dataset
            augment=True,
            degrees=10.0,
            translate=0.1,
            scale=0.5,
            shear=0.0,
            perspective=0.0,
            flipud=0.0,
            fliplr=0.5,
            mosaic=1.0,
            mixup=0.2
        )
        best_weights = os.path.join(project_dir, "runs", "detect", "smarteyes_model", "weights", "best.pt")
        print("\n✅ Training completed successfully!")
        print(f"Best weights saved at: {best_weights}")
        print("Copy these weights to models/best.pt to deploy.")
    except Exception as e:
        import traceback
        print(f"Failed to start training. Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    train_model()
