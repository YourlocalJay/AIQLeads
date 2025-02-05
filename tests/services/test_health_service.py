import pytest
from unittest.mock import patch, AsyncMock
from src.services.health_service import HealthService


@pytest.mark.asyncio
async def test_check_database():
    health_service = HealthService()

    with patch("asyncpg.connect", new_callable=AsyncMock) as mock_connect:
        mock_conn = AsyncMock()
        mock_connect.return_value = mock_conn

        result = await health_service.check_database()
        assert result["status"] == "healthy"
        mock_conn.execute.assert_called_once_with("SELECT 1")
        mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_check_cache():
    health_service = HealthService()

    with patch("aioredis.create_redis_pool", new_callable=AsyncMock) as mock_redis:
        mock_conn = AsyncMock()
        mock_redis.return_value = mock_conn

        result = await health_service.check_cache()
        assert result["status"] == "healthy"
        mock_conn.ping.assert_called_once()
        mock_conn.close.assert_called_once()


@pytest.mark.asyncio
async def test_check_search():
    health_service = HealthService()

    with patch("elasticsearch.AsyncElasticsearch", new_callable=AsyncMock) as mock_es:
        mock_es.return_value.cluster.health.return_value = {"status": "green"}

        result = await health_service.check_search()
        assert result["status"] == "healthy"
        assert result["cluster_status"] == "green"


@pytest.mark.asyncio
async def test_check_all_services():
    health_service = HealthService()

    with patch.multiple(
        "src.services.health_service.HealthService",
        check_database=AsyncMock(return_value={"status": "healthy"}),
        check_cache=AsyncMock(return_value={"status": "healthy"}),
        check_search=AsyncMock(return_value={"status": "healthy"}),
    ):
        result = await health_service.check_all_services()
        assert result["database"]["status"] == "healthy"
        assert result["cache"]["status"] == "healthy"
        assert result["search"]["status"] == "healthy"
        assert "timestamp" in result
