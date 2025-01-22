import pytest
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from src.database.postgres_manager import (
    PostgresManager,
    DatabaseError,
    ConnectionError
)
from src.database import Base

@pytest.fixture
def mock_engine():
    """Fixture for mocked SQLAlchemy engine"""
    engine = Mock()
    engine.pool.size.return_value = 5
    engine.pool.checkedin.return_value = 3
    engine.pool.overflow.return_value = 0
    engine.pool.checkedout.return_value = 2
    return engine

@pytest.fixture
def mock_session():
    """Fixture for mocked SQLAlchemy session"""
    session = Mock(spec=Session)
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session

@pytest.fixture
def mock_session_local():
    """Fixture for mocked session factory"""
    session_local = Mock()
    return session_local

class TestPostgresManager:
    """Test suite for PostgresManager"""

    def test_singleton_instance(self):
        """Test singleton pattern implementation"""
        manager1 = PostgresManager()
        manager2 = PostgresManager()
        assert manager1 is manager2

    @patch('src.database.postgres_manager.create_engine')
    @patch('src.database.postgres_manager.sessionmaker')
    def test_initialization(self, mock_sessionmaker, mock_create_engine, mock_engine):
        """Test database initialization"""
        mock_create_engine.return_value = mock_engine
        mock_sessionmaker.return_value = Mock()

        manager = PostgresManager()
        assert manager._engine is not None
        assert manager._SessionLocal is not None

        mock_create_engine.assert_called_once()
        mock_sessionmaker.assert_called_once()
