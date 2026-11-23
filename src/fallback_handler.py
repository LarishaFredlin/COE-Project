
"""
SpareSync Fallback Handler Module

Implements operational resilience for inventory management during
infrastructure failures:

1. Store-and-Forward: Offline local SQLite queue during network outages.
2. Manual Fallback: Human-in-the-loop transaction logging during
   scanner/sensor failures.
"""

import sqlite3
import uuid
import os
import tempfile

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from src.data_generator import PARTS_CATALOG, TRANSACTIONS_FILE, DATA_DIR


DB_PATH = DATA_DIR / "offline_queue.db"


class FallbackHandler:
    """
    Manages local edge persistence (SQLite) for store-and-forward
    queuing and manual fallback transactions when network/scanners fail.
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
        transactions_file: Path = TRANSACTIONS_FILE
    ):
        self.db_path = db_path
        self.transactions_file = transactions_file
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Creates a connection to the local SQLite database."""
        return sqlite3.connect(self.db_path)

    def init_db(self) -> None:
        """Initializes the local SQLite store-and-forward table schema."""

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS local_offline_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id TEXT UNIQUE NOT NULL,
                    part_id TEXT NOT NULL,
                    part_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    location TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    transfer_id TEXT DEFAULT '',
                    status TEXT NOT NULL,
                    sync_status TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    verification_required INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)

            conn.commit()

    def record_offline_transaction(
        self,
        part_id: str,
        event_type: str,
        quantity: int,
        location: str,
        timestamp: Optional[str] = None,
        reason: str = "Network connectivity unavailable"
    ) -> Dict[str, Any]:
        """
        Records a transaction locally on the edge terminal
        when the network is offline.

        Assigns sync_status = PENDING_SYNC and generates
        a unique transaction_id.
        """

        now = datetime.now()
        ts_str = timestamp or now.strftime("%Y-%m-%d %H:%M:%S")

        unique_suffix = uuid.uuid4().hex[:6].upper()
        tx_id = (
            f"TX-OFFLINE-{now.strftime('%Y%m%d%H%M%S')}"
            f"-{unique_suffix}"
        )

        part_name = PARTS_CATALOG.get(part_id, "Spare Component")

        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO local_offline_transactions (
                    transaction_id,
                    part_id,
                    part_name,
                    event_type,
                    quantity,
                    location,
                    timestamp,
                    transfer_id,
                    status,
                    sync_status,
                    reason,
                    verification_required,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx_id,
                part_id,
                part_name,
                event_type.upper().strip(),
                int(quantity),
                location,
                ts_str,
                "",
                "COMPLETED",
                "PENDING_SYNC",
                reason,
                0,
                ts_str
            ))

            conn.commit()

        return {
            "transaction_id": tx_id,
            "part_id": part_id,
            "part_name": part_name,
            "event_type": event_type.upper().strip(),
            "quantity": int(quantity),
            "location": location,
            "timestamp": ts_str,
            "transfer_id": "",
            "status": "COMPLETED",
            "sync_status": "PENDING_SYNC",
            "reason": reason,
            "verification_required": False
        }

    def get_pending_transactions(self) -> pd.DataFrame:
        """
        Returns all transactions waiting for synchronization.
        """

        with self._get_connection() as conn:
            df = pd.read_sql_query(
                """
                SELECT *
                FROM local_offline_transactions
                WHERE sync_status = 'PENDING_SYNC'
                ORDER BY id ASC
                """,
                conn
            )

        return df

    def sync_pending_transactions(self) -> Dict[str, Any]:
        """
        Synchronizes pending offline transactions without
        creating duplicates.

        Transactions already present in the central CSV ledger
        are marked as synchronized without being appended again.
        """

        pending_df = self.get_pending_transactions()
        pending_count = len(pending_df)

        if pending_count == 0:
            return {
                "pending_before": 0,
                "successfully_synchronized": 0,
                "remaining_pending": 0,
                "synced_transaction_ids": [],
                "message": (
                    "No pending offline transactions waiting "
                    "for synchronization."
                )
            }

        # Load the central transaction ledger.
        if self.transactions_file.exists():
            main_df = pd.read_csv(self.transactions_file)
        else:
            main_df = pd.DataFrame()

        if (
            not main_df.empty
            and "transaction_id" not in main_df.columns
        ):
            raise ValueError(
                "Central ledger is missing transaction_id column."
            )

        # Identify transactions already written to the CSV.
        existing_ids = set()

        if "transaction_id" in main_df.columns:
            existing_ids = set(
                main_df["transaction_id"]
                .dropna()
                .astype(str)
            )

        new_rows = []
        synced_ids = []
        duplicates_skipped = 0

        for _, row in pending_df.iterrows():

            tx_id = str(row["transaction_id"])
            synced_ids.append(tx_id)

            if tx_id in existing_ids:
                duplicates_skipped += 1
                continue

            new_rows.append({
                "transaction_id": tx_id,
                "part_id": row["part_id"],
                "part_name": row["part_name"],
                "event_type": row["event_type"],
                "quantity": int(row["quantity"]),
                "location": row["location"],
                "timestamp": row["timestamp"],
                "transfer_id": row.get("transfer_id", ""),
                "sync_status": "SYNCED"
            })

        # Append only new transactions.
        if new_rows:

            append_df = pd.DataFrame(new_rows)

            if main_df.empty and len(main_df.columns) == 0:
                combined_df = append_df

            else:
                # Preserve additional columns in the original ledger.
                for column in main_df.columns:
                    if column not in append_df.columns:
                        append_df[column] = None

                append_df = append_df.reindex(
                    columns=main_df.columns
                )

                combined_df = pd.concat(
                    [main_df, append_df],
                    ignore_index=True
                )

            # Write to a temporary file before replacing the original.
            self.transactions_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            temp_path = None

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".tmp",
                    prefix="transactions_",
                    dir=self.transactions_file.parent,
                    delete=False,
                    newline=""
                ) as temp_file:

                    temp_path = temp_file.name
                    combined_df.to_csv(temp_file, index=False)

                os.replace(temp_path, self.transactions_file)
                temp_path = None

            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

        # Mark processed transaction IDs as synchronized.
        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.executemany(
                """
                UPDATE local_offline_transactions
                SET sync_status = 'SYNCED'
                WHERE transaction_id = ?
                  AND sync_status = 'PENDING_SYNC'
                """,
                [(tx_id,) for tx_id in synced_ids]
            )

            conn.commit()

        return {
            "pending_before": pending_count,
            "successfully_synchronized": pending_count,
            "remaining_pending": 0,
            "synced_transaction_ids": synced_ids,
            "duplicates_skipped": duplicates_skipped,
            "message": (
                f"Successfully synchronized {pending_count} offline "
                f"transaction(s). {duplicates_skipped} duplicate(s) skipped."
            )
        }

    def simulate_network_restore(self) -> Dict[str, Any]:
        """
        Simulates network restoration and synchronizes
        all pending offline transactions.
        """

        return self.sync_pending_transactions()

    def record_manual_fallback(
        self,
        part_id: str,
        event_type: str,
        quantity: int,
        location: str,
        reason: str,
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Supports manual data entry when barcode scanners,
        sensors, or automated terminals fail.

        Assigns status = MANUAL_PENDING_VERIFICATION,
        verification_required = True, and saves the transaction
        into both local fallback storage and the central CSV ledger.
        """

        now = datetime.now()
        ts_str = timestamp or now.strftime("%Y-%m-%d %H:%M:%S")

        unique_suffix = uuid.uuid4().hex[:6].upper()
        tx_id = (
            f"TX-MANUAL-{now.strftime('%Y%m%d%H%M%S')}"
            f"-{unique_suffix}"
        )

        part_name = PARTS_CATALOG.get(part_id, "Spare Component")

        # 1. Store in local SQLite.
        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO local_offline_transactions (
                    transaction_id,
                    part_id,
                    part_name,
                    event_type,
                    quantity,
                    location,
                    timestamp,
                    transfer_id,
                    status,
                    sync_status,
                    reason,
                    verification_required,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tx_id,
                part_id,
                part_name,
                event_type.upper().strip(),
                int(quantity),
                location,
                ts_str,
                "",
                "MANUAL_PENDING_VERIFICATION",
                "MANUAL_PENDING_VERIFICATION",
                reason,
                1,
                ts_str
            ))

            conn.commit()

        # 2. Append to the main transaction dataset.
        if self.transactions_file.exists():
            main_df = pd.read_csv(self.transactions_file)
        else:
            main_df = pd.DataFrame()

        manual_entry = pd.DataFrame([{
            "transaction_id": tx_id,
            "part_id": part_id,
            "part_name": part_name,
            "event_type": event_type.upper().strip(),
            "quantity": int(quantity),
            "location": location,
            "timestamp": ts_str,
            "transfer_id": "",
            "sync_status": "MANUAL_PENDING_VERIFICATION"
        }])

        combined_df = pd.concat(
            [main_df, manual_entry],
            ignore_index=True
        )

        self.transactions_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        combined_df.to_csv(
            self.transactions_file,
            index=False
        )

        return {
            "transaction_id": tx_id,
            "part_id": part_id,
            "part_name": part_name,
            "event_type": event_type.upper().strip(),
            "quantity": int(quantity),
            "location": location,
            "timestamp": ts_str,
            "transfer_id": "",
            "status": "MANUAL_PENDING_VERIFICATION",
            "sync_status": "MANUAL_PENDING_VERIFICATION",
            "reason": reason,
            "verification_required": True
        }

    def clear_database(self) -> None:
        """Resets the local fallback SQLite database."""

        with self._get_connection() as conn:

            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM local_offline_transactions"
            )

            conn.commit()
