from flaskr.entities.Alert import Alert
from datetime import datetime
import json

# {
#     "logic": "AND",
#     "location": {
#         "zone_ids": [1, 2, 3], # List of zone IDs to check
#         "camera_ids": [1, 2] # List of camera IDs to check
#     },
#     "conditions": [
#         # all possible conditions
#         {"object": "Person", "min_count": 1, "max_count": 10, "dwell_time": 30 }, # Object detected in the frame, dwell times in seconds
#         {"object": "Face", "employee_ids": [101, 102], "dwell_time": 30}, # Recognized employee in the frame
#     ]
# }

"""
What: Detecting specific objects (Person, Face) or employees.
How Many: Specifying counts (min_count, max_count).
How Long: Incorporating dwell_time.
Where: Limiting the rule to specific zone_ids or camera_ids.
How: Combining conditions using logic (AND/OR).

// Example structure compatible with the Python code (excluding location/dwell_time handling)
{
    "logic": "AND",
    // "location": { ... } // This part is NOT currently handled by the Python code
    "conditions": [
        {
            "type": "object_detected", // Use the 'type' key
            "object_name": "Person",   // Use 'object_name' as expected by the code
            "min_count": 1,
            "max_count": 10
            // "dwell_time": 30 // Dwell time handling needs to be added to the Python code
        },
        {
            "type": "employee_present", // Use the 'type' key
            "employee_ids": [101, 102]
            // "dwell_time": 30 // Dwell time handling needs to be added to the Python code
        }
        // Add other condition types like "ppe_missing", "time_of_day", "zone_entry" as needed
    
"""

# event_context = {
#     "timestamp": datetime.now(), # Or frame timestamp
#     "camera_id": camera.id,
#     "camera_name": camera_name,
#     "detected_objects": [ # List of detected objects
#         {"name": "Person", "count": 3, "zone_ids": [1, 2]},
#         {"name": "Hardhat", "count": 2, "zone_ids": [1]},
#         {"name": "Safety Vest", "count": 3, "zone_ids": [1, 2]},
#         {"name": "car", "count": 1, "zone_ids": [3]},
#     ],
#     "recognized_employees": [ # List of recognized employee IDs in the frame
#         {"employee_id": 101, "zone_ids": [1]},
#         {"employee_id": 105, "zone_ids": [2]},
#     ],
#     # Add other relevant data like dwell times if tracked
#     "dwell_times": {
#         # object_id: {zone_id: duration_seconds}
#     }
# }

# {
#   "logic": "AND",
#   "conditions": [
#     { "type": "zone", "zone_ids": [5] }, // Assuming Zone 5 is 'Pedestrian Only'
#     { "type": "object_detected", "object_name": ["car", "van", "truck", "vehicle"], "min_count": 1 } // Can list multiple object types
#   ]
# }

