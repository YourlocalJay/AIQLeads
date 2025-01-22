import os
import pytest
import docker
import requests
from time import sleep
from sqlalchemy import create_engine, text
from redis import Redis
from elasticsearch import Elasticsearch

@pytest.fixture(scope='session')
def docker_client():
    return docker.from_env()

@pytest.fixture(scope='session')
def docker_services(docker_client):
    # Start services using docker-compose
    os.system('docker-compose up -d')
    
    # Wait for services to be ready
    sleep(30)
    
    yield
    
    # Cleanup
    os.system('docker-compose down -v')

def test_postgres_connection(docker_services):
    """Test PostgreSQL connection and PostGIS extension"""
    db_params = {
        'host': 'localhost',
        'port': 5432,
        'database': 'aiqleads',
        'user': 'postgres',
        'password': 'password'
    }
    
    # Try to connect multiple times (container might need time to start)
    for _ in range(5):
        try:
            engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@"
                                 f"{db_params['host']}:{db_params['port']}/{db_params['database']}")
            
            with engine.connect() as conn:
                # Test basic connection
                result = conn.execute(text('SELECT 1')).scalar()
                assert result == 1
                
                # Test PostGIS extension
                result = conn.execute(text('SELECT PostGIS_Version()')).scalar()
                assert result and 'POSTGIS' in result
            break
        except Exception:
            sleep(5)
            continue

def test_redis_connection(docker_services):
    """Test Redis connection"""
    redis_client = Redis(host='localhost', port=6379, db=0)
    
    # Test set and get
    redis_client.set('test_key', 'test_value')
    assert redis_client.get('test_key').decode('utf-8') == 'test_value'
    
    # Clean up
    redis_client.delete('test_key')

def test_elasticsearch_connection(docker_services):
    """Test Elasticsearch connection and basic operations"""
    es = Elasticsearch(['http://localhost:9200'])
    
    # Test cluster health
    health = es.cluster.health()
    assert health['status'] in ['green', 'yellow']
    
    # Test index creation and document indexing
    index_name = 'test_index'
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
    
    es.indices.create(index=index_name)
    doc = {'test_field': 'test_value'}
    es.index(index=index_name, body=doc, refresh=True)
    
    # Test search
    search_result = es.search(index=index_name, body={'query': {'match_all': {}}})
    assert search_result['hits']['total']['value'] == 1
    
    # Clean up
    es.indices.delete(index=index_name)

def test_prometheus_grafana_setup(docker_services):
    """Test Prometheus and Grafana are accessible"""
    # Test Prometheus
    prometheus_response = requests.get('http://localhost:9090/-/healthy')
    assert prometheus_response.status_code == 200
    
    # Test Grafana
    grafana_response = requests.get('http://localhost:3000/api/health')
    assert grafana_response.status_code == 200

def test_app_container(docker_services):
    """Test the main application container"""
    response = requests.get('http://localhost:8000/docs')
    assert response.status_code == 200
    assert 'swagger' in response.text.lower()