import pytest
from src.services.api.integration import APIIntegration, APIIntegrationError

def test_api_request_success(requests_mock):
    api = APIIntegration('http://api.test')
    requests_mock.get('http://api.test/data', json={'status': 'ok'})
    response = api.request('GET', 'data')
    assert response['status'] == 'ok'

def test_api_request_retry(requests_mock):
    api = APIIntegration('http://api.test')
    requests_mock.register_uri('GET', 'http://api.test/data',
                             [{'status_code': 500}, {'json': {'status': 'ok'}}])
    response = api.request('GET', 'data')
    assert response['status'] == 'ok'