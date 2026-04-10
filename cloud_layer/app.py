from fastapi import FastAPI, UploadFile, Form, File, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
from contextlib import asynccontextmanager
import json
import cv2
import numpy as np
import datetime
import os
import uuid
import sys
sys.path.append(os.path.abspath('..'))

import torch
# Monkeypatch PyTorch 2.6 security protocol affecting Ultralytics
_original_load = torch.load
def _safe_load(*args, **kwargs):
    kwargs['weights_only'] = False
    return _original_load(*args, **kwargs)
torch.load = _safe_load

from database import connect_db, close_db, get_db
from ocr_processor import OCRProcessor
from challan_generator import ChallanGenerator
from edge_layer.yolo_detector import YoloDetector
from edge_layer.violation_logic import ViolationLogic
from geopy.geocoders import Nominatim
import base64

ocr_processor = None
cloud_yolo_detector = None
cloud_violation_logic = None
geolocator = Nominatim(user_agent="smarteyes_citizen_app")

def perform_reverse_geocode(lat, lon):
    try:
        # Auto-mock Nagpur coordinates for demo if browser disables location tracking
        import numpy as np
        if lat == 0.0 and lon == 0.0:
            lat = round(21.1458 + np.random.uniform(-0.01, 0.01), 6)
            lon = round(79.0882 + np.random.uniform(-0.01, 0.01), 6)

        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=5)
        if location:
            addr = location.raw.get('address', {})
            road = addr.get('road', '')
            city = addr.get('city', addr.get('town', addr.get('village', 'Unknown City')))
            if road:
                return f"{road}, {city}"
            return location.address
    except Exception as e:
        print(f"Geocoding error: {e}")
    return f"{lat}, {lon} (Auto-Tagged GPS)"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    global ocr_processor, cloud_yolo_detector, cloud_violation_logic
    ocr_processor = OCRProcessor()
    
    # Initialize Cloud-side AI for Citizen processing
    print("Loading Cloud Target AI Models...")
    cloud_yolo_detector = YoloDetector(model_path="../models/best.pt", conf_threshold=0.15)
    cloud_violation_logic = ViolationLogic()
    
    # Create static/uploads directory if not exists
    os.makedirs("static/uploads", exist_ok=True)
    yield
    # Shutdown
    await close_db()

app = FastAPI(title="SmartEyes Cloud API", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key="super-secret-smarteyes-key")

# OAuth Setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Mount static files for CSS/JS and Images
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
os.makedirs("templates", exist_ok=True)
templates = Jinja2Templates(directory="templates")


# ---------------- API ENDPOINTS ---------------- #

@app.post("/api/violations")
async def receive_violation(
    device_id: str = Form(...),
    timestamp: str = Form(...),
    violations: str = Form(...),
    image: UploadFile = File(...)
):
    """
    Endpoint for Edge Devices to submit violations.
    """
    # 1. Parse JSON list of violations
    try:
        violation_list = json.loads(violations)
    except Exception:
        return JSONResponse({"error": "Invalid violations format."}, status_code=400)

    # 2. Read Image
    try:
        contents = await image.read()
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 3. Save Image Locally (or Cloud Storage)
        filename = f"{uuid.uuid4()}.jpg"
        filepath = f"static/uploads/{filename}"
        cv2.imwrite(filepath, img)

        # 4. Run OCR to detect number plate
        global ocr_processor
        vehicle_number = ocr_processor.extract_number_plate(img)

        # 5. Generate Challan and Simulate GPS for Edge Node (Hardcoded to Nagpur area)
        mock_lat = round(21.1458 + np.random.uniform(-0.02, 0.02), 6)
        mock_lon = round(79.0882 + np.random.uniform(-0.02, 0.02), 6)
        location = perform_reverse_geocode(mock_lat, mock_lon)
        challan = ChallanGenerator.generate(vehicle_number, violation_list, location, timestamp)

        # 6. Store in DB
        db = get_db()
        record = {
            "device_id": device_id,
            "vehicle_number": vehicle_number,
            "violations": violation_list,
            "timestamp": timestamp,
            "location": location,
            "lat": mock_lat,
            "lon": mock_lon,
            "image_path": f"/static/uploads/{filename}",
            "challan": challan
        }
        
        await db["violations"].insert_one(record)

        return {"status": "success", "message": "Violation logged", "challan_id": challan["challan_id"]}

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"API CRASH: {error_details}")
        return JSONResponse({"error": str(e), "traceback": error_details}, status_code=500)


