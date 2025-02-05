from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from datetime import datetime
from typing import Optional, Generator, Type, List, Any, Dict
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from src.config.settings import get_settings
from src.database import Base


class DatabaseError(Exception):
    """Base exception for database-related errors"""

    pass


class ConnectionError(DatabaseError):
    """Raised when database connection fails"""

    pass


class PostgresManager:
    """
    Singleton manager for PostgreSQL database connections and session handling.

    Provides centralized database connection management, connection pooling,
    session handling, and health monitoring capabilities.

    Attributes:
        _instance: Singleton instance of PostgresManager
        _engine: SQLAlchemy engine instance
        _SessionLocal: SQLAlchemy session factory
    """

    _instance: Optional[PostgresManager] = None
    _engine: Optional[Engine] = None
    _SessionLocal: Optional[Type[Session]] = None

    def __new__(cls) -> PostgresManager:
        """
        Create or return the singleton instance of PostgresManager.

        Returns:
            PostgresManager: The singleton instance
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        Initialize database engine and session factory with connection pooling.

        Raises:
            ConnectionError: If database initialization fails
        """
        if not self._engine:
            try:
                settings = get_settings()
                logging.info("Initializing database connection...")

                self._engine = create_engine(
                    settings.get_database_url(),
                    pool_pre_ping=True,
                    pool_size=settings.DB_POOL_SIZE,
                    max_overflow=settings.DB_MAX_OVERFLOW,
                    pool_timeout=30,
                    pool_recycle=3600,
                    echo=settings.DEBUG,
                )

                self._SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self._engine,
                    expire_on_commit=False,
                )

                logging.info("Database engine initialized successfully")

            except Exception as e:
                logging.critical(f"Failed to initialize database: {str(e)}")
                raise ConnectionError(
                    f"Database initialization failed: {str(e)}"
                ) from e

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Provide a transactional scope with automatic commit/rollback.

        Yields:
            Session: SQLAlchemy session object

        Raises:
            ConnectionError: When session creation fails
            DatabaseError: When transaction operations fail

        Example:
            with postgres_manager.get_session() as session:
                user = session.query(User).filter_by(id=1).first()
        """
        if not self._SessionLocal:
            raise ConnectionError("Database session factory not initialized")

        session = self._SessionLocal()
        start_time = time.time()

        try:
            yield session
            session.commit()

            duration = time.time() - start_time
            logging.debug(f"Transaction completed successfully in {duration:.2f}s")

        except SQLAlchemyError as e:
            session.rollback()
            logging.error(f"Database transaction failed: {str(e)}")
            raise DatabaseError(f"Transaction failed: {str(e)}") from e

        except Exception as e:
            session.rollback()
            logging.error(f"Unexpected error during transaction: {str(e)}")
            raise

        finally:
            session.close()

    def create_database(self, tables: Optional[List[Type[Base]]] = None) -> None:
        """
        Create database tables for specified models or all models.

        Args:
            tables: Optional list of SQLAlchemy models to create tables for

        Raises:
            ConnectionError: If database engine is not initialized
            DatabaseError: If table creation fails
        """
        if not self._engine:
            raise ConnectionError("Database engine not initialized")

        try:
            logging.info("Creating database tables...")

            if tables:
                for table in tables:
                    table.__table__.create(self._engine, checkfirst=True)
                logging.info(
                    f"Created tables for: {', '.join(t.__tablename__ for t in tables)}"
                )
            else:
                Base.metadata.create_all(self._engine)
                logging.info("All database tables created successfully")

        except Exception as e:
            logging.error(f"Failed to create database tables: {str(e)}")
            raise DatabaseError(f"Table creation failed: {str(e)}") from e

    def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.

        Returns:
            dict: Health status including connection info and pool metrics

        Raises:
            ConnectionError: When health check fails
        """
        try:
            with self.get_engine().connect() as conn:
                # Basic connectivity check
                conn.execute(text("SELECT 1"))

                # Get PostgreSQL version
                version = conn.execute(text("SELECT version();")).scalar()

                # Get connection pool statistics
                pool_status = {
                    "size": self._engine.pool.size(),
                    "checkedin": self._engine.pool.checkedin(),
                    "overflow": self._engine.pool.overflow(),
                    "checkedout": self._engine.pool.checkedout(),
                }

                # Get database size
                db_size = conn.execute(
                    text(
                        """
                    SELECT pg_size_pretty(pg_database_size(current_database()))
                """
                    )
                ).scalar()

                return {
                    "status": "healthy",
                    "version": version,
                    "database_size": db_size,
                    "pool": pool_status,
                    "timestamp": datetime.utcnow().isoformat(),
                }

        except Exception as e:
            logging.error(f"Health check failed: {str(e)}")
            raise ConnectionError(f"Database health check failed: {str(e)}") from e

    def get_engine(self) -> Engine:
        """
        Get the SQLAlchemy engine instance.

        Returns:
            Engine: SQLAlchemy engine instance

        Raises:
            ConnectionError: If engine is not initialized
        """
        if not self._engine:
            raise ConnectionError("Database engine not initialized")
        return self._engine


# Singleton instance for global use
postgres_manager = PostgresManager()
