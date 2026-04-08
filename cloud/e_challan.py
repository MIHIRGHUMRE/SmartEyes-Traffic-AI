from datetime import datetime, timedelta
from typing import Dict, List, Optional
import uuid
import json
from pathlib import Path

class EChallanGenerator:
    """Generate and manage electronic challans."""

    def __init__(self, template_path: str = 'templates/challan_template.html'):
        """
        Initialize e-challan generator.

        Args:
            template_path: Path to challan template
        """
        self.template_path = Path(template_path)
        self.challan_counter = 0

    def generate_challan(self, violation_data: Dict) -> Dict:
        """
        Generate e-challan for violation.

        Args:
            violation_data: Violation information

        Returns:
            Challan data dictionary
        """
        challan_number = self._generate_challan_number()

        # Calculate due date (30 days from now)
        due_date = datetime.now() + timedelta(days=30)

        challan_data = {
            'challan_id': str(uuid.uuid4()),
            'challan_number': challan_number,
            'violation_id': violation_data['id'],
            'vehicle_number': violation_data.get('license_plate', {}).get('text', 'UNKNOWN'),
            'violation_type': violation_data['violation_type'],
            'penalty_amount': violation_data['penalty_amount'],
            'location': violation_data.get('location_address', 'Unknown Location'),
            'timestamp': violation_data['timestamp'],
            'due_date': due_date,
            'issued_date': datetime.now(),
            'payment_status': 'pending',
            'officer_id': 'SYSTEM_AUTO',  # Automated system
            'evidence_path': violation_data.get('evidence_path')
        }

        return challan_data

    def _generate_challan_number(self) -> str:
        """Generate unique challan number."""
        self.challan_counter += 1
        date_str = datetime.now().strftime('%Y%m%d')
        return f"TV{date_str}{self.challan_counter:04d}"

    def generate_challan_html(self, challan_data: Dict) -> str:
        """
        Generate HTML version of challan.

        Args:
            challan_data: Challan data

        Returns:
            HTML string
        """
        template = self._load_template()

        # Replace placeholders
        html = template
        html = html.replace('{{CHALLAN_NUMBER}}', challan_data['challan_number'])
        html = html.replace('{{VEHICLE_NUMBER}}', challan_data['vehicle_number'])
        html = html.replace('{{VIOLATION_TYPE}}', challan_data['violation_type'])
        html = html.replace('{{PENALTY_AMOUNT}}', f"₹{challan_data['penalty_amount']:.2f}")
        html = html.replace('{{LOCATION}}', challan_data['location'])
        html = html.replace('{{TIMESTAMP}}', challan_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S'))
        html = html.replace('{{DUE_DATE}}', challan_data['due_date'].strftime('%Y-%m-%d'))
        html = html.replace('{{ISSUED_DATE}}', challan_data['issued_date'].strftime('%Y-%m-%d %H:%M:%S'))

        return html

    def _load_template(self) -> str:
        """Load HTML template."""
        if self.template_path.exists():
            with open(self.template_path, 'r') as f:
                return f.read()

        # Default template
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>E-Challan - {{CHALLAN_NUMBER}}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .header { text-align: center; border-bottom: 2px solid #333; padding-bottom: 10px; }
                .details { margin: 20px 0; }
                .detail-row { margin: 10px 0; }
                .amount { font-size: 18px; font-weight: bold; color: red; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Traffic Violation E-Challan</h1>
                <h2>Challan Number: {{CHALLAN_NUMBER}}</h2>
            </div>

            <div class="details">
                <div class="detail-row">
                    <strong>Vehicle Number:</strong> {{VEHICLE_NUMBER}}
                </div>
                <div class="detail-row">
                    <strong>Violation Type:</strong> {{VIOLATION_TYPE}}
                </div>
                <div class="detail-row">
                    <strong>Penalty Amount:</strong> <span class="amount">{{PENALTY_AMOUNT}}</span>
                </div>
                <div class="detail-row">
                    <strong>Location:</strong> {{LOCATION}}
                </div>
                <div class="detail-row">
                    <strong>Violation Time:</strong> {{TIMESTAMP}}
                </div>
                <div class="detail-row">
                    <strong>Due Date:</strong> {{DUE_DATE}}
                </div>
                <div class="detail-row">
                    <strong>Issued Date:</strong> {{ISSUED_DATE}}
                </div>
            </div>

            <div style="margin-top: 30px; text-align: center; color: #666;">
                <p>This is an electronically generated challan.</p>
                <p>Please pay before the due date to avoid additional penalties.</p>
            </div>
        </body>
        </html>
        """

    def send_challan_notification(self, challan_data: Dict, contact_info: Dict):
        """
        Send challan notification to vehicle owner.

        Args:
            challan_data: Challan information
            contact_info: Contact details (email, phone)
        """
        # This would integrate with SMS/email services
        message = f"""
        TRAFFIC VIOLATION CHALLAN

        Challan Number: {challan_data['challan_number']}
        Vehicle: {challan_data['vehicle_number']}
        Violation: {challan_data['violation_type']}
        Amount: ₹{challan_data['penalty_amount']:.2f}
        Due Date: {challan_data['due_date'].strftime('%Y-%m-%d')}

        Please pay at the earliest to avoid penalties.
        """

        print(f"Sending notification: {message}")

        # In production, integrate with:
        # - SMS service (Twilio, AWS SNS, etc.)
        # - Email service (SendGrid, AWS SES, etc.)
        # - Push notifications

    def calculate_late_fees(self, challan_data: Dict) -> float:
        """
        Calculate late payment fees.

        Args:
            challan_data: Challan data

        Returns:
            Late fee amount
        """
        now = datetime.now()
        due_date = challan_data['due_date']

        if now <= due_date:
            return 0.0

        days_overdue = (now - due_date).days

        # 10% per month late fee
        original_amount = challan_data['penalty_amount']
        late_fee = original_amount * 0.10 * (days_overdue // 30 + 1)

        return late_fee

    def generate_bulk_challans(self, violations: List[Dict]) -> List[Dict]:
        """
        Generate challans for multiple violations.

        Args:
            violations: List of violation data

        Returns:
            List of challan data
        """
        challans = []
        for violation in violations:
            challan = self.generate_challan(violation)
            challans.append(challan)

        return challans