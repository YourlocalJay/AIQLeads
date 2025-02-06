import pytest
from fastapi import status

def test_create_lead(client, auth_headers):
    lead_data = {
        'name': 'Test Lead',
        'email': 'test@example.com',
        'phone': '+1234567890',
        'source': 'website'
    }
    
    response = client.post(
        '/api/v1/leads/',
        json=lead_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['name'] == lead_data['name']
    assert 'id' in data
    assert 'created_at' in data
    assert 'ai_score' in data

def test_get_lead(client, auth_headers):
    # First create a lead
    lead_data = {
        'name': 'Test Lead',
        'email': 'test@example.com'
    }
    create_response = client.post(
        '/api/v1/leads/',
        json=lead_data,
        headers=auth_headers
    )
    lead_id = create_response.json()['id']
    
    # Then retrieve it
    response = client.get(
        f'/api/v1/leads/{lead_id}',
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['id'] == lead_id
    assert data['name'] == lead_data['name']

def test_update_lead(client, auth_headers):
    # Create lead first
    lead_data = {
        'name': 'Original Name',
        'email': 'test@example.com'
    }
    create_response = client.post(
        '/api/v1/leads/',
        json=lead_data,
        headers=auth_headers
    )
    lead_id = create_response.json()['id']
    
    # Update the lead
    update_data = {
        'name': 'Updated Name'
    }
    response = client.patch(
        f'/api/v1/leads/{lead_id}',
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['name'] == update_data['name']

def test_delete_lead(client, auth_headers):
    # Create lead first
    lead_data = {
        'name': 'To Delete',
        'email': 'delete@example.com'
    }
    create_response = client.post(
        '/api/v1/leads/',
        json=lead_data,
        headers=auth_headers
    )
    lead_id = create_response.json()['id']
    
    # Delete the lead
    response = client.delete(
        f'/api/v1/leads/{lead_id}',
        headers=auth_headers
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify it's deleted
    get_response = client.get(
        f'/api/v1/leads/{lead_id}',
        headers=auth_headers
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND