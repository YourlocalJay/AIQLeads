import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Severity levels for errors in the feature engineering pipeline."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    """Structured context for feature engineering errors."""
    timestamp: str = datetime.utcnow().isoformat()
    component: str = "feature_engineering"
    severity: ErrorSeverity = ErrorSeverity.ERROR
    details: Dict[str, Any] = None
    cause: Optional[Exception] = None
    trace_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary suitable for logging."""
        return {
            "timestamp": self.timestamp,
            "component": self.component,
            "severity": self.severity.value,
            "details": self.details or {},
            "cause": str(self.cause) if self.cause else None,
            "trace_id": self.trace_id
        }

class FeatureEngineeringError(Exception):
    """
    Base class for exceptions in the feature engineering module.
    
    Examples:
        >>> try:
        ...     raise FeatureEngineeringError("Configuration missing")
        ... except FeatureEngineeringError as e:
        ...     print(f"Error: {e}")
        Error: Configuration missing
    
    Attributes:
        message (str): Human readable error message
        context (ErrorContext): Structured error context
    """
    
    def __init__(
        self, 
        message: str, 
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        trace_id: Optional[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = ErrorContext(
            severity=severity,
            details=details,
            cause=cause,
            trace_id=trace_id
        )
        
        # Log structured error information
        self._log_error()
    
    def _log_error(self) -> None:
        """Log structured error information."""
        log_data = {
            "error_type": self.__class__.__name__,
            "message": self.message,
            **self.context.to_dict()
        }
        
        # Convert to JSON for structured logging
        log_message = json.dumps(log_data)
        
        if self.context.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif self.context.severity == ErrorSeverity.ERROR:
            logger.error(log_message)
        elif self.context.severity == ErrorSeverity.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)

class PreprocessingError(FeatureEngineeringError):
    """
    Exception raised for errors during preprocessing.
    
    Examples:
        >>> try:
        ...     raise PreprocessingError(
        ...         message="Missing required field",
        ...         preprocessor_name="DataCleaner",
        ...         field_name="property_type"
        ...     )
        ... except PreprocessingError as e:
        ...     print(f"Error in {e.context.details['preprocessor']}: {e}")
        Error in DataCleaner: Missing required field
    
    Common scenarios:
        - Missing required input fields
        - Data type conversion failures
        - Validation rule violations
        - Resource access errors during preprocessing
    """
    
    def __init__(
        self,
        message: str,
        preprocessor_name: str,
        field_name: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        **kwargs
    ):
        details = {
            "preprocessor": preprocessor_name,
            "field": field_name,
            "input_sample": self._sanitize_input(input_data) if input_data else None,
            **kwargs.get("details", {})
        }
        super().__init__(
            message,
            severity=severity,
            details=details,
            cause=kwargs.get("cause"),
            trace_id=kwargs.get("trace_id")
        )
    
    @staticmethod
    def _sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive information from input data."""
        # Add sanitization logic here
        return data

class ExtractionError(FeatureEngineeringError):
    """
    Exception raised for errors during feature extraction.
    
    Examples:
        >>> try:
        ...     raise ExtractionError(
        ...         message="Feature calculation failed",
        ...         extractor_name="GeoFeatureExtractor",
        ...         feature_name="distance_to_center"
        ...     )
        ... except ExtractionError as e:
        ...     print(f"Failed to extract {e.context.details['feature']}")
        Failed to extract distance_to_center
    
    Common scenarios:
        - Computation errors in feature calculations
        - Missing dependencies for feature generation
        - Resource timeouts during extraction
        - Invalid input data for feature computation
    """
    
    def __init__(
        self,
        message: str,
        extractor_name: str,
        feature_name: Optional[str] = None,
        computation_details: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        **kwargs
    ):
        details = {
            "extractor": extractor_name,
            "feature": feature_name,
            "computation": computation_details,
            **kwargs.get("details", {})
        }
        super().__init__(
            message,
            severity=severity,
            details=details,
            cause=kwargs.get("cause"),
            trace_id=kwargs.get("trace_id")
        )

class ValidationError(FeatureEngineeringError):
    """
    Exception raised for errors during validation.
    
    Examples:
        >>> try:
        ...     raise ValidationError(
        ...         message="Feature values out of expected range",
        ...         validator_name="RangeValidator",
        ...         failed_validations=[("price", "above_maximum")]
        ...     )
        ... except ValidationError as e:
        ...     print(f"Validation failed: {e}")
        Validation failed: Feature values out of expected range
    
    Common scenarios:
        - Feature values outside acceptable ranges
        - Missing required features in output
        - Data type mismatches in features
        - Correlation or dependency violations
    """
    
    def __init__(
        self,
        message: str,
        validator_name: str,
        failed_validations: Optional[List[tuple]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        **kwargs
    ):
        details = {
            "validator": validator_name,
            "failed_validations": failed_validations or [],
            **kwargs.get("details", {})
        }
        super().__init__(
            message,
            severity=severity,
            details=details,
            cause=kwargs.get("cause"),
            trace_id=kwargs.get("trace_id")
        )

class StorageError(FeatureEngineeringError):
    """
    Exception raised for errors during feature storage.
    
    Examples:
        >>> try:
        ...     raise StorageError(
        ...         message="Failed to store features",
        ...         operation="write",
        ...         storage_type="redis",
        ...         affected_features=["price_normalized"]
        ...     )
        ... except StorageError as e:
        ...     print(f"Storage error: {e}")
        Storage error: Failed to store features
    
    Common scenarios:
        - Database connection failures
        - Write permission issues
        - Storage quota exceeded
        - Data integrity violations
    """
    
    def __init__(
        self,
        message: str,
        operation: str,
        storage_type: str,
        affected_features: Optional[List[str]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        **kwargs
    ):
        details = {
            "operation": operation,
            "storage_type": storage_type,
            "affected_features": affected_features or [],
            **kwargs.get("details", {})
        }
        super().__init__(
            message,
            severity=severity,
            details=details,
            cause=kwargs.get("cause"),
            trace_id=kwargs.get("trace_id")
        )

class ConfigurationError(FeatureEngineeringError):
    """
    Exception raised for configuration-related errors.
    
    Examples:
        >>> try:
        ...     raise ConfigurationError(
        ...         message="Invalid configuration value",
        ...         config_section="feature_extractors",
        ...         invalid_keys=["batch_size"]
        ...     )
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")
        Configuration error: Invalid configuration value
    
    Common scenarios:
        - Missing required configuration values
        - Invalid configuration types or formats
        - Configuration dependency conflicts
        - Resource allocation configuration errors
    """
    
    def __init__(
        self,
        message: str,
        config_section: str,
        invalid_keys: Optional[List[str]] = None,
        config_context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        **kwargs
    ):
        details = {
            "config_section": config_section,
            "invalid_keys": invalid_keys or [],
            "config_context": config_context,
            **kwargs.get("details", {})
        }
        super().__init__(
            message,
            severity=severity,
            details=details,
            cause=kwargs.get("cause"),
            trace_id=kwargs.get("trace_id")
        )