class FeatureEngineeringError(Exception):
    """Base exception for feature engineering errors."""
    pass

class PipelineConfigError(FeatureEngineeringError):
    """Raised when there's an error in pipeline configuration."""
    pass

class PreprocessingError(FeatureEngineeringError):
    """Raised when preprocessing fails."""
    pass

class FeatureExtractionError(FeatureEngineeringError):
    """Raised when feature extraction fails."""
    pass

class ValidationError(FeatureEngineeringError):
    """Raised when feature validation fails."""
    pass

class StorageError(FeatureEngineeringError):
    """Raised when feature storage fails."""
    pass