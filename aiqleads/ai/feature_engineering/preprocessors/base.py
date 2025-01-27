from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePreprocessor(ABC):
    """Base class for all preprocessors in the pipeline."""
    
    @abstractmethod
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single data point."""
        pass
    
    @abstractmethod
    def get_config(self) -> Dict[str, Any]:
        """Get preprocessor configuration."""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """Validate preprocessor configuration and dependencies."""
        pass