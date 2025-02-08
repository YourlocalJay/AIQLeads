"""
Chat sequence validation system
Implements comprehensive validation for chat sequences
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum, auto

class ValidationResult:
    def __init__(self, success: bool, message: str = "", data: Dict[str, Any] = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
        
class ValidationType(Enum):
    INITIALIZATION = auto()
    STATE_CHANGE = auto()
    CONTINUATION = auto()
    INTEGRATION = auto()
    EXIT = auto()
    
class SequenceValidator:
    def __init__(self):
        self.validation_history = []
        self.error_handlers = {}
        
    def validate_initialization(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate chat initialization sequence"""
        required_fields = [
            "repository",
            "branch",
            "access",
            "history"
        ]
        
        # Check required fields
        missing_fields = [f for f in required_fields if f not in data]
        if missing_fields:
            return ValidationResult(
                success=False,
                message=f"Missing required fields: {missing_fields}",
                data={"missing_fields": missing_fields}
            )
            
        # Validate field values
        if not data["repository"] or not data["branch"]:
            return ValidationResult(
                success=False,
                message="Repository and branch must not be empty",
                data={"invalid_fields": ["repository", "branch"]}
            )
            
        # Validate access type
        valid_access = ["full", "read", "write"]
        if data["access"] not in valid_access:
            return ValidationResult(
                success=False,
                message=f"Invalid access type. Must be one of: {valid_access}",
                data={"invalid_access": data["access"]}
            )
            
        return ValidationResult(
            success=True,
            message="Initialization validation successful",
            data={"validated_fields": required_fields}
        )
        
    def validate_state_change(self, from_state: str, to_state: str, 
                            context: Dict[str, Any]) -> ValidationResult:
        """Validate state transitions"""
        valid_transitions = {
            "initial": ["active"],
            "active": ["closing", "error"],
            "closing": ["closed"],
            "error": ["active", "closed"],
            "closed": []
        }
        
        # Check valid transition
        if from_state not in valid_transitions:
            return ValidationResult(
                success=False,
                message=f"Invalid from_state: {from_state}",
                data={"invalid_state": from_state}
            )
            
        if to_state not in valid_transitions[from_state]:
            return ValidationResult(
                success=False,
                message=f"Invalid transition: {from_state} -> {to_state}",
                data={
                    "from_state": from_state,
                    "to_state": to_state,
                    "valid_transitions": valid_transitions[from_state]
                }
            )
            
        # Validate context for transition
        if not self._validate_transition_context(from_state, to_state, context):
            return ValidationResult(
                success=False,
                message="Invalid transition context",
                data={"context": context}
            )
            
        return ValidationResult(
            success=True,
            message="State transition validation successful",
            data={
                "from_state": from_state,
                "to_state": to_state,
                "context": context
            }
        )
        
    def validate_continuation(self, continuation_data: Dict[str, Any]) -> ValidationResult:
        """Validate continuation data"""
        required_fields = [
            "sequence_id",
            "repository",
            "branch",
            "timestamp",
            "state"
        ]
        
        # Check required fields
        missing_fields = [f for f in required_fields if f not in continuation_data]
        if missing_fields:
            return ValidationResult(
                success=False,
                message=f"Missing required continuation fields: {missing_fields}",
                data={"missing_fields": missing_fields}
            )
            
        # Validate timestamp
        if not isinstance(continuation_data["timestamp"], datetime):
            return ValidationResult(
                success=False,
                message="Invalid timestamp format",
                data={"invalid_field": "timestamp"}
            )
            
        # Validate state
        if continuation_data["state"] not in ["active", "closing", "closed", "error"]:
            return ValidationResult(
                success=False,
                message="Invalid state in continuation data",
                data={"invalid_state": continuation_data["state"]}
            )
            
        return ValidationResult(
            success=True,
            message="Continuation data validation successful",
            data={"validated_fields": required_fields}
        )
        
    def validate_exit(self, exit_data: Dict[str, Any]) -> ValidationResult:
        """Validate exit sequence"""
        required_fields = [
            "sequence_id",
            "final_state",
            "continuation_data",
            "history_preserved"
        ]
        
        # Check required fields
        missing_fields = [f for f in required_fields if f not in exit_data]
        if missing_fields:
            return ValidationResult(
                success=False,
                message=f"Missing required exit fields: {missing_fields}",
                data={"missing_fields": missing_fields}
            )
            
        # Validate final state
        if exit_data["final_state"] != "closed":
            return ValidationResult(
                success=False,
                message="Invalid final state",
                data={"invalid_state": exit_data["final_state"]}
            )
            
        # Validate continuation data
        continuation_result = self.validate_continuation(exit_data["continuation_data"])
        if not continuation_result.success:
            return continuation_result
            
        return ValidationResult(
            success=True,
            message="Exit sequence validation successful",
            data={
                "validated_fields": required_fields,
                "continuation_validation": continuation_result.data
            }
        )
        
    def validate_integration_point(self, point_name: str, point_data: Dict[str, Any],
                                current_state: str) -> ValidationResult:
        """Validate integration points"""
        valid_points = {
            "initialization": ["initial"],
            "message_processing": ["active"],
            "state_change": ["active", "closing"],
            "exit": ["closing"]
        }
        
        # Check valid integration point
        if point_name not in valid_points:
            return ValidationResult(
                success=False,
                message=f"Invalid integration point: {point_name}",
                data={"invalid_point": point_name}
            )
            
        # Check state compatibility
        if current_state not in valid_points[point_name]:
            return ValidationResult(
                success=False,
                message=f"Invalid state for integration point: {current_state}",
                data={
                    "point": point_name,
                    "current_state": current_state,
                    "valid_states": valid_points[point_name]
                }
            )
            
        # Validate point-specific data
        if not self._validate_point_data(point_name, point_data):
            return ValidationResult(
                success=False,
                message="Invalid integration point data",
                data={"point_data": point_data}
            )
            
        return ValidationResult(
            success=True,
            message="Integration point validation successful",
            data={
                "point": point_name,
                "state": current_state,
                "validated_data": point_data
            }
        )
        
    def _validate_transition_context(self, from_state: str, to_state: str,
                                 context: Dict[str, Any]) -> bool:
        """Validate context for state transition"""
        required_context = {
            "initial-active": ["repository", "branch"],
            "active-closing": ["history"],
            "closing-closed": ["continuation_data"],
            "error-active": ["error_details", "recovery_plan"]
        }
        
        transition_key = f"{from_state}-{to_state}"
        if transition_key not in required_context:
            return True
            
        return all(field in context for field in required_context[transition_key])
        
    def _validate_point_data(self, point_name: str, data: Dict[str, Any]) -> bool:
        """Validate data for specific integration point"""
        required_data = {
            "initialization": ["type", "data"],
            "message_processing": ["type", "data"],
            "state_change": ["type", "data"],
            "exit": ["type", "data"]
        }
        
        return all(field in data for field in required_data[point_name])