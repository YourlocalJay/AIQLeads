import logging
from typing import Optional, Any, Dict

logger = logging.getLogger(__name__)

class FeatureEngineeringError(Exception):
    """
    Base class for exceptions in the feature engineering module.
    
    Attributes:
        message (str): Human readable error message
        details (Optional[Dict[str, Any]]): Additional error context
        cause (Optional[Exception]): Original exception that caused this error
    """
    
    def __init__(
        self, 
        message: str, 
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.cause = cause
        
        # Log the error with context
        logger.error(
            f"{self.__class__.__name__}: {message}",
            extra={
                "error_type": self.__class__.__name__,
                "details": self.details,
                "cause": str(cause) if cause else None
            }
        )

class PreprocessingError(FeatureEngineeringError):
    """
    Exception raised for errors during preprocessing.
    
    This exception is raised when a preprocessing step fails, such as:
    - Data cleaning errors
    - Format conversion issues
    - Missing required fields
    - Invalid data types
    """
    
    def __init__(
        self,
        message: str,
        preprocessor_name: str,
        input_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = {
            "preprocessor": preprocessor_name,
            "input_data": input_data,
            **kwargs.get("details", {})
        }
        super().__init__(message, details=details, cause=kwargs.get("cause"))

class ExtractionError(FeatureEngineeringError):
    """
    Exception raised for errors during feature extraction.
    
    This exception is raised when feature extraction fails, such as:
    - Invalid feature calculations
    - Missing dependencies
    - Resource access errors
    - Computation timeouts
    """
    
    def __init__(
        self,
        message: str,
        extractor_name: str,
        feature_name: Optional[str] = None,
        **kwargs
    ):
        details = {
            "extractor": extractor_name,
            "feature": feature_name,
            **kwargs.get("details", {})
        }
        super().__init__(message, details=details, cause=kwargs.get("cause"))

class ValidationError(FeatureEngineeringError):
    """
    Exception raised for errors during validation.
    
    This exception is raised when feature validation fails, such as:
    - Out of range values
    - Missing required features
    - Data type mismatches
    - Constraint violations
    """
    
    def __init__(
        self,
        message: str,
        validator_name: str,
        failed_rules: Optional[list] = None,
        **kwargs
    ):
        details = {
            "validator": validator_name,
            "failed_rules": failed_rules or [],
            **kwargs.get("details", {})
        }
        super().__init__(message, details=details, cause=kwargs.get("cause"))

class StorageError(FeatureEngineeringError):
    """
    Exception raised for errors during feature storage.
    
    This exception is raised when feature storage operations fail, such as:
    - Database connection errors
    - Write permission issues
    - Storage quota exceeded
    - Data integrity errors
    """
    
    def __init__(
        self,
        message: str,
        operation: str,
        storage_type: str,
        **kwargs
    ):
        details = {
            "operation": operation,
            "storage_type": storage_type,
            **kwargs.get("details", {})
        }
        super().__init__(message, details=details, cause=kwargs.get("cause"))

class ConfigurationError(FeatureEngineeringError):
    """
    Exception raised for configuration-related errors.
    
    This exception is raised when configuration validation or loading fails, such as:
    - Missing required configuration
    - Invalid configuration values
    - Configuration dependency conflicts
    - Schema validation errors
    """
    
    def __init__(
        self,
        message: str,
        config_section: str,
        invalid_keys: Optional[list] = None,
        **kwargs
    ):
        details = {
            "config_section": config_section,
            "invalid_keys": invalid_keys or [],
            **kwargs.get("details", {})
        }
        super().__init__(message, details=details, cause=kwargs.get("cause"))