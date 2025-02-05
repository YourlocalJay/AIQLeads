from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_create_lead():
    payload = {
        "company_name": "Sample Company",
        "contact_name": "John Doe",
        "email": "johndoe@example.com",
        "phone": "+1-234-567-8900",
        "street_address": "123 Sample St",
        "city": "Sample City",
        "state": "Sample State",
        "postal_code": "12345",
        "country": "Sample Country",
    }
    response = client.post("/leads", json=payload)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["company_name"] == "Sample Company"


def test_get_lead_not_found():
    response = client.get("/leads/9999")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_delete_lead_not_found():
    response = client.delete("/leads/9999")
    assert response.status_code == 404
    assert "detail" in response.json()
