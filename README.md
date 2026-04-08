# Traffic Violation Detection System

An end-to-end AI-powered traffic violation detection system with edge, cloud, and dashboard components.

## Workflow

1. **Camera/Video Feed/Citizen Upload** → `edge/capture.py`
2. **Frame Extraction (OpenCV)** → `edge/frame_extraction.py` (with quality assessment)
3. **YOLO Object Detection** → `edge/object_detection.py`
4. **Object Tracking** → `edge/object_tracking.py` (optional)
5. **Violation Logic Engine** → `edge/violation_logic.py`
6. **License Plate Detection** → `edge/license_plate_detection.py`
7. **PaddleOCR** → `edge/ocr.py`
8. **Evidence Capture** → `edge/evidence_capture.py`
9. **GPS Tagging** → `edge/gps_tagging.py`
10. **User Identification** ⭐ → `edge/user_identification.py`
11. **Database Storage** → `cloud/database.py`
12. **E-Challan Generation** → `cloud/e_challan.py`
13. **Incentive Calculation** ⭐ → `cloud/incentive_calculation.py`
14. **Dashboard/Authority Notification** → `dashboard/app.py` + `cloud/notification.py`

## Architecture

- **Edge**: Real-time processing on device/camera
- **Cloud**: Centralized processing, storage, and analytics
- **Dashboard**: Web interface for monitoring and management

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download Models
```bash
# Create models directory
mkdir models

# Download YOLOv8 nano model
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt
```

### 3. Run Demo
```bash
python demo.py
```

## Manual Setup

### Run Individual Components

**Start Cloud API:**
```bash
python cloud/main.py
```
API available at: http://localhost:8000

**Start Dashboard:**
```bash
python dashboard/app.py
```
Dashboard available at: http://localhost:5000

**Run Edge Processing:**
```bash
# Process video file
python edge/main.py --video path/to/video.mp4

# Live camera feed
python edge/main.py --live --display
```

### Run All Services
For production deployment, run each service in separate terminals:

```bash
# Terminal 1: Cloud API
python cloud/main.py

# Terminal 2: Dashboard
python dashboard/app.py

# Terminal 3: Edge Processing
python edge/main.py --live
```

## Features

- **Real-time violation detection** with quality assessment
- **License plate recognition** using OCR
- **GPS tagging** for location tracking
- **User incentives** for citizen reports ⭐
- **E-Challan generation** with automated fines
- **Multi-channel notifications** (email, SMS)
- **Web dashboard** for monitoring and analytics
- **Multi-violation detection** (single image can detect multiple violations)

## API Endpoints

### Cloud API (FastAPI)
- `POST /api/report` - Report violation from edge
- `GET /api/violations` - Get violations list
- `GET /api/dashboard/stats` - Get dashboard statistics
- `POST /api/user/register` - Register new user
- `GET /api/user/{user_id}` - Get user profile

### Dashboard (Flask)
- `GET /` - Main dashboard
- `GET /violations` - Violations management
- `GET /users` - Users management
- `GET /reports` - Analytics and reports

## Configuration

### Violation Rules
Edit `config/violation_rules.json` to customize violation types and penalties.

### Incentive System
Edit `config/incentive_config.json` to adjust reward calculations.

### Database
Default: SQLite (`traffic_violation.db`)
Change in `cloud/database.py` for production databases.

## Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_basic.py::test_imports -v
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Run `pip install -r requirements.txt`
2. **Model Not Found**: Download YOLO model to `models/yolov8n.pt`
3. **Camera Not Working**: Check camera permissions and index
4. **OCR Not Working**: Install PaddlePaddle or use fallback mode

### Environment Variables

```bash
# Disable PaddlePaddle network checks
export PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK=True
```

## Development

### Project Structure
```
MINI_PROJECT/
├── edge/          # Edge processing modules
├── cloud/         # Cloud API and services
├── dashboard/     # Web dashboard
├── models/        # ML models
├── config/        # Configuration files
├── data/          # Data storage
├── templates/     # Document templates
├── tests/         # Test suite
└── utils/         # Utilities
```

### Adding New Features

1. **Edge Features**: Add to `edge/` directory
2. **API Endpoints**: Add to `cloud/main.py`
3. **Dashboard Pages**: Add to `dashboard/` directory
4. **Tests**: Add to `tests/` directory

## License

This project is for educational and research purposes.