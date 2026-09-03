"""
SpareSync Failure Simulation Module
Constructs and evaluates controlled inventory failure scenarios to demonstrate
how the rule-based reconciliation engine detects, diagnoses, and recovers from operational anomalies.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple
import pandas as pd

from src.data_generator import PARTS_CATALOG
from src.reconciliation_engine import ReconciliationEngine


def simulate_missing_transfer(
    part_id: str = "SP-001",
    source_loc: str = "Chennai Repair Hub",
    dest_loc: str = "Bangalore Repair Hub",
    qty: int = 3
) -> Dict[str, Any]:
    """
    Scenario 1: Missing Transfer Confirmation
    Simulates TRANSFER_OUT dispatched from source but unconfirmed at destination.
    """
    part_name = PARTS_CATALOG.get(part_id, "Turbine Flow Sensor")
    trf_id = "TRF-SIM-101"
    t_base = datetime(2026, 8, 15, 9, 0, 0)
    
    # 1. Normal State Transactions
    tx_normal = [
        {
            "transaction_id": "TX-SIM-001",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "RECEIPT",
            "quantity": 10,
            "location": source_loc,
            "timestamp": t_base.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": "",
            "sync_status": "SYNCED"
        }
    ]

    # 2. Failure Event: Outbound transfer recorded, inbound omitted
    tx_failure = list(tx_normal)
    t_out = t_base + timedelta(hours=2)
    tx_failure.append({
        "transaction_id": "TX-SIM-002",
        "part_id": part_id,
        "part_name": part_name,
        "event_type": "TRANSFER_OUT",
        "quantity": qty,
        "location": source_loc,
        "timestamp": t_out.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": trf_id,
        "sync_status": "SYNCED"
    })

    # Destination physical count: Parts physically arrived at destination hub
    df_counts = pd.DataFrame([
        {"part_id": part_id, "part_name": part_name, "location": dest_loc, "physical_stock": qty},
        {"part_id": part_id, "part_name": part_name, "location": source_loc, "physical_stock": 10 - qty}
    ])

    df_tx = pd.DataFrame(tx_failure)
    engine = ReconciliationEngine(df_tx, df_counts)
    rec_result = engine.reconcile_item(part_id, dest_loc)

    return {
        "scenario_title": "Missing Transfer Confirmation",
        "part_id": part_id,
        "part_name": part_name,
        "source_loc": source_loc,
        "dest_loc": dest_loc,
        "transfer_id": trf_id,
        "quantity": qty,
        "normal_state": {
            "description": f"Chennai Hub received 10 units of {part_name}. Bangalore Hub held 0 units.",
            "source_system_stock": 10,
            "dest_system_stock": 0,
        },
        "failure_state": {
            "description": f"Dispatched {qty} units with transfer ID '{trf_id}'. Physical shipment arrived at Bangalore, but destination TRANSFER_IN was never recorded in system ledger.",
            "source_system_stock": 10 - qty,
            "dest_system_stock": 0,
            "dest_physical_stock": qty,
            "dest_variance": 0 - qty, # System is deficient by 3
        },
        "transactions_table": df_tx,
        "reconciliation": rec_result
    }


def simulate_duplicate_receipt(
    part_id: str = "SP-002",
    loc: str = "Mumbai Repair Hub",
    qty: int = 4,
    time_diff_mins: int = 4
) -> Dict[str, Any]:
    """
    Scenario 2: Duplicate Receipt
    Simulates a technician double-scanning a delivery batch within a short time window.
    """
    part_name = PARTS_CATALOG.get(part_id, "High-Voltage Inverter Module")
    t_base = datetime(2026, 8, 15, 10, 0, 0)
    t_dup = t_base + timedelta(minutes=time_diff_mins)

    # Transactions
    tx_list = [
        {
            "transaction_id": "TX-SIM-DUP1",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "RECEIPT",
            "quantity": qty,
            "location": loc,
            "timestamp": t_base.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": "",
            "sync_status": "SYNCED"
        },
        {
            "transaction_id": "TX-SIM-DUP2",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "RECEIPT",
            "quantity": qty,
            "location": loc,
            "timestamp": t_dup.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": "",
            "sync_status": "SYNCED"
        }
    ]

    # Only 1 batch of `qty` actually physically arrived
    df_counts = pd.DataFrame([
        {"part_id": part_id, "part_name": part_name, "location": loc, "physical_stock": qty}
    ])
    df_tx = pd.DataFrame(tx_list)

    engine = ReconciliationEngine(df_tx, df_counts)
    rec_result = engine.reconcile_item(part_id, loc)

    return {
        "scenario_title": "Duplicate Receipt Transaction",
        "part_id": part_id,
        "part_name": part_name,
        "location": loc,
        "quantity": qty,
        "time_diff_mins": time_diff_mins,
        "normal_state": {
            "description": f"Delivery docket received for 1 batch of {qty} units of {part_name}.",
            "expected_stock": qty
        },
        "failure_state": {
            "description": f"Operator scanned barcode twice within {time_diff_mins} minutes, creating redundant transaction TX-SIM-DUP2.",
            "system_stock": qty * 2,
            "physical_stock": qty,
            "variance": qty # System has +4 artificial surplus
        },
        "transactions_table": df_tx,
        "reconciliation": rec_result
    }


def simulate_network_failure(
    part_id: str = "SP-003",
    loc: str = "Chennai Repair Hub",
    qty: int = 2
) -> Dict[str, Any]:
    """
    Scenario 3: Network Synchronization Failure
    Simulates offline technician consumption stored locally with PENDING_SYNC.
    """
    part_name = PARTS_CATALOG.get(part_id, "Hydraulic Servo Valve")
    t_base = datetime(2026, 8, 15, 8, 0, 0)
    t_pick = t_base + timedelta(hours=4)

    tx_list = [
        {
            "transaction_id": "TX-SIM-INIT",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "RECEIPT",
            "quantity": 10,
            "location": loc,
            "timestamp": t_base.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": "",
            "sync_status": "SYNCED"
        },
        {
            "transaction_id": "TX-SIM-OFFLINE",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "PICK",
            "quantity": qty,
            "location": loc,
            "timestamp": t_pick.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": "",
            "sync_status": "PENDING_SYNC"
        }
    ]

    # Technician physically removed 2 units
    df_counts = pd.DataFrame([
        {"part_id": part_id, "part_name": part_name, "location": loc, "physical_stock": 10 - qty}
    ])
    df_tx = pd.DataFrame(tx_list)

    engine = ReconciliationEngine(df_tx, df_counts)
    rec_result = engine.reconcile_item(part_id, loc)

    return {
        "scenario_title": "Network Synchronization Failure",
        "part_id": part_id,
        "part_name": part_name,
        "location": loc,
        "quantity": qty,
        "normal_state": {
            "description": f"Initial inventory balance: 10 units of {part_name} at {loc}.",
            "system_stock": 10,
            "physical_stock": 10
        },
        "failure_state": {
            "description": f"Technician consumed {qty} units for repair work, but warehouse gateway was down. Transaction cached locally with PENDING_SYNC status.",
            "central_system_stock": 10, # Central ledger ignores unsynced transactions
            "physical_stock": 10 - qty,
            "apparent_variance": qty # System shows +2 higher than physical shelf
        },
        "transactions_table": df_tx,
        "reconciliation": rec_result
    }


def simulate_timestamp_anomaly(
    part_id: str = "SP-004",
    source_loc: str = "Mumbai Repair Hub",
    dest_loc: str = "Bangalore Repair Hub",
    qty: int = 2
) -> Dict[str, Any]:
    """
    Scenario 4: Timestamp Anomaly
    Simulates inverted chronological events (TRANSFER_IN before TRANSFER_OUT).
    """
    part_name = PARTS_CATALOG.get(part_id, "Fiber Optic Gyroscope")
    trf_id = "TRF-SIM-TIME-90"
    t_out = datetime(2026, 8, 15, 14, 0, 0)
    t_in = datetime(2026, 8, 15, 11, 0, 0) # Logged 3 hours earlier!

    tx_list = [
        {
            "transaction_id": "TX-SIM-TIN",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "TRANSFER_IN",
            "quantity": qty,
            "location": dest_loc,
            "timestamp": t_in.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": trf_id,
            "sync_status": "SYNCED"
        },
        {
            "transaction_id": "TX-SIM-TOUT",
            "part_id": part_id,
            "part_name": part_name,
            "event_type": "TRANSFER_OUT",
            "quantity": qty,
            "location": source_loc,
            "timestamp": t_out.strftime("%Y-%m-%d %H:%M:%S"),
            "transfer_id": trf_id,
            "sync_status": "SYNCED"
        }
    ]

    df_counts = pd.DataFrame([
        {"part_id": part_id, "part_name": part_name, "location": dest_loc, "physical_stock": qty}
    ])
    df_tx = pd.DataFrame(tx_list)

    engine = ReconciliationEngine(df_tx, df_counts)
    rec_result = engine.reconcile_item(part_id, dest_loc)

    return {
        "scenario_title": "Timestamp Sequence Anomaly",
        "part_id": part_id,
        "part_name": part_name,
        "source_loc": source_loc,
        "dest_loc": dest_loc,
        "transfer_id": trf_id,
        "quantity": qty,
        "normal_state": {
            "description": f"Standard inter-hub transfer: Dispatch event (TRANSFER_OUT) must precede destination intake (TRANSFER_IN).",
        },
        "failure_state": {
            "description": f"Due to terminal NTP clock drift, inbound TRANSFER_IN ({t_in.strftime('%H:%M')}) was timestamped 3 hours BEFORE dispatch TRANSFER_OUT ({t_out.strftime('%H:%M')}).",
            "time_discrepancy": "Inverted chronology (Inbound preceding Outbound)"
        },
        "transactions_table": df_tx,
        "reconciliation": rec_result
    }
