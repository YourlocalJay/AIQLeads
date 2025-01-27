from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import logging
from datetime import datetime

from ..exceptions import PreprocessingError

logger = logging.getLogger(__name__)

class PreprocessorConfig(BaseModel):
    """Base configuration model for preprocessors."""
    name: str = Field(..., description="Unique identifier for the preprocessor")
    enabled: bool = Field(True, description="Whether this preprocessor is active")
    input_fields: List[str] = Field(..., description="Fields required for preprocessing")
    output_fields: List[str] = Field(..., description="Fields produced by preprocessing")
    validation_rules: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional validation rules for input data"
    )
    
class PreprocessingMetrics:
    """Tracks preprocessing performance metrics."""
    
    def __init__(self):
        self.processed_count: int = 0
        self.error_count: int = 0
        self.processing_times: List[float] = []
        self.start_time = datetime.now()
    
    def record_success(self, processing_time: float) -> None:
        """Record a successful preprocessing operation."""
        self.processed_count += 1
        self.processing_times.append(processing_time)
    
    def record_error(self) -> None:
        """Record a preprocessing error."""
        self.error_count += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current preprocessing metrics."""
        avg_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times else 0
        )
        return {
            "processed_count": self.processed_count,
            "error_count": self.error_count,
            "average_processing_time_ms": avg_time,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "success_rate": (
                (self.processed_count / (self.processed_count + self.error_count)) * 100
                if (self.processed_count + self.error_count) > 0 else 0
            )
        }

class BasePreprocessor(ABC):
    """Abstract base class for all preprocessors in the pipeline."""
    
    def __init__(self, config: PreprocessorConfig):
        """
        Initialize the preprocessor with configuration.
        
        Args:
            config (PreprocessorConfig): Configuration for the preprocessor
        
        Raises:
            ConfigurationError: If the configuration is invalid
        """
        self.config = config
        self.metrics = PreprocessingMetrics()
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate preprocessor configuration."""
        if not self.config.enabled:
            logger.info(f"Preprocessor {self.config.name} is disabled")
            return
            
        if not self.config.input_fields:
            raise ValueError(f"No input fields specified for {self.config.name}")
            
        if not self.config.output_fields:
            raise ValueError(f"No output fields specified for {self.config.name}")
    
    def _validate_input(self, data: Dict[str, Any]) -> None:
        """
        Validate input data against configuration.
        
        Args:
            data (Dict[str, Any]): Input data to validate
            
        Raises:
            PreprocessingError: If validation fails
        """
        missing_fields = [
            field for field in self.config.input_fields
            if field not in data
        ]
        
        if missing_fields:
            raise PreprocessingError(
                message="Missing required input fields",
                preprocessor_name=self.config.name,
                details={"missing_fields": missing_fields}
            )
            
        if self.config.validation_rules:
            self._apply_validation_rules(data)
    
    def _apply_validation_rules(self, data: Dict[str, Any]) -> None:
        """
        Apply configured validation rules to input data.
        
        Args:
            data (Dict[str, Any]): Input data to validate
            
        Raises:
            PreprocessingError: If validation rules fail
        """
        pass  # Implement in subclasses if needed
    
    @abstractmethod
    async def _preprocess_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Core preprocessing logic to be implemented by subclasses.
        
        Args:
            data (Dict[str, Any]): Validated input data
            
        Returns:
            Dict[str, Any]: Preprocessed data
            
        Raises:
            PreprocessingError: If preprocessing fails
        """
        pass
    
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data through the preprocessing pipeline.
        
        Args:
            data (Dict[str, Any]): Raw input data
            
        Returns:
            Dict[str, Any]: Preprocessed data
            
        Raises:
            PreprocessingError: If preprocessing fails
        """
        start_time = datetime.now()
        
        try:
            if not self.config.enabled:
                return data
                
            self._validate_input(data)
            result = await self._preprocess_data(data)
            
            # Validate output contains all expected fields
            missing_outputs = [
                field for field in self.config.output_fields
                if field not in result
            ]
            if missing_outputs:
                raise PreprocessingError(
                    message="Missing required output fields",
                    preprocessor_name=self.config.name,
                    details={"missing_fields": missing_outputs}
                )
            
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.record_success(processing_time)
            
            return result
            
        except Exception as e:
            self.metrics.record_error()
            if isinstance(e, PreprocessingError):
                raise
            raise PreprocessingError(
                message=f"Preprocessing failed: {str(e)}",
                preprocessor_name=self.config.name,
                cause=e
            )
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get preprocessor metadata and metrics."""
        return {
            "name": self.config.name,
            "enabled": self.config.enabled,
            "input_fields": self.config.input_fields,
            "output_fields": self.config.output_fields,
            "metrics": self.metrics.get_metrics()
        }