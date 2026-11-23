
"""
SpareSync Database Configuration

Handles SQLite database connections and initialisation.
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database location
DATABASE_PATH = BASE_DIR / "data" / "sparesync.db"


def get_database_connection(
    db_path: Path = DATABASE_PATH
) -> sqlite3.Connection:
    """
    Create and return a SQLite database connection.
    """

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(
        str(db_path),
        timeout=10
    )

    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    return connection


@contextmanager
def get_db_connection(
    db_path: Path = DATABASE_PATH
) -> Generator[sqlite3.Connection, None, None]:
    """
    Provide a database connection with automatic commit,
    rollback and closing.
    """

    connection = get_database_connection(db_path)

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def init_database(
    db_path: Path = DATABASE_PATH
) -> None:
    """
    Initialise the SpareSync database and create tables.
    """

    with get_db_connection(db_path) as connection:

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS investigations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                investigation_id TEXT UNIQUE NOT NULL,

                part_id TEXT NOT NULL,

                part_name TEXT,

                location TEXT NOT NULL,

                system_stock INTEGER NOT NULL,

                physical_stock INTEGER NOT NULL,

                variance INTEGER NOT NULL,

                root_cause TEXT,

                recommended_action TEXT,

                confidence REAL,

                status TEXT NOT NULL DEFAULT 'OPEN',

                notes TEXT,

                created_at TEXT NOT NULL,

                updated_at TEXT NOT NULL
            )
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_investigations_part_id
            ON investigations(part_id)
            """
        )

        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_investigations_status
            ON investigations(status)
            """
        )
