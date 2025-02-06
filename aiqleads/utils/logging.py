"""Logging utility for AIQLeads"""

import logging

def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up and configure a logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger