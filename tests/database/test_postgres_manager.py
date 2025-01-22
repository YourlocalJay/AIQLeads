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

    @patch('src.database.postgres_manager.create_engine')
    def test_initialization_failure(self, mock_create_engine):
        """Test handling of initialization failures"""
        mock_create_engine.side_effect = Exception("Connection failed")

        with pytest.raises(ConnectionError) as exc_info:
            PostgresManager()
        assert "Database initialization failed" in str(exc_info.value)

    def test_get_session_success(self, mock_session, mock_session_local):
        """Test successful session creation and management"""
        manager = PostgresManager()
        manager._SessionLocal = mock_session_local
        mock_session_local.return_value = mock_session

        with manager.get_session() as session:
            assert session == mock_session

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        assert not mock_session.rollback.called

    def test_get_session_transaction_failure(self, mock_session, mock_session_local):
        """Test session rollback on transaction failure"""
        manager = PostgresManager()
        manager._SessionLocal = mock_session_local
        mock_session_local.return_value = mock_session
        mock_session.commit.side_effect = SQLAlchemyError("Transaction failed")

        with pytest.raises(DatabaseError):
            with manager.get_session() as session:
                pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    def test_get_session_without_initialization(self):
        """Test session creation without initialization"""
        manager = PostgresManager()
        manager._SessionLocal = None

        with pytest.raises(ConnectionError) as exc_info:
            with manager.get_session() as session:
                pass
        assert "not initialized" in str(exc_info.value)

    @patch.object(Base.metadata, 'create_all')
    def test_create_database_all_tables(self, mock_create_all, mock_engine):
        """Test creation of all database tables"""
        manager = PostgresManager()
        manager._engine = mock_engine

        manager.create_database()
        mock_create_all.assert_called_once_with(mock_engine)

    def test_create_database_specific_tables(self, mock_engine):
        """Test creation of specific database tables"""
        manager = PostgresManager()
        manager._engine = mock_engine

        mock_table1 = Mock()
        mock_table1.__tablename__ = 'table1'
        mock_table1.__table__ = Mock()

        mock_table2 = Mock()
        mock_table2.__tablename__ = 'table2'
        mock_table2.__table__ = Mock()

        manager.create_database([mock_table1, mock_table2])

        mock_table1.__table__.create.assert_called_once_with(mock_engine, checkfirst=True)
        mock_table2.__table__.create.assert_called_once_with(mock_engine, checkfirst=True)