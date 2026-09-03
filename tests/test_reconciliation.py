"""
Test Suite: Rule-Based Reconciliation Engine
Verifies detection of missing transfers, duplicates, network sync failures, and timestamp anomalies.
"""

import pytest
import pandas as pd
from src.reconciliation_engine import ReconciliationEngine


def test_missing_transfer_detection():
    """Verify engine identifies unconfirmed TRANSFER_OUT with matching evidence."""
    sample_tx = pd.DataFrame([
        {
            "transaction_id": "TX-101",
            "part_id": "SP-001",
            "part_name": "Turbine Flow Sensor",
            "event_type": "TRANSFER_OUT",
            "quantity": 3,
            "location": "Chennai Repair Hub",
            "timestamp": "2026-08-01 10:00:00",
            "transfer_id": "TRF-TEST-99",
            "sync_status": "SYNCED"
        }
    ])
    sample_counts = pd.DataFrame([
        {"part_id": "SP-001", "part_name": "Turbine Flow Sensor", "location": "Bangalore Repair Hub", "physical_stock": 3}
    ])

    engine = ReconciliationEngine(sample_tx, sample_counts)
    missing = engine.detect_missing_transfers("SP-001")
    
    assert len(missing) == 1
    assert missing[0]["issue_type"] == "MISSING_TRANSFER"
    assert missing[0]["transfer_id"] == "TRF-TEST-99"
    assert "92%" in missing[0]["confidence"]
    assert len(missing[0]["evidence"]) > 0


def test_duplicate_transaction_detection():
    """Verify engine detects duplicate receipts logged within a 30-minute window."""
    sample_tx = pd.DataFrame([
        {
            "transaction_id": "TX-201",
            "part_id": "SP-002",
            "part_name": "High-Voltage Inverter Module",
            "event_type": "RECEIPT",
            "quantity": 4,
            "location": "Mumbai Repair Hub",
            "timestamp": "2026-08-01 10:00:00",
            "transfer_id": "",
            "sync_status": "SYNCED"
        },
        {
            "transaction_id": "TX-202",
            "part_id": "SP-002",
            "part_name": "High-Voltage Inverter Module",
            "event_type": "RECEIPT",
            "quantity": 4,
            "location": "Mumbai Repair Hub",
            "timestamp": "2026-08-01 10:04:00",
            "transfer_id": "",
            "sync_status": "SYNCED"
        }
    ])
    sample_counts = pd.DataFrame([
        {"part_id": "SP-002", "part_name": "High-Voltage Inverter Module", "location": "Mumbai Repair Hub", "physical_stock": 4}
    ])

    engine = ReconciliationEngine(sample_tx, sample_counts)
    dups = engine.detect_duplicate_transactions("SP-002", "Mumbai Repair Hub")
    
    assert len(dups) == 1
    assert dups[0]["issue_type"] == "DUPLICATE_TRANSACTION"
    assert dups[0]["tx_1"] == "TX-201"
    assert dups[0]["tx_2"] == "TX-202"
    assert dups[0]["time_diff_mins"] == 4.0


def test_network_sync_failure_detection():
    """Verify engine detects PENDING_SYNC status resulting from network failure."""
    sample_tx = pd.DataFrame([
        {
            "transaction_id": "TX-301",
            "part_id": "SP-003",
            "part_name": "Hydraulic Servo Valve",
            "event_type": "PICK",
            "quantity": 2,
            "location": "Chennai Repair Hub",
            "timestamp": "2026-08-01 12:00:00",
            "transfer_id": "",
            "sync_status": "PENDING_SYNC"
        }
    ])
    sample_counts = pd.DataFrame([
        {"part_id": "SP-003", "part_name": "Hydraulic Servo Valve", "location": "Chennai Repair Hub", "physical_stock": 8}
    ])

    engine = ReconciliationEngine(sample_tx, sample_counts)
    sync_fails = engine.detect_network_sync_failures("SP-003", "Chennai Repair Hub")

    assert len(sync_fails) == 1
    assert sync_fails[0]["issue_type"] == "NETWORK_SYNC_FAILURE"
    assert sync_fails[0]["tx_id"] == "TX-301"


def test_timestamp_anomaly_detection():
    """Verify engine flags TRANSFER_IN occurring prior to TRANSFER_OUT."""
    sample_tx = pd.DataFrame([
        {
            "transaction_id": "TX-401",
            "part_id": "SP-004",
            "part_name": "Fiber Optic Gyroscope",
            "event_type": "TRANSFER_IN",
            "quantity": 2,
            "location": "Bangalore Repair Hub",
            "timestamp": "2026-08-01 09:00:00",
            "transfer_id": "TRF-808",
            "sync_status": "SYNCED"
        },
        {
            "transaction_id": "TX-402",
            "part_id": "SP-004",
            "part_name": "Fiber Optic Gyroscope",
            "event_type": "TRANSFER_OUT",
            "quantity": 2,
            "location": "Mumbai Repair Hub",
            "timestamp": "2026-08-01 11:00:00",
            "transfer_id": "TRF-808",
            "sync_status": "SYNCED"
        }
    ])
    sample_counts = pd.DataFrame([
        {"part_id": "SP-004", "part_name": "Fiber Optic Gyroscope", "location": "Bangalore Repair Hub", "physical_stock": 5}
    ])

    engine = ReconciliationEngine(sample_tx, sample_counts)
    anoms = engine.detect_timestamp_anomalies("SP-004")

    assert len(anoms) == 1
    assert anoms[0]["issue_type"] == "TIMESTAMP_ANOMALY"
    assert anoms[0]["transfer_id"] == "TRF-808"


def test_reconcile_item_end_to_end():
    """Verify complete reconcile_item flow for an item with variance."""
    sample_tx = pd.DataFrame([
        {"transaction_id": "TX-1", "part_id": "SP-001", "part_name": "Turbine Flow Sensor", "event_type": "RECEIPT", "quantity": 10, "location": "Chennai Repair Hub", "timestamp": "2026-08-01 08:00:00", "transfer_id": "", "sync_status": "SYNCED"},
        {"transaction_id": "TX-2", "part_id": "SP-001", "part_name": "Turbine Flow Sensor", "event_type": "TRANSFER_OUT", "quantity": 3, "location": "Chennai Repair Hub", "timestamp": "2026-08-01 10:00:00", "transfer_id": "TRF-FAIL-901", "sync_status": "SYNCED"}
    ])
    sample_counts = pd.DataFrame([
        {"part_id": "SP-001", "part_name": "Turbine Flow Sensor", "location": "Chennai Repair Hub", "physical_stock": 7}
    ])

    engine = ReconciliationEngine(sample_tx, sample_counts)
    rec = engine.reconcile_item("SP-001", "Chennai Repair Hub")

    assert rec["part_id"] == "SP-001"
    assert rec["system_stock"] == 7
    assert rec["physical_stock"] == 7
    assert rec["variance"] == 0
