# 🚦 SmartEyes AI — Intelligent Traffic Violation Enforcement System

> **A production-ready, AI-powered traffic monitoring platform** that uses computer vision, cloud analytics, and citizen participation to automatically detect and penalize traffic violations in real time.

---

## 📌 Table of Contents

1. [Project Overview](#-project-overview)
2. [Key Features](#-key-features)
3. [System Architecture](#-system-architecture)
4. [Tech Stack](#-tech-stack)
5. [Violation Detection Classes](#-violation-detection-classes)
6. [How It Works](#-how-it-works)
7. [Citizen Portal (Live Lens)](#-citizen-portal-live-lens)
8. [Authority Dashboard](#-authority-dashboard)
9. [E-Challan System](#-e-challan-system)
10. [Gamified Incentive Engine](#-gamified-incentive-engine)
11. [OCR & License Plate Recognition](#-ocr--license-plate-recognition)
12. [Geo-Tagging & Mapping](#-geo-tagging--mapping)
13. [Project Structure](#-project-structure)
14. [Setup & Installation](#-setup--installation)
15. [How to Train the Model](#-how-to-train-the-model)
16. [Running the System](#-running-the-system)
17. [Team & Credits](#-team--credits)

---

## 🧠 Project Overview

**SmartEyes AI** is a two-layer intelligent traffic enforcement system developed as a mini-project for academic purposes. The system leverages a custom-trained **YOLOv8m** deep learning model to detect traffic violations from camera feeds, automatically generate official **E-Challans**, and reward citizens who report violations via a gamified wallet system.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| 🔍 **AI Violation Detection** | Real-time YOLOv8m inference detecting No Helmet, Triple Riding, and Public Spitting |
| 📷 **WebRTC Live Camera** | Citizens can stream directly from their phone browser, no app install required |
| 🗂️ **Automatic E-Challan** | Official formatted challan auto-generated instantly after violation confirmation |
| 🗺️ **Dynamic Map Embed** | OpenStreetMap embedded inside each challan showing exact violation location |
| 🔐 **Google OAuth 2.0** | Secure role-based login for both citizens and traffic authority |
| 💰 **Incentive Wallet** | Citizens earn ₹50 tokens for every confirmed violation they report |
| 🔡 **OCR Plate Reader** | EasyOCR-powered license plate extractor |
| 📊 **Authority Dashboard** | Live violation stream with statistics for traffic police officers |
| ☁️ **Cloud-Native Design** | FastAPI + MongoDB cloud backend, deployable on Render.com |

---

## 🏗️ System Architecture

The system uses a **Hybrid Two-Layer Architecture** with local edge detection and cloud-based management:

```
┌─────────────────────────────────────────────────────────────────┐
│                        CITIZEN DEVICE                          │
│  Browser WebRTC Camera  ──►  Base64 Frame  ──►  Cloud API      │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                         EDGE LAYER                             │
│   Physical Camera ──► OpenCV ──► YOLOv8m ──► Violation Logic  │
│                                     │                          │
│                            Upload to Cloud API                 │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                        CLOUD LAYER                             │
│  FastAPI Backend                                               │
│  ├── AI Inference (YOLOv8m)                                   │
│  ├── OCR (EasyOCR)                                             │
│  ├── Reverse Geocoding (Geopy → Nagpur)                        │
│  ├── Challan Generator                                         │
│  ├── MongoDB (violations + wallets)                           │
│  └── Google OAuth 2.0                                         │
└─────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AUTHORITY DASHBOARD                       │
│  Real-time Live Violations Table + Statistics + Challan Links  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### AI & Machine Learning
- **YOLOv8m** (Ultralytics) — Object detection model
- **PyTorch 2.6+** — Deep learning framework
- **EasyOCR** — License plate text extraction
- **OpenCV** — Image processing and augmentation

### Backend
- **FastAPI** — High-performance async Python web framework
- **Uvicorn** — ASGI server
- **MongoDB** (via Motor async driver) — NoSQL database
- **Authlib** — Google OAuth 2.0 integration
- **Geopy** — Reverse geocoding (coordinates → road names)

### Frontend
- **HTML5 / CSS3 / Bootstrap 5** — UI structure and styling
- **Vanilla JavaScript (ES6+)** — Fetch API, WebRTC, DOM updates
- **Jinja2** — Server-side templating for E-Challans
- **OpenStreetMap (OSM)** — Free map embeds in challans

### DevOps
- **Git / GitHub** — Version control
- **Python venv** — Dependency isolation
- **python-dotenv** — Secure environment variable management

---

## 🎯 Violation Detection Classes

The custom YOLOv8m model is trained to detect the following 5 classes:

| Class ID | Class Name | Description |
|---|---|---|
| 0 | `bike` | Two-wheeled vehicle (motorcycle/scooter) |
| 1 | `helmet` | Person wearing a helmet |
| 2 | `no_helmet` | Person on bike **without** a helmet ⚠️ |
| 3 | `person` | Generic pedestrian/person |
| 4 | `spitting` | Person spitting in public ⚠️ |

**Business Logic:**
- `NO_HELMET` → detected when `no_helmet` class appears on/near a `bike`
- `TRIPLE_RIDING` → detected when **3+ persons** are spatially overlapping on **1 bike** (via IoU logic)
- `SPITTING` → detected directly from the `spitting` class

---

## 🔄 How It Works

### End-to-End Pipeline

```
1. Camera Input (Edge Camera OR Citizen Phone)
        │
        ▼
2. YOLOv8m Inference
   └── Detects: bike, person, helmet, no_helmet, spitting
        │
        ▼
3. Violation Logic (IoU Spatial Analysis)
   └── Determines: NO_HELMET / TRIPLE_RIDING / SPITTING
        │
        ▼
4. If Violation Confirmed:
   ├── Save frame image to /static/uploads/
   ├── Run EasyOCR on frame → Extract license plate
   ├── Reverse geocode GPS 
   ├── Generate E-Challan (with fine amount)
   ├── Save record to MongoDB
   └── Credit ₹50 to Citizen's wallet
        │
        ▼
5. Authority Dashboard auto-refreshes with new violation
6. Citizen sees instant confirmation + wallet update
```

---

## 📱 Citizen Portal (Live Lens)

The Citizen Portal allows any verified resident to participate in traffic enforcement directly from their browser.

**Two input modes:**

- **🔴 Live Camera Stream** — Start camera button activates WebRTC and sends frames every 3 seconds
- **📁 Upload Evidence** — Upload a photo or video recording of a violation

**After Detection:**
- Violation type displayed (e.g., `NO_HELMET DETECTED`)
- Location displayed as road name + city (e.g., `Wardha Road, Nagpur`)
- Wallet instantly updated: **+₹50 credited**
- Navigation link to Authority Dashboard visible at top

---

## 📊 Authority Dashboard

The traffic authority's real-time monitoring interface, protected by role-based Google OAuth login.

**Dashboard Features:**
- 📈 Summary cards: Total fines collected, total violations, active cameras
- 🔄 Live auto-refreshing violation table (every 5 seconds, cache-busted)
- 🔗 Direct challan links (each row opens the official E-Challan)
- 🖼️ Thumbnail preview of violation evidence image

---

## 📄 E-Challan System

Every confirmed violation auto-generates a digital E-Challan with:

| Field | Value |
|---|---|
| Challan ID | Auto-generated `CHLN-XXXXXXXX` |
| Vehicle Number | OCR-extracted OR Maharashtra fallback (e.g. `MH31WX9821`) |
| Violation Type | `NO HELMET` / `TRIPLE RIDING` / `PUBLIC SPITTING` |
| Fine Amount | ₹1000 / ₹500 / ₹200 (violation-specific) |
| Date & Time | ISO timestamp |
| Location | Reverse-geocoded Nagpur address |
| Map | Embedded OpenStreetMap centered on exact GPS coordinates |
| Evidence Image | Screenshot of frame with violation |
| QR Code | Dynamic payment QR for UPI |

**Three separate official challan templates:**
- `challan_helmet.html`
- `challan_tripling.html`
- `challan_spitting.html`

---

## 💰 Gamified Incentive Engine

SmartEyes encourages civic participation with a token-based reward system:

- Citizen reports a violation via Live Lens → **+₹50 added to wallet**
- Wallet balance persists across sessions via MongoDB
- Balance visible at the top-right of the Citizen Portal
- Future scope: wallet redemption, leaderboard system

---

## 🔡 OCR & License Plate Recognition

**Engine:** EasyOCR (Transformer-based deep learning OCR)

**Pre-processing Pipeline:**
1. Convert frame to grayscale
2. 2x upscale (`cv2.INTER_CUBIC`)
3. Gaussian Blur to reduce noise
4. OTSU Thresholding for contrast enhancement
5. Run OCR on both raw and thresholded images
6. Select best result by confidence score

**Fallback Logic:**
When OCR cannot confidently read the plate (e.g., blurry frame), the system generates a **realistic Maharashtra RTO plate**:
```
MH30 | MH31 | MH40 followed by random valid alphanumeric suffix
e.g. MH31WX9821 | MH30JB8829
```

---

## 🗺️ Geo-Tagging & Mapping

- **Library:** Geopy (Nominatim reverse geocoder)
- **Fallback:** If browser denies location or geocoder fails:
  - Default to **Nagpur, Maharashtra** coordinates: `21.1458°N, 79.0882°E`
  - Slight random jitter applied to simulate different Nagpur roads

**Result format:**
```
Wardha Road, Nagpur, Maharashtra
```

The E-Challan map iframe dynamically zooms and centers on the real GPS coordinates stored with each violation record.

---

## 📁 Project Structure

```
mini_project/
├── cloud_layer/                  # Cloud Backend (FastAPI)
│   ├── app.py                    # Main FastAPI application
│   ├── ocr_processor.py          # EasyOCR wrapper + MH fallback
│   ├── static/
│   │   ├── css/style.css         # Global custom styling
│   │   ├── js/app.js             # Dashboard real-time JS
│   │   └── uploads/              # Evidence images (auto-generated)
│   └── templates/
│       ├── dashboard.html        # Authority Dashboard UI
│       ├── citizen.html          # Citizen Live Lens UI
│       ├── login.html            # Google OAuth Login page
│       ├── challan_helmet.html   # No Helmet E-Challan
│       ├── challan_tripling.html # Triple Riding E-Challan
│       └── challan_spitting.html # Spitting E-Challan
│
├── edge_layer/                   # On-premise Edge Node
│   ├── main.py                   # Entry point, camera loop
│   ├── yolo_detector.py          # YOLOv8m inference wrapper
│   ├── violation_logic.py        # IoU-based violation classifier
│   ├── video_processor.py        # OpenCV camera handler
│   └── cloud_uploader.py         # Async uploader to Cloud API
│
├── models/
│   ├── train.py                  # YOLOv8m training script
│   └── best.pt                   # Trained model weights (gitignored)
│
├── datasets/
│   ├── data.yaml                 # YOLO dataset config
│   ├── images/                   # Training images
│   └── labels/                   # YOLO format annotation files
│
├── .env                          # Secrets (MONGO_URI, OAuth keys)
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.10+
- MongoDB Atlas account (or local MongoDB)
- Google Cloud Console project (for OAuth)

### 1. Clone & Setup
```bash
git clone https://github.com/MIHIRGHUMRE/SmartEyes-Traffic-AI.git
cd SmartEyes-Traffic-AI

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment
Create a `.env` file in the root:
```env
MONGO_URI=mongodb+srv://<user>:<password>@cluster.mongodb.net/smarteyes
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
CLOUD_API_URL=http://localhost:8000/api/violations
DEVICE_ID=edge_cam_01
MODEL_PATH=../models/best.pt
CONFIDENCE_THRESHOLD=0.5
```

### 3. Add OAuth Redirect URI
In Google Cloud Console → OAuth 2.0 → Authorized redirect URIs, add:
```
http://localhost:8000/auth/callback
```

---

## 🏋️ How to Train the Model

```bash
# Activate venv from the parent 'mini project' folder
cd "mini project"
.\venv\Scripts\Activate.ps1

# Run the training script
cd mini_project
python models/train.py
```

**Training config (in `train.py`):**
- Model: `yolov8m.pt` (pretrained, 25.8M params)
- Epochs: `50`
- Batch size: `4`
- Image size: `640x640`
- Device: `cpu` (switch to `cuda` if CUDA libs match)
- Heavy augmentation: mosaic, mixup, fliplr, HSV shifts

After training completes, copy best weights:
```bash
copy "runs\detect\smarteyes_model\weights\best.pt" "models\best.pt"
```

---

## ▶️ Running the System

### Start Cloud Server
```bash
cd cloud_layer
python -m uvicorn app:app --reload
```
Open browser: **http://localhost:8000**

### Start Edge Node (CCTV Camera)
```bash
cd edge_layer
python main.py --source 0        # Webcam
python main.py --source video.mp4 # Video file
```

---

## 👨‍💻 Team & Credits

| Role | Name |
|---|---|
| Project Lead & AI Engineer | Mihir Ghumre |
| Dataset & Annotation | Traffic Violation Dataset (Roboflow) |
| AI Framework | Ultralytics YOLOv8 |
| OCR Engine | JaidedAI EasyOCR |
| Geo Services | OpenStreetMap / Nominatim |

---

## 📜 License

This project is built for academic purposes under the **CC BY 4.0** license (dataset).
Model weights and source code are proprietary to the SmartEyes team.

---

*SmartEyes AI — Making Nagpur's roads safer, one detection at a time. 🚔*
