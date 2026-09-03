"""
Test Suite: Operational Resilience & Fallback Handler
Verifies:
1. Offline transaction creation and store-and-forward queueing
2. Pending transaction retrieval
3. Successful synchronization upon network restoration
4. Manual fallback transaction logging during scanner/sensor failure
"""

import pytest
import pandas as pd
from pathlib import Path

from src.fallback_handler import FallbackHandler


@pytest.fixture
def temp_fallback_handler(tmp_path):
    """Provides an isolated FallbackHandler with temporary SQLite db and CSV dataset."""
    db_file = tmp_path / "test_offline.db"
    tx_csv = tmp_path / "test_transactions.csv"
    
    # Initialize empty main transactions dataset
    initial_tx = pd.DataFrame([
        {
            "transaction_id": "TX-INIT-001",
            "part_id": "SP-001",
            "part_name": "Turbine Flow Sensor",
            "event_type": "RECEIPT",
            "quantity": 10,
            "location": "Chennai Repair Hub",
            "timestamp": "2026-08-01 08:00:00",
            "transfer_id": "",
            "sync_status": "SYNCED"
        }
    ])
    initial_tx.to_csv(tx_csv, index=False)

    handler = FallbackHandler(db_path=db_file, transactions_file=tx_csv)
    return handler


def test_offline_transaction_creation(temp_fallback_handler):
    """Verify recording an offline transaction saves it with PENDING_SYNC status and generated ID."""
    handler = temp_fallback_handler

    tx = handler.record_offline_transaction(
        part_id="SP-003",
        event_type="PICK",
        quantity=2,
        location="Delhi Repair Hub",
        reason="Network gateway unreachable"
    )

    assert tx["part_id"] == "SP-003"
    assert tx["event_type"] == "PICK"
    assert tx["quantity"] == 2
    assert tx["sync_status"] == "PENDING_SYNC"
    assert "TX-OFFLINE-" in tx["transaction_id"]
    assert tx["reason"] == "Network gateway unreachable"


def test_pending_transaction_retrieval(temp_fallback_handler):
    """Verify get_pending_transactions returns all un-synced transactions."""
    handler = temp_fallback_handler

    # Initially empty
    pending_before = handler.get_pending_transactions()
    assert len(pending_before) == 0

    # Add 2 offline transactions
    handler.record_offline_transaction("SP-001", "PICK", 1, "Chennai Repair Hub", reason="Router outage")
    handler.record_offline_transaction("SP-002", "RECEIPT", 3, "Mumbai Repair Hub", reason="Switch failure")

    pending_after = handler.get_pending_transactions()
    assert len(pending_after) == 2
    assert set(pending_after["part_id"].tolist()) == {"SP-001", "SP-002"}
    assert all(pending_after["sync_status"] == "PENDING_SYNC")


def test_successful_synchronization_after_network_restoration(temp_fallback_handler):
    """Verify restore/sync flushes queue and appends transactions to central CSV with SYNCED status."""
    handler = temp_fallback_handler

    # Add 2 offline transactions
    handler.record_offline_transaction("SP-001", "PICK", 2, "Chennai Repair Hub", reason="Offline Pick")
    handler.record_offline_transaction("SP-004", "TRANSFER_OUT", 1, "Bangalore Repair Hub", reason="Offline Transfer")

    # Perform network restore simulation
    summary = handler.simulate_network_restore()

    assert summary["pending_before"] == 2
    assert summary["successfully_synchronized"] == 2
    assert summary["remaining_pending"] == 0
    assert len(summary["synced_transaction_ids"]) == 2

    # Verify pending queue is now empty
    remaining_pending = handler.get_pending_transactions()
    assert len(remaining_pending) == 0

    # Verify central CSV has the newly synced transactions
    main_df = pd.read_csv(handler.transactions_file)
    assert len(main_df) == 3  # 1 initial + 2 synced
    assert "TX-OFFLINE-" in main_df.iloc[-1]["transaction_id"]
    assert main_df.iloc[-1]["sync_status"] == "SYNCED"


def test_manual_fallback_transaction_creation(temp_fallback_handler):
    """Verify manual entry saves with MANUAL_PENDING_VERIFICATION status and verification_required=True."""
    handler = temp_fallback_handler

    manual_tx = handler.record_manual_fallback(
        part_id="SP-005",
        event_type="RECEIPT",
        quantity=5,
        location="Chennai Repair Hub",
        reason="Barcode scanner laser head failed during inspection"
    )

    assert manual_tx["part_id"] == "SP-005"
    assert manual_tx["status"] == "MANUAL_PENDING_VERIFICATION"
    assert manual_tx["sync_status"] == "MANUAL_PENDING_VERIFICATION"
    assert manual_tx["verification_required"] is True
    assert "TX-MANUAL-" in manual_tx["transaction_id"]

    # Verify it is recorded in the central CSV for the transaction explorer
    main_df = pd.read_csv(handler.transactions_file)
    assert len(main_df) == 2  # 1 initial + 1 manual
    assert main_df.iloc[-1]["sync_status"] == "MANUAL_PENDING_VERIFICATION"
