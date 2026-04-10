# SmartEyes API & Detection System

A complete AI-based traffic and civic violation detection system using computer vision on the Edge and centralized Cloud aggregation. 

## Features
- **Real-Time YOLOv8 Detection**: Detect persons, motorcycles, helmets, and civic issues.
- **Multi-Violation Logic**: Flags `TRIPLE_RIDING`, `NO_HELMET`, and `SPITTING`.
- **Blur filtering**: Ensures only clear images are sent to the cloud.
- **ANPR**: Uses EasyOCR server-side to extract number plates.
- **Beautiful Dashboard**: Glassmorphic, modern web UI for authority reporting and citizen dashboard.
- **Automated Challan Generation**.

## 1. Setup Instructions

1. Install Python 3.10+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Update your `.env` file credentials:
   Replace `MONGO_URI` with your MongoDB Atlas string.

## 2. Train Custom Model (Optional)

We process out-of-the-box YOLO models for basic detections (`person`, `motorcycle`), but to unlock advanced civic classes:
1. Put your traffic datasets inside `datasets/`.
2. Run the training script:
   ```bash
   cd models
   python train.py
   ```
3. Move your trained best weights (`best.pt`) to `models/best.pt`.

## 3. Running the System

### Terminal 1: Run the Cloud Layer (FastAPI + Web Application)
```bash
cd cloud_layer
uvicorn app:app --reload
```
You can now open the Dashboard at: [http://localhost:8000/](http://localhost:8000/)  
The Citizen Portal is located at: [http://localhost:8000/citizen](http://localhost:8000/citizen)

### Terminal 2: Run the Edge Camera Processor
Provide a local video file (e.g. your dataset video) or '0' for webcam.
```bash
cd edge_layer
python main.py --source 0
```
This script will parse your camera, run AI inferences, detect violations, and HTTP POST them securely to your Cloud instance.

## Tech Stack
* **CV**: YOLOv8, OpenCV, EasyOCR
* **Backend**: FastAPI, MongoDB (Motor Async)
* **Frontend**: HTML/JS + Bootstrap + Vanilla CSS Glassmorphism
