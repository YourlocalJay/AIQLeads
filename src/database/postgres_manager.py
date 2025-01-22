from typing import Optional, Generator
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from src.config.settings import get_database_url
import logging

Base = declarative_base()

class PostgresManager:
    """
    Manages PostgreSQL database connections and sessions.
    Implements connection pooling and context management for database operations.
    """
    _instance: Optional['PostgresManager'] = None
    _engine: Optional[Engine] = None
    _SessionLocal: Optional[sessionmaker] = None

    def __new__(cls) -> 'PostgresManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize database engine and session factory"""
        if not self._engine:
            logging.info("Initializing database engine and session factory...")
            self._engine = create_engine(
                get_database_url(),
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            self._SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )
            logging.info("Database engine and session factory initialized.")

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Provides a transactional scope around a series of operations.
        Usage:
            with postgres_manager.get_session() as session:
                session.query(Model).all()
        """
        if not self._SessionLocal:
            logging.error("Session factory is not initialized.")
            raise RuntimeError("Database not initialized")

        session = self._SessionLocal()
        try:
            logging.debug("Session started.")
            yield session
            session.commit()
            logging.debug("Session committed.")
        except Exception as e:
            logging.error(f"Session rollback due to: {e}")
            session.rollback()
            raise
        finally:
            session.close()
            logging.debug("Session closed.")

    def create_database(self) -> None:
        """Create all database tables"""
        if not self._engine:
            logging.error("Cannot create database tables: Engine not initialized.")
            raise RuntimeError("Database engine not initialized")

        logging.info("Creating database tables...")
        Base.metadata.create_all(self._engine)
        logging.info("Database tables created successfully.")

    def get_engine(self) -> Engine:
        """Get the SQLAlchemy engine instance"""
        if not self._engine:
            logging.error("Database engine is not initialized.")
            raise RuntimeError("Database engine not initialized")
        return self._engine

# Global instance for database management
postgres_manager = PostgresManager()