"""
Test suite for the logging utility functionality.
"""
import pytest
import os
import logging
from unittest.mock import patch, MagicMock
from aiqleads.utils.logging import LogManager, RotatingLogger

@pytest.fixture
def log_manager():
    """Create a LogManager instance for testing."""
    return LogManager()

@pytest.fixture
def rotating_logger():
    """Create a RotatingLogger instance for testing."""
    return RotatingLogger("test_logger", "test.log")

def test_log_manager_initialization(log_manager):
    """Test that LogManager initializes correctly."""
    assert log_manager is not None
    assert isinstance(log_manager.loggers, dict)

def test_rotating_logger_initialization(rotating_logger):
    """Test that RotatingLogger initializes correctly."""
    assert rotating_logger is not None
    assert rotating_logger.name == "test_logger"
    assert rotating_logger.log_file == "test.log"

def test_log_manager_get_logger(log_manager):
    """Test getting a logger instance."""
    logger = log_manager.get_logger("test")
    assert isinstance(logger, logging.Logger)
    assert logger.name == "test"

def test_log_manager_duplicate_logger(log_manager):
    """Test getting the same logger twice."""
    logger1 = log_manager.get_logger("test")
    logger2 = log_manager.get_logger("test")
    assert logger1 is logger2

def test_rotating_logger_file_creation(tmp_path):
    """Test log file creation."""
    log_file = tmp_path / "test.log"
    logger = RotatingLogger("test", str(log_file))
    logger.logger.info("Test message")
    assert os.path.exists(log_file)

def test_rotating_logger_rotation(tmp_path):
    """Test log file rotation."""
    log_file = tmp_path / "test.log"
    logger = RotatingLogger("test", str(log_file), max_bytes=100, backup_count=3)
    
    # Write enough data to trigger rotation
    long_message = "x" * 50
    for _ in range(10):
        logger.logger.info(long_message)
    
    # Check that backup files were created
    assert os.path.exists(str(log_file) + ".1")

@pytest.mark.parametrize("log_level", [
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL
])
def test_logging_levels(rotating_logger, log_level):
    """Test all logging levels."""
    with patch('logging.Logger.log') as mock_log:
        rotating_logger.logger.setLevel(log_level)
        rotating_logger.logger.log(log_level, "Test message")
        mock_log.assert_called_once_with(log_level, "Test message")

def test_log_formatting(tmp_path):
    """Test log message formatting."""
    log_file = tmp_path / "test.log"
    logger = RotatingLogger("test", str(log_file))
    test_message = "Test message"
    logger.logger.info(test_message)
    
    with open(log_file) as f:
        log_content = f.read()
        assert test_message in log_content
        assert logger.name in log_content

def test_multiple_handlers(rotating_logger):
    """Test adding multiple handlers to logger."""
    stream_handler = logging.StreamHandler()
    rotating_logger.logger.addHandler(stream_handler)
    assert len(rotating_logger.logger.handlers) > 1

def test_log_manager_configuration(log_manager):
    """Test LogManager configuration options."""
    config = {
        "level": logging.DEBUG,
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
    logger = log_manager.get_logger("test", config)
    assert logger.level == logging.DEBUG

def test_rotating_logger_error_handling(tmp_path):
    """Test error handling in RotatingLogger."""
    invalid_path = "/invalid/path/test.log"
    with pytest.raises(Exception):
        RotatingLogger("test", invalid_path)

@patch('logging.handlers.RotatingFileHandler')
def test_rotating_logger_handler_creation(mock_handler):
    """Test creation of rotating file handler."""
    logger = RotatingLogger("test", "test.log")
    mock_handler.assert_called_once()

def test_log_manager_cleanup(log_manager):
    """Test cleanup of logger resources."""
    logger = log_manager.get_logger("test")
    log_manager.cleanup()
    assert not log_manager.loggers

def test_rotating_logger_context_manager(tmp_path):
    """Test using RotatingLogger as a context manager."""
    log_file = tmp_path / "test.log"
    with RotatingLogger("test", str(log_file)) as logger:
        logger.logger.info("Test message")
    assert os.path.exists(log_file)

def test_concurrent_logging(tmp_path):
    """Test logging from multiple sources concurrently."""
    log_file = tmp_path / "test.log"
    logger1 = RotatingLogger("test1", str(log_file))
    logger2 = RotatingLogger("test2", str(log_file))
    
    logger1.logger.info("Message from logger1")
    logger2.logger.info("Message from logger2")
    
    with open(log_file) as f:
        content = f.read()
        assert "logger1" in content
        assert "logger2" in content

def test_log_manager_get_all_loggers(log_manager):
    """Test retrieving all registered loggers."""
    logger1 = log_manager.get_logger("test1")
    logger2 = log_manager.get_logger("test2")
    
    loggers = log_manager.get_all_loggers()
    assert len(loggers) == 2
    assert "test1" in loggers
    assert "test2" in loggers