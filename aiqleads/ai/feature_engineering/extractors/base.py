from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseFeatureExtractor(ABC):
    """Base class for all feature extractors."""

    @abstractmethod
    async def extract(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from a single data point."""
        pass

    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """Get list of features this extractor generates."""
        pass

    @abstractmethod
    def get_feature_metadata(self) -> Dict[str, Any]:
        """Get metadata about the features being generated."""
        pass
