import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.services.seed_service import seed_sample_data

from backend.app.models import SystemStatus

@pytest.fixture(autouse=True)
def setup_db():
    db = SessionLocal()
    seed_sample_data(db)
    state = db.query(SystemStatus).filter(SystemStatus.key == "DISCOVERY_STATE").first()
    if state:
        state.value = "IDLE"
        db.commit()
    db.close()

def test_root_endpoint():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "online"

def test_check_epic_valid_match():
    with TestClient(app) as client:
        response = client.post("/api/check-epic", json={"epic": "abc1234567"})
        assert response.status_code == 200
        data = response.json()
        assert data["epic"] == "ABC1234567"
        assert data["found"] is True
        assert len(data["records"]) >= 1
        assert data["records"][0]["source"]["url"].startswith("http")

def test_check_epic_no_match():
    with TestClient(app) as client:
        response = client.post("/api/check-epic", json={"epic": "NOT9999999"})
        assert response.status_code == 200
        data = response.json()
        assert data["found"] is False
        assert data["records_count"] == 0
        assert "total_documents_indexed" in data

def test_check_epic_invalid_input():
    with TestClient(app) as client:
        response = client.post("/api/check-epic", json={"epic": "123"})
        assert response.status_code == 400
        assert "Please enter a valid EPIC number" in response.json()["detail"]

def test_check_name_search_valid():
    with TestClient(app) as client:
        response = client.post("/api/check-name", json={"name": "Ramesh"})
        assert response.status_code == 200
        data = response.json()
        assert data["query_type"] == "NAME"
        assert data["found"] is True
        assert data["warning"] is not None
        assert "Names may not uniquely identify a person" in data["warning"]
        assert len(data["records"]) >= 1

def test_check_name_search_invalid():
    with TestClient(app) as client:
        response = client.post("/api/check-name", json={"name": "a"})
        assert response.status_code == 400
        assert "Please enter a valid name" in response.json()["detail"]

def test_admin_start_discovery_single_district():
    with TestClient(app) as client:
        response = client.post(
            "/api/admin/start-discovery",
            json={"district": "Tumakuru", "batch_size": 10},
            auth=("admin", "admin123")
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Tumakuru" in data["message"]

