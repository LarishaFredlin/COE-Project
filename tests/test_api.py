
import pytest
from pydantic import ValidationError


import pytest
from fastapi.testclient import TestClient

from backend import main
from backend.database import get_db_connection, init_database
import backend.services.investigation_service as service


from backend.schemas import (
    InvestigationCreate,
    InvestigationUpdate
)


@pytest.fixture
def api_client(tmp_path, monkeypatch):
    db_path = tmp_path / "api_test.db"

    # Initialise a separate temporary database for each test
    monkeypatch.setattr(
        main,
        "init_database",
        lambda: init_database(db_path)
    )

    # Make the service use the temporary database
    monkeypatch.setattr(
        service,
        "get_db_connection",
        lambda: get_db_connection(db_path)
    )

    with TestClient(main.app) as client:
        yield client


def test_valid_investigation_creation():
    investigation = InvestigationCreate(
        part_id="SP-001",
        part_name="Brake Assembly",
        location="Chennai Repair Hub",
        system_stock=100,
        physical_stock=95,
        confidence=0.85
    )

    assert investigation.variance == 5


def test_negative_stock_is_rejected():
    with pytest.raises(ValidationError):
        InvestigationCreate(
            part_id="SP-001",
            location="Chennai Repair Hub",
            system_stock=-10,
            physical_stock=95
        )


def test_invalid_confidence_is_rejected():
    with pytest.raises(ValidationError):
        InvestigationCreate(
            part_id="SP-001",
            location="Chennai Repair Hub",
            system_stock=100,
            physical_stock=95,
            confidence=1.5
        )


def test_invalid_status_is_rejected():
    with pytest.raises(ValidationError):
        InvestigationUpdate(status="PENDING")


def test_create_investigation_api(api_client):
    response = api_client.post(
        "/investigations/",
        json={
            "part_id": "SP-001",
            "part_name": "Brake Assembly",
            "location": "Chennai Repair Hub",
            "system_stock": 100,
            "physical_stock": 95,
            "root_cause": "Missing transfer",
            "recommended_action": "Verify transfer records",
            "confidence": 0.85,
            "notes": "API test"
        }
    )

    assert response.status_code == 201
    assert response.json()["variance"] == 5
    assert response.json()["status"] == "OPEN"


def test_list_investigations_api(api_client):
    api_client.post(
        "/investigations/",
        json={
            "part_id": "SP-002",
            "location": "Coimbatore",
            "system_stock": 50,
            "physical_stock": 45
        }
    )

    response = api_client.get("/investigations/")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_investigation_api(api_client):
    created = api_client.post(
        "/investigations/",
        json={
            "part_id": "SP-003",
            "location": "Chennai",
            "system_stock": 80,
            "physical_stock": 75
        }
    )

    investigation_id = created.json()["investigation_id"]

    response = api_client.get(
        f"/investigations/{investigation_id}"
    )

    assert response.status_code == 200
    assert response.json()["part_id"] == "SP-003"


def test_update_investigation_api(api_client):
    created = api_client.post(
        "/investigations/",
        json={
            "part_id": "SP-004",
            "location": "Coimbatore",
            "system_stock": 60,
            "physical_stock": 55
        }
    )

    investigation_id = created.json()["investigation_id"]

    response = api_client.put(
        f"/investigations/{investigation_id}",
        json={
            "status": "IN_PROGRESS",
            "notes": "Verification started"
        }
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"
    assert response.json()["notes"] == "Verification started"


def test_delete_investigation_api(api_client):
    created = api_client.post(
        "/investigations/",
        json={
            "part_id": "SP-005",
            "location": "Chennai",
            "system_stock": 40,
            "physical_stock": 35
        }
    )

    investigation_id = created.json()["investigation_id"]

    response = api_client.delete(
        f"/investigations/{investigation_id}"
    )

    assert response.status_code == 200

    get_response = api_client.get(
        f"/investigations/{investigation_id}"
    )

    assert get_response.status_code == 404


def test_invalid_investigation_returns_404(api_client):
    response = api_client.get(
        "/investigations/INV-DOES-NOT-EXIST"
    )

    assert response.status_code == 404

