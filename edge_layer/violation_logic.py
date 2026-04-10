def calculate_iou(boxA, boxB):
    # Determine the (x, y)-coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Compute the area of intersection rectangle
    interArea = max(0, xB - xA) * max(0, yB - yA)

    # Compute the area of both the prediction and ground-truth rectangles
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    
    # Check what percentage of the Box A (person) is inside Box B (motorcycle)
    if boxAArea == 0:
        return 0
    return interArea / float(boxAArea)

class ViolationLogic:
    def __init__(self):
        # The percentage of a person's bounding box that must overlap with the motorcycle
        # to be considered "riding" it.
        self.overlap_threshold = 0.3
    
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

        # Process specifically for Riders on Vehicles to prevent bystander flagging
        vehicles = objects_by_class["motorcycle"] + objects_by_class["bike"]
        
        # Pillion Rider Helmet Exception Check & Tripling Check
        for mc in vehicles:
            riders_on_this_mc = []
            helmets_on_this_mc = []
            
            # Find persons intersecting closely with this specific motorcycle 
            for p in objects_by_class["person"]:
                overlap = calculate_iou(p["bbox"], mc["bbox"])
                if overlap > self.overlap_threshold:
                    riders_on_this_mc.append(p)
                    
            # Find helmets intersecting with this motorcycle
            for h in objects_by_class["helmet"]:
                overlap = calculate_iou(h["bbox"], mc["bbox"])
                if overlap > self.overlap_threshold:
                    helmets_on_this_mc.append(h)
            
            num_riders = len(riders_on_this_mc)
            num_helmets = len(helmets_on_this_mc)
            
            # Tripling Violation Logic:
            if num_riders >= 3:
                violations.add("TRIPLE_RIDING")
                
            # No Helmet Violation Logic (Pillion exception rules):
            # If there's at least 1 rider, but ZERO helmets detected on the bike -> Violation
            # If 2 riders but 1 helmet -> Accepted locally (no violation)
            if num_riders > 0 and num_helmets == 0:
                violations.add("NO_HELMET")

        return list(violations)
