"""
SpareSync Data Generator
Generates synthetic inventory transactions and physical count audits with known failure scenarios and ground truth labels.
"""

import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Tuple
import pandas as pd

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True, parents=True)

TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
PHYSICAL_COUNTS_FILE = DATA_DIR / "physical_counts.csv"

# Catalog and Locations
PARTS_CATALOG = {
    "SP-001": "Turbine Flow Sensor",
    "SP-002": "High-Voltage Inverter Module",
    "SP-003": "Hydraulic Servo Valve",
    "SP-004": "Fiber Optic Gyroscope",
    "SP-005": "CNC Controller Board",
    "SP-006": "Diode Laser Pump",
    "SP-007": "Cryogenic Pump",
    "SP-008": "Optical Transceiver Array",
}

LOCATIONS = [
    "Chennai Repair Hub",
    "Bangalore Repair Hub",
    "Mumbai Repair Hub",
]


def generate_synthetic_data(seed: int = 42, num_records: int = 350) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates realistic inventory transactions and physical counts.
    Injects 4 specific failure modes with ground truth:
      1. Missing TRANSFER_IN after TRANSFER_OUT (SP-001 at Bangalore)
      2. Duplicate RECEIPT transaction (SP-002 at Mumbai)
      3. Unsynchronized PICK due to network outage (SP-003 at Chennai)
      4. Out-of-order timestamp sequence (SP-004 at Bangalore)
    """
    random.seed(seed)
    transactions = []
    current_time = datetime(2026, 8, 1, 8, 0, 0)
    tx_id_counter = 1000

    # Ground truth mapping: (part_id, location) -> ground_truth_cause
    ground_truth_map = {}

    # Running inventory balance per (part_id, location)
    running_balance = {(pid, loc): 0 for pid in PARTS_CATALOG.keys() for loc in LOCATIONS}

    # 1. Initial Stock Receipts for all parts and locations
    for part_id, part_name in PARTS_CATALOG.items():
        for loc in LOCATIONS:
            tx_id_counter += 1
            current_time += timedelta(minutes=random.randint(10, 30))
            init_qty = random.randint(10, 20)
            
            transactions.append({
                "transaction_id": f"TX-{tx_id_counter}",
                "part_id": part_id,
                "part_name": part_name,
                "event_type": "RECEIPT",
                "quantity": init_qty,
                "location": loc,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "transfer_id": "",
                "sync_status": "SYNCED"
            })
            running_balance[(part_id, loc)] += init_qty

    # 2. Standard routine transactions (Picks, Receipts, Completed Transfers)
    part_keys = list(PARTS_CATALOG.keys())
    while len(transactions) < num_records - 15:
        tx_id_counter += 1
        current_time += timedelta(minutes=random.randint(15, 90))
        part_id = random.choice(part_keys)
        part_name = PARTS_CATALOG[part_id]
        loc = random.choice(LOCATIONS)
        
        event_choice = random.choices(["PICK", "TRANSFER", "RECEIPT"], weights=[0.55, 0.30, 0.15])[0]

        if event_choice == "PICK":
            if running_balance[(part_id, loc)] > 2:
                pick_qty = random.randint(1, 2)
                transactions.append({
                    "transaction_id": f"TX-{tx_id_counter}",
                    "part_id": part_id,
                    "part_name": part_name,
                    "event_type": "PICK",
                    "quantity": pick_qty,
                    "location": loc,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "transfer_id": "",
                    "sync_status": "SYNCED"
                })
                running_balance[(part_id, loc)] -= pick_qty

        elif event_choice == "TRANSFER":
            src_loc = loc
            dst_loc = random.choice([l for l in LOCATIONS if l != src_loc])
            if running_balance[(part_id, src_loc)] > 3:
                trf_qty = random.randint(1, 2)
                trf_id = f"TRF-{tx_id_counter}"
                
                # Outbound
                transactions.append({
                    "transaction_id": f"TX-{tx_id_counter}",
                    "part_id": part_id,
                    "part_name": part_name,
                    "event_type": "TRANSFER_OUT",
                    "quantity": trf_qty,
                    "location": src_loc,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "transfer_id": trf_id,
                    "sync_status": "SYNCED"
                })
                running_balance[(part_id, src_loc)] -= trf_qty

                # Inbound (matched)
                tx_id_counter += 1
                in_time = current_time + timedelta(hours=random.randint(1, 4))
                transactions.append({
                    "transaction_id": f"TX-{tx_id_counter}",
                    "part_id": part_id,
                    "part_name": part_name,
                    "event_type": "TRANSFER_IN",
                    "quantity": trf_qty,
                    "location": dst_loc,
                    "timestamp": in_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "transfer_id": trf_id,
                    "sync_status": "SYNCED"
                })
                running_balance[(part_id, dst_loc)] += trf_qty

        elif event_choice == "RECEIPT":
            rcv_qty = random.randint(2, 4)
            transactions.append({
                "transaction_id": f"TX-{tx_id_counter}",
                "part_id": part_id,
                "part_name": part_name,
                "event_type": "RECEIPT",
                "quantity": rcv_qty,
                "location": loc,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "transfer_id": "",
                "sync_status": "SYNCED"
            })
            running_balance[(part_id, loc)] += rcv_qty

    # 3. INJECTED FAILURE 1: Missing TRANSFER_IN (SP-001: Chennai -> Bangalore)
    tx_id_counter += 1
    current_time += timedelta(hours=2)
    f1_part = "SP-001"
    f1_trf_id = "TRF-FAIL-901"
    f1_qty = 3
    transactions.append({
        "transaction_id": f"TX-{tx_id_counter}",
        "part_id": f1_part,
        "part_name": PARTS_CATALOG[f1_part],
        "event_type": "TRANSFER_OUT",
        "quantity": f1_qty,
        "location": "Chennai Repair Hub",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": f1_trf_id,
        "sync_status": "SYNCED"
    })
    running_balance[(f1_part, "Chennai Repair Hub")] -= f1_qty
    # The physical parts arrived at Bangalore, but TRANSFER_IN was never recorded in system ledger
    running_balance[(f1_part, "Bangalore Repair Hub")] += f1_qty
    ground_truth_map[(f1_part, "Bangalore Repair Hub")] = "MISSING_TRANSFER"

    # 4. INJECTED FAILURE 2: Duplicate RECEIPT (SP-002 at Mumbai Repair Hub)
    tx_id_counter += 1
    current_time += timedelta(hours=3)
    f2_part = "SP-002"
    f2_qty = 4
    t_dup1 = current_time
    t_dup2 = current_time + timedelta(minutes=4)
    transactions.append({
        "transaction_id": f"TX-{tx_id_counter}",
        "part_id": f2_part,
        "part_name": PARTS_CATALOG[f2_part],
        "event_type": "RECEIPT",
        "quantity": f2_qty,
        "location": "Mumbai Repair Hub",
        "timestamp": t_dup1.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": "",
        "sync_status": "SYNCED"
    })
    tx_id_counter += 1
    transactions.append({
        "transaction_id": f"TX-{tx_id_counter}",
        "part_id": f2_part,
        "part_name": PARTS_CATALOG[f2_part],
        "event_type": "RECEIPT",
        "quantity": f2_qty,
        "location": "Mumbai Repair Hub",
        "timestamp": t_dup2.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": "",
        "sync_status": "SYNCED"
    })
    running_balance[(f2_part, "Mumbai Repair Hub")] += f2_qty
    ground_truth_map[(f2_part, "Mumbai Repair Hub")] = "DUPLICATE_TRANSACTION"

    # 5. INJECTED FAILURE 3: Network Failure (PENDING_SYNC PICK on SP-003 at Chennai Repair Hub)
    tx_id_counter += 1
    current_time += timedelta(hours=2)
    f3_part = "SP-003"
    f3_qty = 2
    transactions.append({
        "transaction_id": f"TX-{tx_id_counter}",
        "part_id": f3_part,
        "part_name": PARTS_CATALOG[f3_part],
        "event_type": "PICK",
        "quantity": f3_qty,
        "location": "Chennai Repair Hub",
        "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": "",
        "sync_status": "PENDING_SYNC"
    })
    running_balance[(f3_part, "Chennai Repair Hub")] -= f3_qty
    ground_truth_map[(f3_part, "Chennai Repair Hub")] = "NETWORK_SYNC_FAILURE"

    # 6. INJECTED FAILURE 4: Timestamp Anomaly (SP-004 at Bangalore Repair Hub)
    tx_id_counter += 1
    current_time += timedelta(hours=2)
    f4_part = "SP-004"
    f4_trf_id = "TRF-TIME-808"
    f4_qty = 2
    t_out = current_time + timedelta(hours=2)
    t_in = current_time - timedelta(hours=1)
    transactions.append({
        "transaction_id": f"TX-{tx_id_counter}",
        "part_id": f4_part,
        "part_name": PARTS_CATALOG[f4_part],
        "event_type": "TRANSFER_IN",
        "quantity": f4_qty,
        "location": "Bangalore Repair Hub",
        "timestamp": t_in.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": f4_trf_id,
        "sync_status": "SYNCED"
    })
    tx_id_counter += 1
    transactions.append({
        "transaction_id": f"TX-{tx_id_counter}",
        "part_id": f4_part,
        "part_name": PARTS_CATALOG[f4_part],
        "event_type": "TRANSFER_OUT",
        "quantity": f4_qty,
        "location": "Mumbai Repair Hub",
        "timestamp": t_out.strftime("%Y-%m-%d %H:%M:%S"),
        "transfer_id": f4_trf_id,
        "sync_status": "SYNCED"
    })
    running_balance[(f4_part, "Mumbai Repair Hub")] -= f4_qty
    running_balance[(f4_part, "Bangalore Repair Hub")] += f4_qty
    ground_truth_map[(f4_part, "Bangalore Repair Hub")] = "TIMESTAMP_ANOMALY"

    # 7. Generate Physical Counts with Ground Truth Labels
    df_tx = pd.DataFrame(transactions)
    df_tx["parsed_ts"] = pd.to_datetime(df_tx["timestamp"])
    df_tx = df_tx.sort_values(by="parsed_ts").drop(columns=["parsed_ts"]).reset_index(drop=True)

    physical_counts = []
    audit_time = current_time + timedelta(hours=12)

    for part_id, part_name in PARTS_CATALOG.items():
        for loc in LOCATIONS:
            phys_stock = running_balance[(part_id, loc)]
            gt_cause = ground_truth_map.get((part_id, loc), "NONE")

            physical_counts.append({
                "part_id": part_id,
                "part_name": part_name,
                "location": loc,
                "physical_stock": max(0, phys_stock),
                "ground_truth_cause": gt_cause,
                "last_audit_timestamp": audit_time.strftime("%Y-%m-%d %H:%M:%S")
            })

    df_counts = pd.DataFrame(physical_counts)

    # Save to disk
    df_tx.to_csv(TRANSACTIONS_FILE, index=False)
    df_counts.to_csv(PHYSICAL_COUNTS_FILE, index=False)

    return df_tx, df_counts


if __name__ == "__main__":
    df_t, df_c = generate_synthetic_data()
    print(f"Generated {len(df_t)} transactions -> {TRANSACTIONS_FILE}")
    print(f"Generated {len(df_c)} physical count records -> {PHYSICAL_COUNTS_FILE}")
