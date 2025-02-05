import asyncpg
from app.core.config import settings
from app.services.logging import logger

class DatabaseManager:
    """Handles database connections and query execution."""

    def __init__(self, dsn: str = settings.DATABASE_URL):
        self.dsn = dsn
        self.pool = None

    async def connect(self):
        """Establishes a database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn, min_size=1, max_size=10)
            logger.info("Database connection pool established.")
        except Exception as e:
            logger.error(f"Database connection error: {e}")

    async def execute(self, query: str, *args):
        """Executes a SQL query and returns the number of affected rows."""
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch(self, query: str, *args):
        """Executes a SQL query and returns results."""
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def close(self):
        """Closes the database connection pool."""
        await self.pool.close()
        logger.info("Database connection closed.")