class RuleInference:
    def __init__(self, rules):
        self.rules = rules
        self.inference_results = []
        self.alerts = []
        self.frame_context = {}

    def set_frame_context(self, frame_context):
        """
        Set the context for the current frame being processed.
        Args:
            frame_context (dict): {
                "timestamp": datetime,
                "camera_id": int,
                "detected_objects": dict,
                "detected_persons": list,
                }
        """
        self.frame_context = frame_context

    def _evaluate_conditions(self, rule):
        """
        Evaluate the conditions of a rule against the current frame context.
        Args:
            rule (AlertRule): The rule to evaluate.
        Returns:
            bool: True if conditions are met, False otherwise.
        """
        try:
            conditions_data = json.loads(rule.conditions_json) if isinstance(rule.conditions_json, str) else rule.conditions_json
        except json.JSONDecodeError:
            print(f"Error decoding conditions_json for rule {rule.id}")
            return False

        conditions = conditions_data.get("conditions", [])
        logic = conditions_data.get("logic", "AND").upper()

        results = []
        for condition in conditions:
            condition_type = condition.get("type")
            result = False
            try:
                if condition_type == "zone_entry":
                    # Check if any detected person entered a specific zone
                    required_zone_ids = set(condition.get("zone_ids", []))
                    entered_zones = set(self.frame_context.get("zones_entered", {}).values()) # {person_id: zone_id}
                    if required_zone_ids.intersection(entered_zones):
                        result = True
                elif condition_type == "object_detected":
                    # Check if a specific object is detected with min/max count
                    object_name = condition.get("object_name")
                    min_count = condition.get("min_count", 0)
                    max_count = condition.get("max_count", float('inf'))
                    detected_objects = self.frame_context.get("detected_objects", {}) # {'Person': 2, 'Helmet': 1}
                    count = detected_objects.get(object_name, 0)
                    if min_count <= count <= max_count:
                        result = True
                elif condition_type == "time_of_day":
                    # Check if current time is within a specified range
                    start_time_str = condition.get("start_time")
                    end_time_str = condition.get("end_time")
                    current_time = self.frame_context.get("timestamp", datetime.now()).time()
                    start_time = datetime.strptime(start_time_str, '%H:%M:%S').time()
                    end_time = datetime.strptime(end_time_str, '%H:%M:%S').time()
                    if start_time <= current_time <= end_time:
                         result = True
                elif condition_type == "employee_present":
                    # Check if specific employees are present
                    required_employee_ids = set(condition.get("employee_ids", []))
                    detected_persons = set(self.frame_context.get("detected_persons", [])) # List of employee_ids
                    if required_employee_ids.intersection(detected_persons):
                        result = True
                elif condition_type == "ppe_missing":
                    # Check if any detected person is missing required PPE
                    # ppe_status = {employee_id: {'helmet': True, 'vest': False}}
                    required_ppe = set(condition.get("required_ppe", []))
                    ppe_status = self.frame_context.get("ppe_status", {})
                    for person_id, status in ppe_status.items():
                        missing_ppe = required_ppe - set(item for item, present in status.items() if present)
                        if missing_ppe:
                            result = True
                            # Optionally store which person is missing what in context for the alert
                            self.frame_context['triggering_person_id'] = person_id
                            self.frame_context['missing_ppe'] = list(missing_ppe)
                            break # One person missing PPE is enough to trigger
                # Add more condition types as needed
                else:
                    print(f"Unknown condition type: {condition_type}")

            except Exception as e:
                print(f"Error evaluating condition {condition}: {e}")
                result = False # Fail safe

            results.append(result)

        if not results:
            return False # No conditions to evaluate

        if logic == "AND":
            return all(results)
        elif logic == "OR":
            return any(results)
        else:
            print(f"Unknown logic type: {logic}")
            return False

    def _create_alert(self, rule):
        """
        Create an alert based on the rule and current frame context.
        Args:
            rule (AlertRule): The rule that triggered the alert.
        Returns:
            Alert: The created alert object (not saved to DB here).
        """
        try:
            action_details = json.loads(rule.action_details_json) if isinstance(rule.action_details_json, str) else rule.action_details_json
        except json.JSONDecodeError:
             print(f"Error decoding action_details_json for rule {rule.id}")
             # Provide default values or handle error appropriately
             action_details = {"type": "generic", "level": "LOW", "message": "Default alert message", "explanation": "Could not parse action details."}


        # Enhance explanation with context if available
        explanation = action_details.get("explanation", "Rule triggered.")
        if 'triggering_person_id' in self.frame_context and 'missing_ppe' in self.frame_context:
             explanation += f" Employee ID {self.frame_context['triggering_person_id']} missing PPE: {', '.join(self.frame_context['missing_ppe'])}."

        # Determine relevant IDs from context
        # This might need refinement based on the specific condition that triggered the alert
        employee_id = self.frame_context.get("triggering_person_id") # Prioritize person causing trigger
        if not employee_id and self.frame_context.get("detected_persons"):
             employee_id = self.frame_context.get("detected_persons")[0] # Fallback to first detected person

        zone_id = None
        if employee_id and self.frame_context.get("zones_entered"):
            zone_id = self.frame_context.get("zones_entered").get(employee_id) # Zone the triggering person entered


        alert = Alert(
            timestamp=self.frame_context.get("timestamp", datetime.now()),
            type=action_details.get("type", "Rule Violation"),
            level=action_details.get("level", "MEDIUM"),
            message=action_details.get("message", "Alert Triggered"), # Added message field
            explanation=explanation,
            camera_id=self.frame_context.get("camera_id"),
            zone_id=zone_id, # Use determined zone_id
            employee_id=employee_id, # Use determined employee_id
            rule_id=rule.id, # Link alert back to the rule
            resolved=False # Alerts start as unresolved
            # screenshot field would be set later when saving if applicable
        )
        return alert

    def infer(self):
        """
        Perform inference based on the provided rules and frame context.
        Clears previous results and alerts before running.
        Returns:
            list: List of newly generated Alert objects (not saved to DB).
        """
        self.alerts = []
        self.inference_results = []
        for rule in self.rules:
            if rule.is_active:
                # Reset context potentially modified by previous rule evaluations in the same frame
                if 'triggering_person_id' in self.frame_context: del self.frame_context['triggering_person_id']
                if 'missing_ppe' in self.frame_context: del self.frame_context['missing_ppe']

                if self._evaluate_conditions(rule):
                    alert = self._create_alert(rule)
                    self.alerts.append(alert)
                    self.inference_results.append({"rule_id": rule.id, "alert_message": alert.message}) # Store basic result info
        return self.alerts
