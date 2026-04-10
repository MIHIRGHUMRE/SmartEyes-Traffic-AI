from fastapi import FastAPI, UploadFile, Form, File, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import json
import cv2
import numpy as np
import datetime
import os
import uuid

from database import connect_db, close_db, get_db
from ocr_processor import OCRProcessor
from challan_generator import ChallanGenerator

ocr_processor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    global ocr_processor
    ocr_processor = OCRProcessor()
    
    # Create static/uploads directory if not exists
    os.makedirs("static/uploads", exist_ok=True)
    yield
    # Shutdown
    await close_db()

app = FastAPI(title="SmartEyes Cloud API", lifespan=lifespan)

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

        # 5. Generate Challan and Simulate GPS
        mock_lat = round(28.6139 + np.random.uniform(-0.05, 0.05), 6)
        mock_lon = round(77.2090 + np.random.uniform(-0.05, 0.05), 6)
        location = f"{mock_lat}, {mock_lon} (Auto-Tagged)" 
        challan = ChallanGenerator.generate(vehicle_number, violation_list, location, timestamp)

        # 6. Store in DB
        db = get_db()
        record = {
            "vehicle_number": vehicle_number,
            "violations": violation_list,
            "timestamp": timestamp,
            "location": location,
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

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """
    Serve the Authority Dashboard page.
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/citizen", response_class=HTMLResponse)
async def serve_citizen_portal(request: Request):
    """
    Serve the Citizen Portal page.
    """
    return templates.TemplateResponse("citizen.html", {"request": request})

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
        "timestamp": record["timestamp"],
        "challan": record["challan"],
        "image_path": record["image_path"]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
