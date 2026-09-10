from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "CivicPulse API"
    assert data["status"] == "running"
    assert "docs" in data
    assert "health" in data


def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["project_name"] == "CivicPulse API"
    assert "environment" in data
    assert "version" in data
    assert "database" in data
    assert "connected" in data["database"]
    assert "status" in data["database"]
    assert "message" in data["database"]


def test_standardized_not_found(client: TestClient):
    response = client.get("/api/v1/nonexistent-route-xyz")
    assert response.status_code == 404
    data = response.json()
    assert data["error"] is True
    assert data["status_code"] == 404
    assert "message" in data
