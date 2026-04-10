import os
from dotenv import load_dotenv
import cv2
import time
import argparse

from video_processor import VideoProcessor
from yolo_detector import YoloDetector
from violation_logic import ViolationLogic
from cloud_uploader import CloudUploader

# Load configurable environment variables
load_dotenv(dotenv_path="../.env")

CLOUD_API_URL = os.getenv("CLOUD_API_URL", "http://localhost:8000/api/violations")
DEVICE_ID = os.getenv("DEVICE_ID", "edge_cam_01")
MODEL_PATH = os.getenv("MODEL_PATH", "../models/best.pt")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.5))

def main(video_source, headless):
    print("Starting SmartEyes Edge Layer...")
    
    processor = VideoProcessor(video_source)
    detector = YoloDetector(model_path=MODEL_PATH, conf_threshold=CONFIDENCE_THRESHOLD)
    logic = ViolationLogic()
    uploader = CloudUploader(api_url=CLOUD_API_URL, device_id=DEVICE_ID)

    # Frame processing settings
    # Process every Nth frame to save compute power, depending on FPS
    frame_skip = 4
    frame_count = 0
    # To prevent spamming the cloud with the identical violation in consecutive frames
    last_upload_time = 0
    upload_cooldown = 5 # seconds

    try:
        while True:
            success, frame = processor.get_frame()
            if not success:
                print("End of video stream or failed to grab frame.")
                break
                
            frame_count += 1
            if frame_count % frame_skip != 0:
                continue

            # Check if image is clear before heavy processing
            if not processor.is_image_clear(frame, threshold=20.0):
                # Image too blurry, skip
                print("Image rejected: Too blurry (failed Laplacian variance check).")
                continue

            # Run YOLO detection
            detected_objects, annotated_frame = detector.detect(frame)
            print(f"YOLO Raw Detections: {[obj['class'] for obj in detected_objects]}")
            
            # Evaluate violations
            violations = logic.evaluate(detected_objects)
            
            # Check if we found a violation
            if len(violations) > 0:
                print(f"[{DEVICE_ID}] Violations detected: {violations}")
                
                # Check upload cooldown and if the number plate might be in view
                current_time = time.time()
                if current_time - last_upload_time > upload_cooldown:
                    # Depending on strictness, we might require "number_plate" to be in detected_objects
                    # But often number plate OCR is run on the whole image in the cloud layer.
                    # We will send the full resolution frame (unannotated by default) to the cloud so OCR is clean.
                    uploaded = uploader.upload_violation(frame, violations)
                    if uploaded:
                        last_upload_time = current_time

            # Show display
            if not headless:
                # Add instructions to the frame for the presenter
                cv2.putText(annotated_frame, "DEMO HOTKEYS: [S]=Spit, [T]=Tripling", (10, 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                
                cv2.imshow("SmartEyes Edge - Live Inference", annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    # Force a spitting violation for the professor demo
                    print("[DEMO MODE] Manual Spitting Triggered!")
                    violations = ["SPITTING"]
                elif key == ord('t'):
                    print("[DEMO MODE] Manual Tripling Triggered!")
                    violations = ["TRIPLE_RIDING"]
                
                # Re-run upload block if a manual key was pressed
                if key in [ord('s'), ord('t')]:
                    uploader.upload_violation(frame, violations)
                    last_upload_time = time.time()

    finally:
        processor.release()
        if not headless:
            cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SmartEyes Edge Layer Processor")
    parser.add_argument("--source", type=str, default="0", help="Video source (e.g., 0 for webcam, or path to mp4)")
    parser.add_argument("--headless", action="store_true", help="Run without UI display")
    args = parser.parse_args()
    
    # Process source: if it's a digit string, make it an int
    src = int(args.source) if args.source.isdigit() else args.source
    main(src, args.headless)
