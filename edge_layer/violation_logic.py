def calculate_center(bbox):
    """Calculate center of a bounding box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2, (y1 + y2) / 2)

class ViolationLogic:
    def __init__(self):
        # Define distance threshold for associating a person with a motorcycle
        # This will depend on resolution, but using a generic pixel distance threshold
        self.association_threshold = 300 
    
    def evaluate(self, detected_objects):
        """
        Evaluates detected objects and returns a list of violations.
        Support multiple violations per frame.
        """
        violations = set()
        
        counts = {
            "person": 0,
            "bike": 0,
            "motorcycle": 0,
            "helmet": 0,
            "no_helmet": 0,
            "spitting": 0,
            "number_plate": 0
        }
        
        objects_by_class = {
            "person": [],
            "bike": [],
            "motorcycle": [],
            "helmet": []
        }

        # Count objects
        for obj in detected_objects:
            cls = obj["class"]
            if cls in counts:
                counts[cls] += 1
            if cls in objects_by_class:
                objects_by_class[cls].append(obj)
            # If detecting "spitting" or "no_helmet" classification natively
            if cls == "spitting":
                violations.add("SPITTING")
            if cls == "no_helmet":
                violations.add("NO_HELMET")

        # Logic for NO_HELMET (if no specific "no_helmet" class is detected, but persons exceed helmets)
        if counts["person"] > counts["helmet"] and counts["person"] > 0 and (counts["motorcycle"] > 0 or counts["bike"] > 0):
            violations.add("NO_HELMET")
            
        # Logic for TRIPLE_RIDING
        # Basic: if total persons >= 3 and there's a motorcycle/bike
        # Advanced (Spatial): group persons to the nearest motorcycle/bike
        if counts["person"] >= 3 and (counts["motorcycle"] > 0 or counts["bike"] > 0):
            vehicles = objects_by_class["motorcycle"] + objects_by_class["bike"]
            for mc in vehicles:
                mc_center = calculate_center(mc["bbox"])
                riders_on_mc = 0
                for p in objects_by_class["person"]:
                    p_center = calculate_center(p["bbox"])
                    # Calculate Euclidean distance
                    dist = ((p_center[0] - mc_center[0])**2 + (p_center[1] - mc_center[1])**2)**0.5
                    if dist < self.association_threshold:
                        riders_on_mc += 1
                
                if riders_on_mc >= 3:
                    violations.add("TRIPLE_RIDING")
                    break

        return list(violations)
