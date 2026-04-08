import cv2
import time
from datetime import datetime
from typing import Dict, List
import argparse
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from capture import MediaCapture
from frame_extraction import FrameExtractor
from object_detection import ObjectDetector
from object_tracking import ObjectTracker
from violation_logic import ViolationLogicEngine
from license_plate_detection import LicensePlateDetector
from ocr import LicensePlateOCR
from evidence_capture import EvidenceCapture
from gps_tagging import GPSTagger
from user_identification import UserIdentification

class TrafficViolationSystem:
    """Main traffic violation detection system."""

    def __init__(self, config: Dict = None):
        """
        Initialize the traffic violation system.

        Args:
            config: Configuration dictionary
        """
        self.config = config or self._default_config()

        # Initialize components
        self.capture = MediaCapture(self.config['camera_source'])
        self.frame_extractor = FrameExtractor(
            fps=self.config['fps'],
            quality_threshold=self.config['quality_threshold']
        )
        self.object_detector = ObjectDetector(
            model_path=self.config['yolo_model'],
            conf_threshold=self.config['detection_threshold']
        )
        self.object_tracker = ObjectTracker() if self.config['use_tracking'] else None
        self.violation_engine = ViolationLogicEngine(self.config['rules_file'])
        self.plate_detector = LicensePlateDetector()
        self.ocr = LicensePlateOCR()
        self.evidence_capture = EvidenceCapture(self.config['evidence_dir'])
        self.gps_tagger = GPSTagger()
        self.user_id_system = UserIdentification(self.config['user_db'])

        print("Traffic Violation System initialized")

    def _default_config(self) -> Dict:
        """Get default configuration."""
        return {
            'camera_source': 0,  # Default camera
            'fps': 10,
            'quality_threshold': 0.6,
            'yolo_model': 'models/yolov8n.pt',
            'detection_threshold': 0.5,
            'use_tracking': True,
            'rules_file': 'config/violation_rules.json',
            'evidence_dir': 'evidence',
            'user_db': 'data/users.json',
            'cloud_endpoint': 'http://localhost:8000/api/report'
        }

    def process_video_file(self, video_path: str, user_id: str = None) -> List[Dict]:
        """
        Process a video file for violations.

        Args:
            video_path: Path to video file
            user_id: User ID for citizen reports

        Returns:
            List of violation reports
        """
        print(f"Processing video: {video_path}")

        # Extract frames
        frames = self.frame_extractor.extract_frames(video_path)
        print(f"Extracted {len(frames)} frames")

        violations_found = []

        for i, frame in enumerate(frames):
            print(f"Processing frame {i+1}/{len(frames)}")

            # Detect objects
            detections = self.object_detector.detect(frame)

            # Track objects if enabled
            if self.object_tracker:
                tracked_objects = self.object_tracker.update(frame, detections)
            else:
                tracked_objects = detections

            # Detect violations
            context = {'timestamp': datetime.now()}
            violations = self.violation_engine.detect_violations(tracked_objects, context)

            if violations:
                print(f"Found {len(violations)} violations in frame {i+1}")

                # Detect license plates
                plates = self.plate_detector.detect_plates(frame, tracked_objects)

                # OCR on plates
                if plates:
                    plate_images = [p['plate_image'] for p in plates]
                    ocr_results = self.ocr.extract_text(plate_images)

                    # Associate OCR with violations
                    for j, violation in enumerate(violations):
                        if j < len(ocr_results):
                            violation['license_plate'] = ocr_results[j]

                # Capture evidence
                evidence = self.evidence_capture.capture_evidence(
                    frame, violations, tracked_objects, datetime.now()
                )

                # GPS tagging (mock coordinates for demo)
                evidence = self.gps_tagger.tag_evidence(evidence, 28.6139, 77.2090)  # Delhi coordinates

                # User identification
                if user_id:
                    evidence['user_id'] = user_id
                    reward = self.user_id_system.calculate_rewards(user_id, violations)
                    evidence['reward_earned'] = reward

                violations_found.append(evidence)

                # Report to cloud
                self._report_to_cloud(evidence)

        return violations_found

    def process_live_feed(self, user_id: str = None):
        """Process live camera feed."""
        print("Starting live feed processing...")

        if not self.capture.start_capture():
            print("Failed to start camera capture")
            return

        try:
            while True:
                frame = self.capture.get_frame()
                if frame is None:
                    continue

                # Extract frame if quality is good
                processed_frame = self.frame_extractor.extract_frame_from_stream(frame)
                if processed_frame is None:
                    continue

                # Detect objects
                detections = self.object_detector.detect(processed_frame)

                # Track objects
                if self.object_tracker:
                    tracked_objects = self.object_tracker.update(processed_frame, detections)
                else:
                    tracked_objects = detections

                # Detect violations
                context = {'timestamp': datetime.now()}
                violations = self.violation_engine.detect_violations(tracked_objects, context)

                if violations:
                    print(f"Violation detected! {len(violations)} violations")

                    # Process violation (similar to video processing)
                    plates = self.plate_detector.detect_plates(processed_frame, tracked_objects)
                    if plates:
                        plate_images = [p['plate_image'] for p in plates]
                        ocr_results = self.ocr.extract_text(plate_images)

                        for j, violation in enumerate(violations):
                            if j < len(ocr_results):
                                violation['license_plate'] = ocr_results[j]

                    evidence = self.evidence_capture.capture_evidence(
                        processed_frame, violations, tracked_objects, datetime.now()
                    )

                    evidence = self.gps_tagger.tag_evidence(evidence)

                    if user_id:
                        evidence['user_id'] = user_id
                        reward = self.user_id_system.calculate_rewards(user_id, violations)
                        evidence['reward_earned'] = reward

                    self._report_to_cloud(evidence)

                # Display frame (optional)
                if self.config.get('display', False):
                    cv2.imshow('Traffic Violation Detection', processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                time.sleep(1.0 / self.config['fps'])

        finally:
            self.capture.stop_capture()
            cv2.destroyAllWindows()

    def _report_to_cloud(self, evidence: Dict):
        """Report violation to cloud service."""
        try:
            import requests
            response = requests.post(self.config['cloud_endpoint'], json=evidence, timeout=5)
            if response.status_code == 200:
                print("Successfully reported to cloud")
            else:
                print(f"Failed to report to cloud: {response.status_code}")
        except Exception as e:
            print(f"Error reporting to cloud: {e}")

def main():
    parser = argparse.ArgumentParser(description='Traffic Violation Detection System')
    parser.add_argument('--video', type=str, help='Path to video file')
    parser.add_argument('--live', action='store_true', help='Process live feed')
    parser.add_argument('--user-id', type=str, help='User ID for citizen reports')
    parser.add_argument('--display', action='store_true', help='Display video feed')

    args = parser.parse_args()

    # Initialize system
    config = {
        'camera_source': 0,
        'fps': 10,
        'quality_threshold': 0.6,
        'yolo_model': 'models/yolov8n.pt',
        'detection_threshold': 0.5,
        'use_tracking': True,
        'rules_file': 'config/violation_rules.json',
        'evidence_dir': 'evidence',
        'user_db': 'data/users.json',
        'cloud_endpoint': 'http://localhost:8000/api/report',
        'display': args.display
    }

    system = TrafficViolationSystem(config)

    if args.video:
        violations = system.process_video_file(args.video, args.user_id)
        print(f"Processing complete. Found {len(violations)} violations.")
    elif args.live:
        system.process_live_feed(args.user_id)
    else:
        print("Please specify --video <path> or --live")

if __name__ == "__main__":
    main()