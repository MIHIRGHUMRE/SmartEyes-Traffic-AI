from typing import Dict, List, Optional
from datetime import datetime
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests

class NotificationManager:
    """Manage notifications for users and authorities."""

    def __init__(self, config: Dict = None):
        """
        Initialize notification manager.

        Args:
            config: Notification configuration
        """
        self.config = config or self._default_config()

    def _default_config(self) -> Dict:
        """Default notification configuration."""
        return {
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'your-email@gmail.com',
                'password': 'your-password',
                'from_email': 'noreply@trafficviolation.com'
            },
            'sms': {
                'api_key': 'your-sms-api-key',
                'api_url': 'https://api.smsprovider.com/send'
            },
            'push': {
                'fcm_server_key': 'your-fcm-server-key',
                'fcm_url': 'https://fcm.googleapis.com/fcm/send'
            }
        }

    def send_reward_notification(self, user_data: Dict, reward_amount: float):
        """
        Send reward notification to user.

        Args:
            user_data: User information
            reward_amount: Reward amount earned
        """
        subject = "Reward Earned - Traffic Violation Report"
        message = f"""
        Congratulations!

        You have earned ₹{reward_amount:.2f} for your traffic violation report.

        Your current total rewards: ₹{user_data.get('rewards_earned', 0):.2f}

        Keep contributing to safer roads!

        Traffic Violation System
        """

        self._send_email(user_data.get('email'), subject, message)
        self._send_sms(user_data.get('phone'), f"You earned ₹{reward_amount:.2f} reward!")

    def send_challan_notification(self, challan_data: Dict, vehicle_owner: Dict):
        """
        Send challan notification to vehicle owner.

        Args:
            challan_data: Challan information
            vehicle_owner: Vehicle owner contact information
        """
        subject = f"Traffic Violation Challan - {challan_data['challan_number']}"
        message = f"""
        TRAFFIC VIOLATION NOTICE

        Challan Number: {challan_data['challan_number']}
        Vehicle Number: {challan_data['vehicle_number']}
        Violation: {challan_data['violation_type']}
        Location: {challan_data['location']}
        Date/Time: {challan_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}
        Penalty Amount: ₹{challan_data['penalty_amount']:.2f}
        Due Date: {challan_data['due_date'].strftime('%Y-%m-%d')}

        Please pay the fine before the due date to avoid additional penalties.

        Payment can be made online at: [payment_link]

        Traffic Police Department
        """

        if vehicle_owner.get('email'):
            self._send_email(vehicle_owner['email'], subject, message)

        if vehicle_owner.get('phone'):
            sms_message = f"Traffic Challan {challan_data['challan_number']}: ₹{challan_data['penalty_amount']:.2f} due by {challan_data['due_date'].strftime('%d/%m/%Y')}"
            self._send_sms(vehicle_owner['phone'], sms_message)

    def send_authority_alert(self, violation_data: Dict, location: str):
        """
        Send alert to traffic authorities.

        Args:
            violation_data: Violation information
            location: Location of violation
        """
        subject = f"Traffic Violation Alert - {location}"
        message = f"""
        TRAFFIC VIOLATION ALERT

        Location: {location}
        Violation Type: {violation_data['violation_type']}
        Vehicle: {violation_data.get('license_plate', {}).get('text', 'Unknown')}
        Time: {violation_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}

        Evidence ID: {violation_data['evidence_id']}

        Please take necessary action.

        Automated Traffic Monitoring System
        """

        # Send to authority email list
        authority_emails = self.config.get('authority_emails', [])
        for email in authority_emails:
            self._send_email(email, subject, message)

    def send_bulk_notifications(self, notifications: List[Dict]):
        """
        Send multiple notifications.

        Args:
            notifications: List of notification data
        """
        for notification in notifications:
            notification_type = notification.get('type')

            if notification_type == 'reward':
                self.send_reward_notification(
                    notification['user_data'],
                    notification['reward_amount']
                )
            elif notification_type == 'challan':
                self.send_challan_notification(
                    notification['challan_data'],
                    notification['vehicle_owner']
                )
            elif notification_type == 'authority_alert':
                self.send_authority_alert(
                    notification['violation_data'],
                    notification['location']
                )

    def _send_email(self, to_email: str, subject: str, message: str):
        """Send email notification."""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config['email']['from_email']
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(message, 'plain'))

            server = smtplib.SMTP(
                self.config['email']['smtp_server'],
                self.config['email']['smtp_port']
            )
            server.starttls()
            server.login(
                self.config['email']['username'],
                self.config['email']['password']
            )
            text = msg.as_string()
            server.sendmail(self.config['email']['from_email'], to_email, text)
            server.quit()

            print(f"Email sent to {to_email}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    def _send_sms(self, phone_number: str, message: str):
        """Send SMS notification."""
        try:
            # Using a generic SMS API structure
            payload = {
                'api_key': self.config['sms']['api_key'],
                'to': phone_number,
                'message': message
            }

            response = requests.post(self.config['sms']['api_url'], json=payload)
            if response.status_code == 200:
                print(f"SMS sent to {phone_number}")
            else:
                print(f"Failed to send SMS: {response.status_code}")
        except Exception as e:
            print(f"Failed to send SMS: {e}")

    def _send_push_notification(self, device_token: str, title: str, message: str):
        """Send push notification."""
        try:
            headers = {
                'Authorization': f"key={self.config['push']['fcm_server_key']}",
                'Content-Type': 'application/json'
            }

            payload = {
                'to': device_token,
                'notification': {
                    'title': title,
                    'body': message
                }
            }

            response = requests.post(
                self.config['push']['fcm_url'],
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                print(f"Push notification sent to {device_token}")
            else:
                print(f"Failed to send push notification: {response.status_code}")
        except Exception as e:
            print(f"Failed to send push notification: {e}")

    def schedule_notification(self, notification_data: Dict, delay_minutes: int):
        """
        Schedule a notification for later delivery.

        Args:
            notification_data: Notification information
            delay_minutes: Delay in minutes
        """
        # In a real implementation, this would use a task queue like Celery
        # For demo purposes, we'll just print
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        print(f"Notification scheduled for {scheduled_time}")

        # Store in database or queue for later processing
        notification_data['scheduled_time'] = scheduled_time
        notification_data['status'] = 'scheduled'

    def get_notification_history(self, user_id: str = None, days: int = 30) -> List[Dict]:
        """
        Get notification history.

        Args:
            user_id: Optional user ID filter
            days: Number of days to look back

        Returns:
            List of notifications
        """
        # This would query the database
        # For demo, return empty list
        return []