from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseValidator(ABC):
    """Base class for all feature validators."""

    @abstractmethod
    async def validate(self, features: Dict[str, Any]) -> bool:
        """Validate a set of features."""
        pass

    @abstractmethod
    def get_validation_report(self) -> Dict[str, Any]:
        """Get detailed validation report."""
        pass
