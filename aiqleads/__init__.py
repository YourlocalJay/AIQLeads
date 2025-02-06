"""AIQLeads package initialization.

This package provides a lead marketplace platform with AI-driven recommendations.
"""

__version__ = "0.1.0"
__author__ = "AIQLeads Team"
__description__ = "AI-powered lead marketplace for real estate professionals"

from .core import project_tracking
from .utils import logging

__all__ = ['project_tracking', 'logging']