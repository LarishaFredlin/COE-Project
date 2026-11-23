"""
Test Suite: Baseline Variance Detection
Verifies calculation of system stock, physical stock, and variance without root-cause explanations.
"""

import pytest
import pandas as pd
from src.baseline import calculate_system_stock, compute_baseline_audit


def test_calculate_system_stock():
    """Verify system stock calculates credits and debits accurately."""
    sample_tx = pd.DataFrame([
        {"transaction_id": "TX-1", "part_id": "SP-001", "event_type": "RECEIPT", "quantity": 10, "location": "Chennai Repair Hub", "sync_status": "SYNCED"},
        {"transaction_id": "TX-2", "part_id": "SP-001", "event_type": "PICK", "quantity": 2, "location": "Chennai Repair Hub", "sync_status": "SYNCED"},
        {"transaction_id": "TX-3", "part_id": "SP-001", "event_type": "TRANSFER_OUT", "quantity": 3, "location": "Chennai Repair Hub", "sync_status": "SYNCED"},
    ])
    stock = calculate_system_stock(sample_tx, "SP-001", "Chennai Repair Hub")
    assert stock == 5  # 10 - 2 - 3 = 5


def test_baseline_detects_variance_without_explanation():
    """Verify baseline detects variance correctly and does not explain causes."""
    sample_tx = pd.DataFrame([
        {"transaction_id": "TX-1", "part_id": "SP-001", "event_type": "RECEIPT", "quantity": 10, "location": "Chennai Repair Hub", "sync_status": "SYNCED"},
    ])
    sample_counts = pd.DataFrame([
        {"part_id": "SP-001", "part_name": "Turbine Flow Sensor", "location": "Chennai Repair Hub", "physical_stock": 7}
    ])

    results = compute_baseline_audit(sample_tx, sample_counts)
    assert len(results) == 1
    res = results[0]
    assert res["system_stock"] == 10
    assert res["physical_stock"] == 7
    assert res["variance"] == 3
    assert res["has_variance"] is True
    assert res["status"] == "Variance Detected"
    assert "No explanation provided by baseline system" in res["explanation"]


def test_missing_required_column_raises_error():
    """Missing transaction columns should produce a clear validation error."""
    sample_tx = pd.DataFrame([
        {
            "part_id": "SP-001",
            "event_type": "RECEIPT",
            "quantity": 10,
            "location": "Chennai Repair Hub"
        }
    ])

    with pytest.raises(ValueError, match="sync_status"):
        calculate_system_stock(sample_tx, "SP-001")


def test_invalid_quantity_raises_error():
    """Non-numeric quantities should not silently corrupt stock calculations."""
    sample_tx = pd.DataFrame([
        {
            "part_id": "SP-001",
            "event_type": "RECEIPT",
            "quantity": "invalid",
            "location": "Chennai Repair Hub",
            "sync_status": "SYNCED"
        }
    ])

    with pytest.raises(ValueError, match="quantity"):
        calculate_system_stock(sample_tx, "SP-001")


def test_unknown_event_type_raises_error():
    """Unsupported transaction types should not be silently ignored."""
    sample_tx = pd.DataFrame([
        {
            "part_id": "SP-001",
            "event_type": "UNKNOWN_EVENT",
            "quantity": 5,
            "location": "Chennai Repair Hub",
            "sync_status": "SYNCED"
        }
    ])

    with pytest.raises(ValueError, match="event_type"):
        calculate_system_stock(sample_tx, "SP-001")


def test_physical_count_does_not_change_system_stock():
    """Physical count records must not affect ledger stock."""
    sample_tx = pd.DataFrame([
        {
            "part_id": "SP-001",
            "event_type": "RECEIPT",
            "quantity": 10,
            "location": "Chennai Repair Hub",
            "sync_status": "SYNCED"
        },
        {
            "part_id": "SP-001",
            "event_type": "PHYSICAL_COUNT",
            "quantity": 50,
            "location": "Chennai Repair Hub",
            "sync_status": "SYNCED"
        }
    ])

    assert calculate_system_stock(
        sample_tx, "SP-001", "Chennai Repair Hub"
    ) == 10

