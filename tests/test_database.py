
import sqlite3

from backend.database import (
    get_database_connection,
    get_db_connection,
    init_database
)

from backend.models import Investigation

def test_database_initialization(tmp_path):
    db_path = tmp_path / "test_sparesync.db"

    init_database(db_path)

    connection = get_database_connection(db_path)

    cursor = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name = 'investigations'
        """
    )

    result = cursor.fetchone()

    connection.close()

    assert result is not None


def test_database_connection_uses_row_factory(tmp_path):
    db_path = tmp_path / "test_sparesync.db"

    connection = get_database_connection(db_path)

    assert connection.row_factory == sqlite3.Row

    connection.close()


def test_database_context_manager(tmp_path):
    db_path = tmp_path / "test_sparesync.db"

    with get_db_connection(db_path) as connection:
        connection.execute(
            """
            CREATE TABLE test_table (
                id INTEGER PRIMARY KEY,
                name TEXT
            )
            """
        )

        connection.execute(
            "INSERT INTO test_table (name) VALUES (?)",
            ("SpareSync",)
        )

    with get_db_connection(db_path) as connection:
        result = connection.execute(
            "SELECT name FROM test_table"
        ).fetchone()

    assert result["name"] == "SpareSync"

def test_investigation_model_from_database_row(tmp_path):
    db_path = tmp_path / "test_sparesync.db"

    init_database(db_path)

    with get_db_connection(db_path) as connection:
        connection.execute(
            """
            INSERT INTO investigations (
                investigation_id,
                part_id,
                part_name,
                location,
                system_stock,
                physical_stock,
                variance,
                root_cause,
                recommended_action,
                confidence,
                status,
                notes,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "INV-001",
                "SP-001",
                "Brake Assembly",
                "Chennai Repair Hub",
                100,
                95,
                5,
                "Missing transfer",
                "Verify transfer records",
                0.85,
                "OPEN",
                "Initial investigation",
                "2026-11-19T10:00:00",
                "2026-11-19T10:00:00"
            )
        )

        row = connection.execute(
            "SELECT * FROM investigations WHERE investigation_id = ?",
            ("INV-001",)
        ).fetchone()

    investigation = Investigation.from_row(row)

    assert investigation.investigation_id == "INV-001"
    assert investigation.part_id == "SP-001"
    assert investigation.variance == 5
    assert investigation.status == "OPEN"


from backend.services.investigation_service import (
    create_investigation,
    get_investigation,
    get_all_investigations,
    update_investigation,
    delete_investigation
)

from backend.schemas import InvestigationCreate, InvestigationUpdate


def test_create_investigation(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sparesync.db"
    init_database(db_path)

    monkeypatch.setattr(
        "backend.services.investigation_service.get_db_connection",
        lambda: get_db_connection(db_path)
    )

    data = InvestigationCreate(
        part_id="SP-001",
        part_name="Brake Assembly",
        location="Chennai Repair Hub",
        system_stock=100,
        physical_stock=95
    )

    result = create_investigation(data)

    assert result.part_id == "SP-001"
    assert result.variance == 5
    assert result.status == "OPEN"


def test_get_investigation(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sparesync.db"
    init_database(db_path)

    monkeypatch.setattr(
        "backend.services.investigation_service.get_db_connection",
        lambda: get_db_connection(db_path)
    )

    data = InvestigationCreate(
        part_id="SP-002",
        location="Bangalore Repair Hub",
        system_stock=50,
        physical_stock=45
    )

    created = create_investigation(data)
    result = get_investigation(created.investigation_id)

    assert result is not None
    assert result.investigation_id == created.investigation_id


def test_update_investigation(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sparesync.db"
    init_database(db_path)

    monkeypatch.setattr(
        "backend.services.investigation_service.get_db_connection",
        lambda: get_db_connection(db_path)
    )

    data = InvestigationCreate(
        part_id="SP-003",
        location="Chennai Repair Hub",
        system_stock=80,
        physical_stock=75
    )

    created = create_investigation(data)

    updated = update_investigation(
        created.investigation_id,
        InvestigationUpdate(
            status="IN_PROGRESS",
            notes="Investigation started"
        )
    )

    assert updated.status == "IN_PROGRESS"
    assert updated.notes == "Investigation started"


def test_delete_investigation(tmp_path, monkeypatch):
    db_path = tmp_path / "test_sparesync.db"
    init_database(db_path)

    monkeypatch.setattr(
        "backend.services.investigation_service.get_db_connection",
        lambda: get_db_connection(db_path)
    )

    data = InvestigationCreate(
        part_id="SP-004",
        location="Chennai Repair Hub",
        system_stock=60,
        physical_stock=60
    )

    created = create_investigation(data)

    result = delete_investigation(created.investigation_id)

    assert result is True
    assert get_investigation(created.investigation_id) is None


