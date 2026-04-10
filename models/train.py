from ultralytics import YOLO
import os

def train_model():
    """
    Train a custom YOLOv8 model for SmartEyes.
    Ensure your dataset is labeled in YOLO format and you have a 'data.yaml' file.
    """
    print("Initializing YOLOv8 training for SmartEyes...")
    
    # Check if dataset yaml exists
    dataset_yaml = "../datasets/data.yaml"
    if not os.path.exists(dataset_yaml):
        print(f"Warning: {dataset_yaml} not found. Ensure you place your dataset configuration here.")
        print("Example content for data.yaml:")
        print("path: ../datasets")
        print("train: images/train")
        print("val: images/val")
        print("names:")
        print("  0: person")
        print("  1: motorcycle")
        print("  2: helmet")
        print("  3: no_helmet")
        print("  4: number_plate")
        print("  5: spitting")

    # Load a pretrained YOLOv8 nano model for transfer learning
    model = YOLO("yolov8n.pt")
    
    # Train the model
    try:
        results = model.train(
            data=dataset_yaml,
            epochs=50,       # Adjust based on dataset size and available compute
            imgsz=640,       # Image size for training
            batch=8,         # Lowered to 8 specifically to prevent CUDA out of memory on RTX 4050 6GB
            name="smarteyes_model", # Save directory name inside runs/detect/
            device="cpu"    # Uses GPU if available, else CPU
        )
        print("Training completed successfully!")
        print("Best weights saved at: runs/detect/smarteyes_model/weights/best.pt")
        print("Copy these weights to the 'models/best.pt' for deployment.")
    except Exception as e:
        print(f"Failed to start training. Error: {e}")

if __name__ == "__main__":
    train_model()
