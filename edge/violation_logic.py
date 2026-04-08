from typing import List, Dict, Set
import json
from pathlib import Path

class ViolationLogicEngine:
    """Engine to determine traffic violations based on detected objects and rules."""

    def __init__(self, rules_file: str = 'config/violation_rules.json'):
        """
        Initialize violation logic engine.

        Args:
            rules_file: Path to JSON file containing violation rules
        """
        self.rules = self._load_rules(rules_file)

    def _load_rules(self, rules_file: str) -> Dict:
        """Load violation rules from JSON file."""
        try:
            with open(rules_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default rules
            return {
                "no_helmet": {
                    "objects": ["motorcycle", "person"],
                    "conditions": ["motorcycle_without_helmet"],
                    "penalty": 500
                },
                "wrong_lane": {
                    "objects": ["car", "truck", "bus"],
                    "conditions": ["lane_violation"],
                    "penalty": 1000
                },
                "overspeed": {
                    "objects": ["car", "motorcycle", "truck", "bus"],
                    "conditions": ["speed_violation"],
                    "penalty": 1500
                },
                "signal_jump": {
                    "objects": ["car", "motorcycle", "truck", "bus"],
                    "conditions": ["signal_violation"],
                    "penalty": 2000
                },
                "parking_violation": {
                    "objects": ["car", "motorcycle", "truck", "bus"],
                    "conditions": ["parking_violation"],
                    "penalty": 300
                }
            }

    def detect_violations(self, detections: List[Dict], context: Dict = None) -> List[Dict]:
        """
        Detect violations based on object detections and context.

        Args:
            detections: List of detected objects
            context: Additional context (time, location, speed, etc.)

        Returns:
            List of detected violations
        """
        violations = []
        context = context or {}

        # Group detections by type
        object_counts = {}
        for det in detections:
            obj_class = det['class']
            object_counts[obj_class] = object_counts.get(obj_class, 0) + 1

        # Check each rule
        for rule_name, rule in self.rules.items():
            if self._check_rule(rule, object_counts, context):
                violations.append({
                    'type': rule_name,
                    'penalty': rule['penalty'],
                    'objects': [det for det in detections if det['class'] in rule['objects']],
                    'timestamp': context.get('timestamp'),
                    'location': context.get('location')
                })

        return violations

    def _check_rule(self, rule: Dict, object_counts: Dict, context: Dict) -> bool:
        """Check if a rule is violated."""
        # Check if required objects are present
        required_objects = rule.get('objects', [])
        if not any(obj in object_counts for obj in required_objects):
            return False

        # Check conditions
        conditions = rule.get('conditions', [])
        for condition in conditions:
            if not self._evaluate_condition(condition, object_counts, context):
                return False

        return True

    def _evaluate_condition(self, condition: str, object_counts: Dict, context: Dict) -> bool:
        """Evaluate a specific condition."""
        # Simple condition evaluation (can be extended)
        condition_map = {
            'motorcycle_without_helmet': object_counts.get('motorcycle', 0) > 0 and object_counts.get('person', 0) > 0,
            'lane_violation': context.get('lane_violation', False),
            'speed_violation': context.get('speed', 0) > context.get('speed_limit', 60),
            'signal_violation': context.get('signal_violation', False),
            'parking_violation': context.get('parking_violation', False)
        }

        return condition_map.get(condition, False)