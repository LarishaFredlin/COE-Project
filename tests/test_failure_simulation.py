"""
Test Suite: Failure Simulation Module
Verifies that all 4 failure scenarios simulate realistic operational breakdown states
and that the reconciliation engine diagnoses each scenario correctly.
"""

import pytest
from src.failure_simulator import (
    simulate_missing_transfer,
    simulate_duplicate_receipt,
    simulate_network_failure,
    simulate_timestamp_anomaly
)


def test_simulate_missing_transfer():
    """Verify missing transfer simulation reproduces unconfirmed transfer diagnosis."""
    res = simulate_missing_transfer("SP-001", "Chennai Repair Hub", "Bangalore Repair Hub", qty=3)
    
    assert res["scenario_title"] == "Missing Transfer Confirmation"
    assert res["reconciliation"]["issue_type"] == "MISSING_TRANSFER"
    assert "Unconfirmed inter-hub transfer" in res["reconciliation"]["likely_cause"]
    assert "92%" in res["reconciliation"]["confidence"]
    assert len(res["reconciliation"]["evidence"]) > 0


def test_simulate_duplicate_receipt():
    """Verify duplicate receipt simulation catches redundant transactions."""
    res = simulate_duplicate_receipt("SP-002", "Mumbai Repair Hub", qty=4, time_diff_mins=4)

    assert res["scenario_title"] == "Duplicate Receipt Transaction"
    assert res["reconciliation"]["issue_type"] == "DUPLICATE_TRANSACTION"
    assert "Duplicate RECEIPT transaction" in res["reconciliation"]["likely_cause"]
    assert "88%" in res["reconciliation"]["confidence"]


def test_simulate_network_failure():
    """Verify network failure simulation detects PENDING_SYNC status."""
    res = simulate_network_failure("SP-003", "Chennai Repair Hub", qty=2)

    assert res["scenario_title"] == "Network Synchronization Failure"
    assert res["reconciliation"]["issue_type"] == "NETWORK_SYNC_FAILURE"
    assert "PENDING_SYNC" in res["reconciliation"]["evidence"][0]
    assert "95%" in res["reconciliation"]["confidence"]


def test_simulate_timestamp_anomaly():
    """Verify timestamp anomaly simulation detects out-of-order sequence."""
    res = simulate_timestamp_anomaly("SP-004", "Mumbai Repair Hub", "Bangalore Repair Hub", qty=2)

    assert res["scenario_title"] == "Timestamp Sequence Anomaly"
    assert res["reconciliation"]["issue_type"] == "TIMESTAMP_ANOMALY"
    assert "Out-of-sequence chronological timestamps" in res["reconciliation"]["likely_cause"]