@app.post("/api/citizen/analyze")
async def citizen_live_analysis(
    request: Request,
    image_base64: str = Form(...),
    lat: float = Form(...),
    lon: float = Form(...)
):
    """
    Analyzes live camera feeds from Citizen phones.
    Awards +₹50 tokens on confirmed AI violations.
    """
    user = request.session.get('user')
    if not user:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
    try:
        # Decode base64 image from web canvas
        header, encoded = image_base64.split(",", 1)
        data = base64.b64decode(encoded)
        nparr = np.frombuffer(data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 1. Run YOLO inference directly in the cloud
        global cloud_yolo_detector, cloud_violation_logic, ocr_processor
        detected_objs, _ = cloud_yolo_detector.detect(img)
        violations = cloud_violation_logic.evaluate(detected_objs)

        if not violations:
            return {"status": "no_violation", "message": "No traffic violation detected."}

        # 2. Reverse Geocode exact street address
        location_string = perform_reverse_geocode(lat, lon)

        # 3. Save Image Locally
        filename = f"{uuid.uuid4()}.jpg"
        filepath = f"static/uploads/{filename}"
        cv2.imwrite(filepath, img)

        # 4. Extract OCR
        vehicle_number = ocr_processor.extract_number_plate(img)

        # 5. Generate Challan
        timestamp = datetime.datetime.now().isoformat()
        challan = ChallanGenerator.generate(vehicle_number, violations, location_string, timestamp)

        # 6. Database Logging
        db = get_db()
        record = {
            "vehicle_number": vehicle_number,
            "violations": violations,
            "timestamp": timestamp,
            "location": location_string,
            "lat": lat or 21.1458,
            "lon": lon or 79.0882,
            "image_path": f"/static/uploads/{filename}",
            "challan": challan,
            "reported_by": user.get("email")
        }
        await db["violations"].insert_one(record)
        
        # 7. Credit Wallet
        await db["users"].update_one(
            {"email": user.get("email")},
            {"$inc": {"wallet_balance": 50}, "$setOnInsert": {"name": user.get("name")}},
            upsert=True
        )
        
        new_wallet = await db["users"].find_one({"email": user.get("email")})

        return {
            "status": "reward_granted", 
            "reward_amount": 50,
            "wallet_balance": new_wallet.get("wallet_balance"),
            "violations_found": violations,
            "location": location_string
        }

    except Exception as e:
        print(f"Citizen API Error: {e}")
        return JSONResponse({"error": "Processing failed"}, status_code=500)


@app.get("/api/dashboard/data")
async def get_dashboard_data():
    """
    API for Dashboard to fetch summary and latest violations.
    """
    db = get_db()
    cursor = db["violations"].find().sort("timestamp", -1).limit(50)
    records = await cursor.to_list(length=50)
    
    # Fix ObjectId for JSON serialization
    for r in records:
        r["_id"] = str(r["_id"])
        
    return {"violations": records}


# ---------------- WEB PAGES (PLATFORM LAYER) ---------------- #

@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    """
    Login landing page for both Citizen and Admin.
    """
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login/google")
async def login_via_google(request: Request):
    """
    Redirects to Google OAuth Consent Screen.
    Uses generic fallback if Client ID is missing for local dev testing.
    """
    if not os.getenv("GOOGLE_CLIENT_ID"):
        # Local Mock Login Fallback (For Professor Demo)
        request.session['user'] = {"email": "citizen@gmail.com", "name": "Demo Citizen"}
        return RedirectResponse(url='/citizen')
        
    redirect_uri = request.url_for('auth_callback')
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/callback")
async def auth_callback(request: Request):
    """
    Google OAuth Callback. Validates token and creates session.
    """
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')
        if user:
            request.session['user'] = dict(user)
    except Exception as e:
        return HTMLResponse(f"OAuth Error: {e}", status_code=400)
    
    # Check if this email belongs to the Admin Whitelist
    if request.session['user'].get('email') in ["admin@smarteyes.com", "police@smarteyes.com"]:
        return RedirectResponse(url='/')
    else:
        return RedirectResponse(url='/citizen')

@app.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/login')

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """
    Serve the Authority Dashboard page. (Protected in Prod)
    """
    user = request.session.get('user')
    # Uncomment to enforce strict Admin Route:
    # if not user or user.get('email') not in ["admin@smarteyes.com"]: return RedirectResponse('/login')
    
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/citizen", response_class=HTMLResponse)
async def serve_citizen_portal(request: Request):
    """
    Serve the Citizen Portal page.
    """
    user = request.session.get('user')
    if not user:
        return RedirectResponse(url='/login')
        
    db = get_db()
    user_record = await db["users"].find_one({"email": user.get("email")})
    wallet_balance = user_record.get("wallet_balance", 0.0) if user_record else 0.0
        
    return templates.TemplateResponse("citizen.html", {"request": request, "user": user, "wallet_balance": wallet_balance})

@app.get("/challan/{challan_id}", response_class=HTMLResponse)
async def serve_challan(request: Request, challan_id: str):
    """
    Serve the Official E-Challan based on violation type.
    """
    db = get_db()
    record = await db["violations"].find_one({"challan.challan_id": challan_id})
    if not record:
        return HTMLResponse("<h1>Challan Record Not Found</h1>", status_code=404)
    
    # Determine the primary template out of the 3 required by professor
    # Default to helmet if multiple, strictly for the templating priority logic
    violations_list = record.get("violations", [])
    if "SPITTING" in violations_list:
        template_name = "challan_spitting.html"
    elif "TRIPLE_RIDING" in violations_list:
        template_name = "challan_tripling.html"
    else:
        template_name = "challan_helmet.html"

    # Pass the record variables into the Jinja template
    return templates.TemplateResponse(template_name, {
        "request": request, 
        "vehicle_number": record["vehicle_number"],
        "location": record["location"],
        "lat": record.get("lat", 21.1458),
        "lon": record.get("lon", 79.0882),
        "timestamp": record["timestamp"],
        "challan": record["challan"],
        "image_path": record["image_path"]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
