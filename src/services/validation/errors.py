from typing import Dict, Any, Optional
from enum import Enum
import logging

class ValidationErrorType(Enum):
    SCHEMA_ERROR = "schema_error"
    DATA_TYPE_ERROR = "data_type_error"
    MISSING_FIELD = "missing_field"
    INVALID_FORMAT = "invalid_format"
    BUSINESS_RULE = "business_rule"

class ValidationError(Exception):
    def __init__(
        self, 
        error_type: ValidationErrorType,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error_type = error_type
        self.message = message
        self.field = field
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_type": self.error_type.value,
            "message": self.message,
            "field": self.field,
            "details": self.details
        }

def handle_validation_error(error: ValidationError) -> Dict[str, Any]:
    logging.error(f"Validation error: {error.message}", extra={
        "error_type": error.error_type.value,
        "field": error.field,
        "details": error.details
    })
    
    return {
        "status": "error",
        "code": "VALIDATION_ERROR",
        **error.to_dict()
    }