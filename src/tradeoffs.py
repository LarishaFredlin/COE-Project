"""
SpareSync Decision Trade-Off Analysis Module
Exposes transparent, prototype-level multi-criteria trade-off evaluations
(Cost, Time, Emissions, Reliability) for recommended recovery actions.
"""

from typing import Dict, Any
import pandas as pd

# Multi-criteria scoring dictionary for standard recovery actions
TRADE_OFF_ACTIONS: Dict[str, Dict[str, Any]] = {
    "Manual Physical Recount": {
        "Cost": "Low",
        "Time": "High",
        "Emissions": "Low",
        "Reliability": "High",
        "Cost_Score": 25,
        "Time_Score": 80,
        "Emissions_Score": 10,
        "Reliability_Score": 90,
        "Description": "Deploy warehouse personnel to perform an independent blind recount of shelf bin locations."
    },
    "Investigate Transaction History": {
        "Cost": "Low",
        "Time": "Medium",
        "Emissions": "Low",
        "Reliability": "High",
        "Cost_Score": 20,
        "Time_Score": 45,
        "Emissions_Score": 5,
        "Reliability_Score": 88,
        "Description": "Audit ERP logs, delivery dockets, and duplicate barcode scans to isolate clerical or system discrepancies."
    },
    "Wait for Pending Synchronization": {
        "Cost": "Low",
        "Time": "Low",
        "Emissions": "Low",
        "Reliability": "Very High",
        "Cost_Score": 5,
        "Time_Score": 15,
        "Emissions_Score": 0,
        "Reliability_Score": 98,
        "Description": "Allow edge handheld terminal network queue to flush automatically upon gateway reconnection."
    },
    "Contact Destination Warehouse": {
        "Cost": "Low",
        "Time": "Medium",
        "Emissions": "Low",
        "Reliability": "High",
        "Cost_Score": 15,
        "Time_Score": 40,
        "Emissions_Score": 5,
        "Reliability_Score": 92,
        "Description": "Initiate inter-hub logistics inquiry to confirm receipt and log missing TRANSFER_IN entry."
    },
    "Emergency Replacement Shipment": {
        "Cost": "High",
        "Time": "Low",
        "Emissions": "High",
        "Reliability": "High",
        "Cost_Score": 95,
        "Time_Score": 20,
        "Emissions_Score": 85,
        "Reliability_Score": 95,
        "Description": "Dispatch expedited air freight replacement directly from OEM supplier to prevent repair downtime."
    }
}

# Mapping rule issue types to primary trade-off action keys
ISSUE_TO_TRADEOFF_KEY = {
    "MISSING_TRANSFER": "Contact Destination Warehouse",
    "DUPLICATE_TRANSACTION": "Investigate Transaction History",
    "NETWORK_SYNC_FAILURE": "Wait for Pending Synchronization",
    "TIMESTAMP_ANOMALY": "Investigate Transaction History",
    "UNEXPLAINED_VARIANCE": "Manual Physical Recount",
    "NONE": "Investigate Transaction History"
}


def get_tradeoff_for_action(action_name: str) -> Dict[str, Any]:
    """Retrieves qualitative scores and numeric metrics for a given action."""
    return TRADE_OFF_ACTIONS.get(action_name, TRADE_OFF_ACTIONS["Manual Physical Recount"])


def get_tradeoff_for_issue(issue_type: str) -> Dict[str, Any]:
    """Retrieves the trade-off assessment matching a diagnosed issue type."""
    action_key = ISSUE_TO_TRADEOFF_KEY.get(issue_type, "Manual Physical Recount")
    tradeoff_info = get_tradeoff_for_action(action_key).copy()
    tradeoff_info["Action_Name"] = action_key
    return tradeoff_info


def get_all_tradeoffs_df() -> pd.DataFrame:
    """Returns a structured DataFrame of all action trade-offs for comparative display."""
    rows = []
    for action, meta in TRADE_OFF_ACTIONS.items():
        rows.append({
            "Action": action,
            "Cost": meta["Cost"],
            "Time": meta["Time"],
            "Emissions": meta["Emissions"],
            "Reliability": meta["Reliability"],
            "Description": meta["Description"]
        })
    return pd.DataFrame(rows)
