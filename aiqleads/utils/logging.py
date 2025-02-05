import logging

class Logger:
    """Configurable logging utility for AIQLeads."""

    @staticmethod
    def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
        """Returns a pre-configured logger."""
        logger = logging.getLogger(name)
        logger.setLevel(level)

        if not logger.hasHandlers():
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

logger = Logger.get_logger("AIQLeads")
