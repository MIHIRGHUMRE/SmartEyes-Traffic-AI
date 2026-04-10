import uuid

FINE_AMOUNTS = {
    "NO_HELMET": 1000,
    "TRIPLE_RIDING": 2000,
    "SPITTING": 500
}

class ChallanGenerator:
    @staticmethod
    def generate(vehicle_number, violations, location, timestamp):
        """
        Generate e-challan data.
        """
        total_fine = 0
        violation_details = []
        
        for v in violations:
            amount = FINE_AMOUNTS.get(v, 0)
            total_fine += amount
            violation_details.append({
                "type": v,
                "fine": amount
            })
            
        challan = {
            "challan_id": f"CHLN-{str(uuid.uuid4())[:8].upper()}",
            "vehicle_number": vehicle_number,
            "total_fine": total_fine,
            "violations": violation_details,
            "location": location,
            "timestamp": timestamp,
            "status": "UNPAID"
        }
        
        return challan
