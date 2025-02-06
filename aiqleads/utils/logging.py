"""Logging utility for AIQLeads."""

import os
import logging
from typing import Optional
from datetime import datetime
from pathlib import Path

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up and configure a logger.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        # Console handler
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # File handler (log to data/logs directory)
        try:
            log_dir = os.path.join("aiqleads", "data", "logs")
            os.makedirs(log_dir, exist_ok=True)
            
            today = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(log_dir, f"{today}.log")
            
            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            # If file logging fails, just log to console
            logger.warning(f"Failed to set up file logging: {e}")
    
    return logger

def get_log_path(date: Optional[str] = None) -> str:
    """Get path to log file for specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format (default: today)
        
    Returns:
        str: Path to log file
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
        
    return os.path.join("aiqleads", "data", "logs", f"{date}.log")