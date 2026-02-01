import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_main():
    response = client.get("/api/")
    assert response.status_code == 200
    assert "version" in response.json()

def test_list_sorties():
    response = client.get("/api/sorties")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_invalid_sortie():
    response = client.get("/api/sorties/999999/telemetry")
    assert response.status_code == 404
