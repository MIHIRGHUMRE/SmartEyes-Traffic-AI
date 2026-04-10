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

    # Load a pretrained YOLOv8 Medium model for advanced feature extraction
    model = YOLO("yolov8m.pt")
    
    # Train the model
    try:
        results = model.train(
            data=dataset_yaml,
            epochs=100,      # Increased to 100 epochs since we are augmenting heavily
            imgsz=640,       # Image size for training
            batch=4,         # Lowered to 4 because YOLOv8m is heavier on VRAM
            name="smarteyes_model", # Save directory name inside runs/detect/
            device="cpu",    # Falling back to CPU because CUDA driver is refusing connection
            # Heavy Data Augmentations explicitly added to multiply initial low dataset
            augment=True,
            degrees=10.0,
            translate=0.1,
            scale=0.5,
            shear=0.0,
            perspective=0.0,
            flipud=0.0,
            fliplr=0.5,
            mosaic=1.0,      # Combines 4 images into 1, crucial for tiny objects like splitting
            mixup=0.2
        )
        print("Training completed successfully!")
        print("Best weights saved at: runs/detect/smarteyes_model/weights/best.pt")
        print("Copy these weights to the 'models/best.pt' for deployment.")
    except Exception as e:
        print(f"Failed to start training. Error: {e}")

if __name__ == "__main__":
    train_model()
