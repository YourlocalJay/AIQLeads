import pytest
from fastapi import status

def test_create_user(client, auth_headers):
    user_data = {
        'email': 'newuser@example.com',
        'password': 'SecurePass123!',
        'full_name': 'Test User'
    }
    
    response = client.post(
        '/api/v1/users/',
        json=user_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['email'] == user_data['email']
    assert 'id' in data
    assert 'created_at' in data
    assert 'password' not in data

def test_user_authentication(client):
    # First create a user
    user_data = {
        'email': 'auth@example.com',
        'password': 'SecurePass123!',
        'full_name': 'Auth Test User'
    }
    client.post('/api/v1/users/', json=user_data)
    
    # Try to authenticate
    auth_data = {
        'username': user_data['email'],
        'password': user_data['password']
    }
    response = client.post('/api/v1/auth/token', data=auth_data)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'access_token' in data
    assert data['token_type'] == 'bearer'

def test_get_current_user(client, auth_headers):
    response = client.get(
        '/api/v1/users/me',
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert 'email' in data
    assert 'full_name' in data
    assert 'id' in data