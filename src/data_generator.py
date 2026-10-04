
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd


# --------------------------------------------------
# DATASET PATHS
# --------------------------------------------------

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

TRANSACTIONS_FILE = DATA_DIR / "transactions.csv"
PHYSICAL_COUNTS_FILE = DATA_DIR / "physical_counts.csv"


# --------------------------------------------------
# PARTS CATALOG
# --------------------------------------------------

PARTS_CATALOG = {
    "SP-001": "Turbine Flow Sensor",
    "SP-002": "High-Voltage Inverter Module",
    "SP-003": "Hydraulic Servo Valve",
    "SP-004": "Fiber Optic Gyroscope",
    "SP-005": "Precision Bearing Assembly",
    "SP-006": "Cooling Pump",
    "SP-007": "Power Control Unit",
    "SP-008": "Pressure Regulator",
}

PARTS = list(PARTS_CATALOG.keys())

LOCATIONS = ["Chennai", "Bangalore", "Mumbai"]


# --------------------------------------------------
# DATA GENERATOR
# --------------------------------------------------

def generate_synthetic_data(seed=42, num_records=350):

    random.seed(seed)

    current_time = datetime(2026, 8, 1, 8, 0)

    transactions = []

    running_balance = {
        (part, location): 0
        for part in PARTS
        for location in LOCATIONS
    }

    ground_truth_map = {}

    tx_id = 1000

    # --------------------------------------------------
    # TRANSACTION HELPER
    # --------------------------------------------------

    def add_transaction(
        part,
        location,
        event_type,
        quantity,
        timestamp,
        sync_status="SYNCED",
        transfer_id=None,
    ):
        nonlocal tx_id

        transactions.append({
            "transaction_id": tx_id,
            "part_id": part,
            "part_name": PARTS_CATALOG[part],
            "location": location,
            "event_type": event_type,
            "quantity": quantity,
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "sync_status": sync_status,
            "transfer_id": transfer_id,
        })

        tx_id += 1

    # --------------------------------------------------
    # INITIAL STOCK RECEIPTS
    # --------------------------------------------------

    for part in PARTS:
        for location in LOCATIONS:

            quantity = random.randint(10, 20)

            add_transaction(
                part,
                location,
                "RECEIPT",
                quantity,
                current_time,
            )

            running_balance[(part, location)] += quantity

    # --------------------------------------------------
    # ROUTINE TRANSACTIONS
    # --------------------------------------------------

    while len(transactions) < num_records - 15:

        part = random.choice(PARTS)
        location = random.choice(LOCATIONS)

        event = random.choices(
            ["PICK", "TRANSFER", "RECEIPT"],
            weights=[0.55, 0.30, 0.15],
        )[0]

        current_time += timedelta(
            minutes=random.randint(10, 180)
        )

        if event == "PICK":

            available = running_balance[(part, location)]

            if available > 2:

                quantity = random.randint(
                    1,
                    min(2, available),
                )

                add_transaction(
                    part,
                    location,
                    "PICK",
                    quantity,
                    current_time,
                )

                running_balance[(part, location)] -= quantity

        elif event == "RECEIPT":

            quantity = random.randint(2, 4)

            add_transaction(
                part,
                location,
                "RECEIPT",
                quantity,
                current_time,
            )

            running_balance[(part, location)] += quantity

        elif event == "TRANSFER":

            destination = random.choice(
                [
                    loc for loc in LOCATIONS
                    if loc != location
                ]
            )

            available = running_balance[(part, location)]

            if available > 3:

                quantity = random.randint(
                    1,
                    min(2, available),
                )

                transfer_id = f"TR-{tx_id}"

                add_transaction(
                    part,
                    location,
                    "TRANSFER_OUT",
                    quantity,
                    current_time,
                    transfer_id=transfer_id,
                )

                running_balance[(part, location)] -= quantity

                add_transaction(
                    part,
                    destination,
                    "TRANSFER_IN",
                    quantity,
                    current_time + timedelta(
                        hours=random.randint(1, 4)
                    ),
                    transfer_id=transfer_id,
                )

                running_balance[(part, destination)] += quantity

    # --------------------------------------------------
    # FAILURE 1: MISSING TRANSFER
    # --------------------------------------------------

    part = "SP-001"
    source = "Chennai"
    destination = "Bangalore"
    quantity = 3

    transfer_id = "TR-MISSING-001"

    add_transaction(
        part,
        source,
        "TRANSFER_OUT",
        quantity,
        current_time,
        transfer_id=transfer_id,
    )

    running_balance[(part, source)] -= quantity

    # Physical stock has arrived at destination,
    # but the destination receipt confirmation is missing.
    running_balance[(part, destination)] += quantity

    ground_truth_map[(part, destination)] = "MISSING_TRANSFER"

    # --------------------------------------------------
    # FAILURE 2: DUPLICATE RECEIPT
    # --------------------------------------------------

    part = "SP-002"
    location = "Mumbai"
    quantity = 4

    add_transaction(
        part,
        location,
        "RECEIPT",
        quantity,
        current_time,
    )

    add_transaction(
        part,
        location,
        "RECEIPT",
        quantity,
        current_time + timedelta(minutes=4),
    )

    # Physical stock reflects only one actual delivery.
    running_balance[(part, location)] += quantity

    ground_truth_map[(part, location)] = "DUPLICATE_TRANSACTION"

    # --------------------------------------------------
    # FAILURE 3: NETWORK SYNC FAILURE
    # --------------------------------------------------

    part = "SP-003"
    location = "Chennai"
    quantity = 2

    add_transaction(
        part,
        location,
        "PICK",
        quantity,
        current_time,
        sync_status="PENDING",
    )

    running_balance[(part, location)] -= quantity

    ground_truth_map[(part, location)] = "NETWORK_SYNC_FAILURE"

    # --------------------------------------------------
    # FAILURE 4: TIMESTAMP ANOMALY
    # --------------------------------------------------

    part = "SP-004"
    source = "Mumbai"
    destination = "Bangalore"
    quantity = 2

    transfer_id = "TR-TIME-004"

    add_transaction(
        part,
        destination,
        "TRANSFER_IN",
        quantity,
        current_time - timedelta(hours=1),
        transfer_id=transfer_id,
    )

    add_transaction(
        part,
        source,
        "TRANSFER_OUT",
        quantity,
        current_time + timedelta(hours=2),
        transfer_id=transfer_id,
    )

    running_balance[(part, source)] -= quantity
    running_balance[(part, destination)] += quantity

    ground_truth_map[(part, destination)] = "TIMESTAMP_ANOMALY"

    # --------------------------------------------------
    # ADJUSTMENT EVENT
    # --------------------------------------------------

    # Controlled adjustment example.
    # Positive quantity increases stock.

    part = "SP-008"
    location = "Chennai"

    adjustment_quantity = 2

    adjustment_time = current_time + timedelta(hours=3)

    add_transaction(
        part,
        location,
        "ADJUSTMENT",
        adjustment_quantity,
        adjustment_time,
    )

    running_balance[(part, location)] += adjustment_quantity

    # --------------------------------------------------
    # PHYSICAL COUNT GENERATION
    # --------------------------------------------------

    audit_time = current_time + timedelta(hours=12)

    physical_counts = []

    for part in PARTS:

        for location in LOCATIONS:

            physical_stock = max(
                0,
                running_balance[(part, location)],
            )

            physical_counts.append({
                "part_id": part,
                "part_name": PARTS_CATALOG[part],
                "location": location,
                "physical_stock": physical_stock,
                "ground_truth": ground_truth_map.get(
                    (part, location),
                    "NONE",
                ),
                "audit_timestamp": audit_time.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            })

            # Physical count is an observation,
            # not a stock movement.

            add_transaction(
                part,
                location,
                "PHYSICAL_COUNT",
                physical_stock,
                audit_time,
            )

    # --------------------------------------------------
    # DATAFRAME CREATION
    # --------------------------------------------------

    df_transactions = pd.DataFrame(transactions)

    df_physical = pd.DataFrame(physical_counts)

    # --------------------------------------------------
    # SORT TRANSACTIONS
    # --------------------------------------------------

    df_transactions["timestamp"] = pd.to_datetime(
        df_transactions["timestamp"]
    )

    df_transactions = df_transactions.sort_values(
        "timestamp"
    ).reset_index(drop=True)

    df_transactions["timestamp"] = (
        df_transactions["timestamp"].dt.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
    )

    # --------------------------------------------------
    # SAVE DATASETS
    # --------------------------------------------------

    df_transactions.to_csv(
        TRANSACTIONS_FILE,
        index=False,
    )

    df_physical.to_csv(
        PHYSICAL_COUNTS_FILE,
        index=False,
    )

    print("Synthetic data generated successfully!")

    print(f"Transactions: {len(df_transactions)}")
    print(f"Physical counts: {len(df_physical)}")

    print(f"Saved: {TRANSACTIONS_FILE}")
    print(f"Saved: {PHYSICAL_COUNTS_FILE}")

    return df_transactions, df_physical


# --------------------------------------------------
# MAIN
# --------------------------------------------------

if __name__ == "__main__":
    generate_synthetic_data()