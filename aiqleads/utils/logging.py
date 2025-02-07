"""Logging utility for AIQLeads."""

import os
import logging
import logging.handlers
from typing import Optional
from datetime import datetime, timedelta
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
            
            # Set up rotating file handler
            log_file = os.path.join(log_dir, "aiqleads.log")
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5MB
                backupCount=5,
                encoding='utf-8'
            )
            
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # Clean up old logs
            cleanup_old_logs(log_dir)
            
        except Exception as e:
            # If file logging fails, just log to console
            logger.warning(f"Failed to set up file logging: {e}")
    
    return logger

def cleanup_old_logs(log_dir: str, max_age_days: int = 30) -> None:
    """Clean up log files older than specified age.
    
    Args:
        log_dir: Directory containing log files
        max_age_days: Maximum age of log files in days
    """
    try:
        now = datetime.now()
        max_age = timedelta(days=max_age_days)
        
        for file in Path(log_dir).glob("*.log*"):
            # Skip current log file
            if file.name == "aiqleads.log":
                continue
                
            age = now - datetime.fromtimestamp(file.stat().st_mtime)
            if age > max_age:
                file.unlink()
                
    except Exception as e:
        # Don't raise exceptions for cleanup failures
        logging.warning(f"Failed to clean up old logs: {e}")

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