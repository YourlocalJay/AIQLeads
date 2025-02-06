"""Core package containing primary business logic.

This package includes:
- Project tracking and status management
- Lead scoring and valuation
- Recommendation engine
"""

from .project_tracking import ProjectTracker, get_tracker

__all__ = ['ProjectTracker', 'get_tracker']