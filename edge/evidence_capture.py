import cv2
import numpy as np
from datetime import datetime
from typing import Dict, List
import os
from pathlib import Path

class EvidenceCapture:
    """Capture and store violation evidence."""

    def __init__(self, output_dir: str = 'evidence'):
        """
        Initialize evidence capture.

        Args:
            output_dir: Directory to store evidence
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def capture_evidence(self, frame: np.ndarray, violations: List[Dict],
                        detections: List[Dict], timestamp: datetime = None) -> Dict:
        """
        Capture evidence for violations.

        Args:
            frame: Original frame
            violations: Detected violations
            detections: Object detections
            timestamp: Timestamp of capture

        Returns:
            Evidence metadata
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Generate unique ID
        evidence_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{hash(str(violations)) % 10000}"

        # Create evidence directory
        evidence_dir = self.output_dir / evidence_id
        evidence_dir.mkdir(exist_ok=True)

        # Save original frame
        frame_path = evidence_dir / 'original.jpg'
        cv2.imwrite(str(frame_path), frame)

        # Save annotated frame
        annotated = self._annotate_frame(frame, violations, detections)
        annotated_path = evidence_dir / 'annotated.jpg'
        cv2.imwrite(str(annotated_path), annotated)

        # Save violation details
        metadata = {
            'evidence_id': evidence_id,
            'timestamp': timestamp.isoformat(),
            'violations': violations,
            'detections': detections,
            'frame_path': str(frame_path),
            'annotated_path': str(annotated_path)
        }

        # Save metadata
        metadata_path = evidence_dir / 'metadata.json'
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)

        return metadata

    def _annotate_frame(self, frame: np.ndarray, violations: List[Dict],
                       detections: List[Dict]) -> np.ndarray:
        """Annotate frame with violations and detections."""
        annotated = frame.copy()

        # Draw detections
        for det in detections:
            x1, y1, x2, y2 = map(int, det['bbox'])
            cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(annotated, det['class'], (x1, y1 - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Draw violations
        for violation in violations:
            for obj in violation['objects']:
                x1, y1, x2, y2 = map(int, obj['bbox'])
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), 3)
                cv2.putText(annotated, f"VIOLATION: {violation['type']}",
                           (x1, y1 - 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return annotated

    def get_evidence_list(self) -> List[Dict]:
        """Get list of all captured evidence."""
        evidence_list = []
        for evidence_dir in self.output_dir.iterdir():
            if evidence_dir.is_dir():
                metadata_path = evidence_dir / 'metadata.json'
                if metadata_path.exists():
                    import json
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                        evidence_list.append(metadata)

        return sorted(evidence_list, key=lambda x: x['timestamp'], reverse=True)