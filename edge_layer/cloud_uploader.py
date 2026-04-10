import requests
import json
import cv2
import datetime
import threading

class CloudUploader:
    def __init__(self, api_url, device_id):
        self.api_url = api_url
        self.device_id = device_id

    def upload_violation(self, frame, violations):
        """
        Upload the frame and violation details to the cloud.
        :param frame: The image frame where violation was detected.
        :param violations: List of violation strings.
        """
        success, encoded_image = cv2.imencode('.jpg', frame)
        if not success:
            print("Error: Could not encode image for upload.")
            return False

        # Convert image to bytes
        image_bytes = encoded_image.tobytes()

        # Prepare payload
        payload = {
            "device_id": self.device_id,
            "timestamp": datetime.datetime.now().isoformat(),
            "violations": json.dumps(violations)  # Send as JSON string inside multipart form
        }

        files = {
            "image": ("violation.jpg", image_bytes, "image/jpeg")
        }

        def execute_upload():
            try:
                response = requests.post(self.api_url, data=payload, files=files)
                if response.status_code in [200, 201]:
                    print(f"[{self.device_id}] Successfully uploaded violation: {violations}")
                else:
                    print(f"[{self.device_id}] Failed to upload. Server responded: {response.text}")
            except Exception as e:
                print(f"[{self.device_id}] Exception during upload: {e}")

        # Dispatch the upload into a background thread so the video doesn't freeze!
        thread = threading.Thread(target=execute_upload)
        thread.start()
        
        return True
