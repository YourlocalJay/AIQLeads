import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from src.main import app

client = TestClient(app)

@pytest.mark.asyncio
async def test_health_check():
    with patch('src.services.health_service.HealthService.check_all_services',
              new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {
            'database': {'status': 'healthy'},
            'cache': {'status': 'healthy'},
            'search': {'status': 'healthy'},
            'timestamp': '2025-01-23T12:00:00'
        }
        
        response = client.get('/api/v1/health')
        assert response.status_code == 200
        assert response.json()['database']['status'] == 'healthy'
        assert response.json()['cache']['status'] == 'healthy'
        assert response.json()['search']['status'] == 'healthy'

@pytest.mark.asyncio
async def test_detailed_health_check():
    with patch('src.services.health_service.HealthService.get_detailed_status',
              new_callable=AsyncMock) as mock_check:
        mock_check.return_value = {
            'database': {'status': 'healthy'},
            'cache': {'status': 'healthy'},
            'search': {'status': 'healthy'},
            'timestamp': '2025-01-23T12:00:00',
            'environment': 'test',
            'api_version': '1.0.0',
            'detailed_checks': {
                'database': {
                    'host': 'localhost',
                    'port': 5432,
                    'pool_size': 5
                },
                'cache': {
                    'host': 'localhost',
                    'port': 6379
                },
                'search': {
                    'host': 'localhost',
                    'port': 9200
                }
            }
        }
        
        response = client.get('/api/v1/health/detailed')
        assert response.status_code == 200
        assert 'detailed_checks' in response.json()
        assert 'database' in response.json()['detailed_checks']
        assert response.json()['environment'] == 'test'