from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import json
from datetime import datetime
import os

# Add current directory to path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from e_challan import EChallanGenerator
from incentive_calculation import IncentiveCalculator
from notification import NotificationManager

app = FastAPI(title="Traffic Violation Cloud API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db = DatabaseManager()
challan_gen = EChallanGenerator()
incentive_calc = IncentiveCalculator()
notification_mgr = NotificationManager()

# Pydantic models
class ViolationReport(BaseModel):
    evidence_id: str
    violations: List[Dict]
    detections: List[Dict]
    timestamp: datetime
    gps: Optional[Dict] = None
    user_id: Optional[str] = None
    license_plate: Optional[Dict] = None

class UserRegistration(BaseModel):
    name: str
    email: str
    phone: str

class ChallanResponse(BaseModel):
    challan_id: str
    challan_number: str
    amount: float
    due_date: datetime

@app.post("/api/report", response_model=Dict)
async def report_violation(report: ViolationReport):
    """Receive violation report from edge device."""
    try:
        # Save violation to database
        violation_data = {
            'evidence_id': report.evidence_id,
            'violation_type': report.violations[0]['type'] if report.violations else 'unknown',
            'penalty_amount': sum(v['penalty'] for v in report.violations),
            'license_plate': report.license_plate.get('text') if report.license_plate else None,
            'timestamp': report.timestamp,
            'latitude': report.gps.get('latitude') if report.gps else None,
            'longitude': report.gps.get('longitude') if report.gps else None,
            'location_address': report.gps.get('address') if report.gps else None,
            'user_id': report.user_id,
            'status': 'pending',
            'evidence_path': f"evidence/{report.evidence_id}",
            'ocr_confidence': report.license_plate.get('confidence') if report.license_plate else None,
            'detection_confidence': report.detections[0].get('confidence') if report.detections else None
        }

        violation_id = db.save_violation(violation_data)

        # Generate e-challan
        challan_data = challan_gen.generate_challan(violation_data)
        challan_id = db.create_e_challan({
            'violation_id': violation_id,
            'challan_number': challan_data['challan_number'],
            'amount': challan_data['penalty_amount'],
            'due_date': challan_data['due_date'],
            'vehicle_number': challan_data['vehicle_number']
        })

        # Calculate incentives if user reported
        reward_info = None
        if report.user_id:
            user = db.get_user(report.user_id)
            if user:
                reward_calc = incentive_calc.calculate_reward(
                    {'violations': report.violations, 'license_plate': report.license_plate},
                    {
                        'trust_score': user.trust_score,
                        'valid_reports': user.valid_reports
                    }
                )

                # Update user rewards
                user.rewards_earned += reward_calc['total_reward']
                db.update_user_stats(report.user_id, True)

                reward_info = reward_calc

                # Send reward notification
                notification_mgr.send_reward_notification({
                    'email': user.email,
                    'phone': user.phone
                }, reward_calc['total_reward'])

        # Send authority alert
        notification_mgr.send_authority_alert(
            violation_data,
            violation_data.get('location_address', 'Unknown Location')
        )

        return {
            'status': 'success',
            'violation_id': violation_id,
            'challan_id': challan_id,
            'challan_number': challan_data['challan_number'],
            'reward': reward_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing report: {str(e)}")

@app.post("/api/user/register", response_model=Dict)
async def register_user(user: UserRegistration):
    """Register new user."""
    try:
        user_data = {
            'name': user.name,
            'email': user.email,
            'phone': user.phone
        }

        user_id = db.create_user(user_data)

        return {
            'status': 'success',
            'user_id': user_id,
            'message': 'User registered successfully'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error registering user: {str(e)}")

@app.get("/api/user/{user_id}", response_model=Dict)
async def get_user_profile(user_id: str):
    """Get user profile."""
    try:
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            'user_id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'total_reports': user.total_reports,
            'valid_reports': user.valid_reports,
            'rewards_earned': user.rewards_earned,
            'trust_score': user.trust_score,
            'tier': incentive_calc.get_user_tier({
                'valid_reports': user.valid_reports
            })
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")

@app.get("/api/violations", response_model=List[Dict])
async def get_violations(user_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50):
    """Get violations with optional filters."""
    try:
        violations = db.get_violations(user_id, status, limit)

        result = []
        for v in violations:
            result.append({
                'id': v.id,
                'violation_type': v.violation_type,
                'penalty_amount': v.penalty_amount,
                'license_plate': v.license_plate,
                'timestamp': v.timestamp.isoformat(),
                'location': v.location_address,
                'status': v.status,
                'user_id': v.user_id
            })

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching violations: {str(e)}")

@app.get("/api/dashboard/stats", response_model=Dict)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    try:
        stats = db.get_dashboard_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")

@app.get("/api/leaderboard", response_model=List[Dict])
async def get_leaderboard(limit: int = 10):
    """Get rewards leaderboard."""
    try:
        # Get all users
        users = []  # This would need a method to get all users from DB
        leaderboard = incentive_calc.get_leaderboard_rewards(users, limit)
        return leaderboard

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching leaderboard: {str(e)}")

@app.post("/api/upload", response_model=Dict)
async def upload_citizen_report(file: UploadFile = File(...), user_id: Optional[str] = None):
    """Handle citizen upload."""
    try:
        # Save uploaded file
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")

        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Here you would process the uploaded file similar to edge processing
        # For demo, just return success

        return {
            'status': 'success',
            'file_path': file_path,
            'user_id': user_id,
            'message': 'File uploaded successfully. Processing will begin shortly.'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)