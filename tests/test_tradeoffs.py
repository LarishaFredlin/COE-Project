"""
Test Suite: Decision Trade-Off Analysis Module
Verifies:
1. Multi-criteria trade-off scoring for all standard recovery actions
2. Retrieval of qualitative and numeric metrics (Cost, Time, Emissions, Reliability)
3. Correct issue-to-action trade-off mapping
"""

import pytest
from src.tradeoffs import (
    TRADE_OFF_ACTIONS,
    get_tradeoff_for_action,
    get_tradeoff_for_issue,
    get_all_tradeoffs_df
)


def test_standard_actions_exist():
    """Verify all 5 required actions exist with Cost, Time, Emissions, and Reliability."""
    required_actions = [
        "Manual Physical Recount",
        "Investigate Transaction History",
        "Wait for Pending Synchronization",
        "Contact Destination Warehouse",
        "Emergency Replacement Shipment"
    ]

    for action in required_actions:
        assert action in TRADE_OFF_ACTIONS
        data = TRADE_OFF_ACTIONS[action]
        assert "Cost" in data
        assert "Time" in data
        assert "Emissions" in data
        assert "Reliability" in data


def test_tradeoff_scores_structure():
    """Verify numeric scores and descriptions are properly structured."""
    recount = get_tradeoff_for_action("Manual Physical Recount")
    assert recount["Cost"] == "Low"
    assert recount["Time"] == "High"
    assert recount["Emissions"] == "Low"
    assert recount["Reliability"] == "High"
    assert 0 <= recount["Cost_Score"] <= 100
    assert 0 <= recount["Reliability_Score"] <= 100

    emergency = get_tradeoff_for_action("Emergency Replacement Shipment")
    assert emergency["Cost"] == "High"
    assert emergency["Time"] == "Low"
    assert emergency["Emissions"] == "High"
    assert emergency["Reliability"] == "High"


def test_tradeoff_mapping_for_issues():
    """Verify issue types map to the appropriate recovery action trade-offs."""
    trf_tradeoff = get_tradeoff_for_issue("MISSING_TRANSFER")
    assert trf_tradeoff["Action_Name"] == "Contact Destination Warehouse"

    sync_tradeoff = get_tradeoff_for_issue("NETWORK_SYNC_FAILURE")
    assert sync_tradeoff["Action_Name"] == "Wait for Pending Synchronization"

    dup_tradeoff = get_tradeoff_for_issue("DUPLICATE_TRANSACTION")
    assert dup_tradeoff["Action_Name"] == "Investigate Transaction History"


def test_all_tradeoffs_dataframe():
    """Verify get_all_tradeoffs_df returns a valid non-empty DataFrame."""
    df = get_all_tradeoffs_df()
    assert len(df) == 5
    assert list(df.columns) == ["Action", "Cost", "Time", "Emissions", "Reliability", "Description"]
