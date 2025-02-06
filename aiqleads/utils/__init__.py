"""Utility functions and helpers.

This package contains utility functions and helper classes used across the project.
Currently includes:
- Logging configuration
- Path validation
- Status tracking helpers
"""

from .logging import setup_logger

__all__ = ['setup_logger']