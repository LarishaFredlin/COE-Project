
"""
SpareSync Baseline Variance Detection

Calculates system stock from transactions, compares it
with physical stock, and calculates variance.

Does NOT attempt to explain the cause of discrepancies.
"""

from typing import Dict, Any, List, Optional
import math
import pandas as pd


TRANSACTION_COLUMNS = {
    "part_id",
    "sync_status",
    "location",
    "event_type",
    "quantity"
}

PHYSICAL_COUNT_COLUMNS = {
    "part_id",
    "part_name",
    "location",
    "physical_stock"
}

VALID_EVENT_TYPES = {
    "RECEIPT",
    "PICK",
    "TRANSFER_IN",
    "TRANSFER_OUT",
    "ADJUSTMENT",
    "PHYSICAL_COUNT"
}


def calculate_system_stock(
    df_transactions: pd.DataFrame,
    part_id: str,
    location: Optional[str] = None
) -> int:
    """
    Calculate system stock using only SYNCED transactions.

    Raises:
        ValueError: If required columns, quantities, or event
                    types are invalid.
    """

    if not isinstance(df_transactions, pd.DataFrame):
        raise ValueError("Transactions must be a pandas DataFrame.")

    missing_columns = TRANSACTION_COLUMNS - set(df_transactions.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required transaction columns: {missing}")

    df = df_transactions.copy()

    df = df[
        (df["part_id"] == part_id) &
        (df["sync_status"] == "SYNCED")
    ]

    if location:
        df = df[df["location"] == location]

    stock = 0

    for _, row in df.iterrows():

        event_type = str(row["event_type"]).upper().strip()

        if event_type not in VALID_EVENT_TYPES:
            raise ValueError(
                f"Invalid event_type: {event_type}"
            )

        # Physical counts are observations, not stock movements.
        if event_type == "PHYSICAL_COUNT":
            continue

        try:
            numeric_quantity = float(row["quantity"])

            if not math.isfinite(numeric_quantity):
                raise ValueError

            if not numeric_quantity.is_integer():
                raise ValueError

            quantity = int(numeric_quantity)

        except (TypeError, ValueError, OverflowError):
            raise ValueError(
                f"Invalid quantity value: {row['quantity']}"
            ) from None

        if event_type in ["RECEIPT", "TRANSFER_IN"]:
            stock += quantity

        elif event_type in ["PICK", "TRANSFER_OUT"]:
            stock -= quantity

        elif event_type == "ADJUSTMENT":
            # Signed adjustment:
            # +5 increases stock; -5 decreases stock.
            stock += quantity

    return stock


def compute_baseline_audit(
    df_transactions: pd.DataFrame,
    df_physical_counts: pd.DataFrame,
    part_id: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Audit inventory using:

        variance = system_stock - physical_stock
    """

    if not isinstance(df_physical_counts, pd.DataFrame):
        raise ValueError("Physical counts must be a pandas DataFrame.")

    missing_columns = (
        PHYSICAL_COUNT_COLUMNS - set(df_physical_counts.columns)
    )

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required physical count columns: {missing}")

    counts_df = df_physical_counts.copy()

    if part_id:
        counts_df = counts_df[counts_df["part_id"] == part_id]

    if location:
        counts_df = counts_df[counts_df["location"] == location]

    results = []

    for _, row in counts_df.iterrows():

        p_id = row["part_id"]
        p_name = row["part_name"]
        loc = row["location"]

        try:
            numeric_stock = float(row["physical_stock"])

            if not math.isfinite(numeric_stock):
                raise ValueError

            if not numeric_stock.is_integer():
                raise ValueError

            physical_stock = int(numeric_stock)

        except (TypeError, ValueError, OverflowError):
            raise ValueError(
                f"Invalid physical_stock value: {row['physical_stock']}"
            ) from None

        system_stock = calculate_system_stock(
            df_transactions,
            p_id,
            loc
        )

        variance = system_stock - physical_stock

        results.append({
            "part_id": p_id,
            "part_name": p_name,
            "location": loc,
            "system_stock": system_stock,
            "physical_stock": physical_stock,
            "variance": variance,
            "has_variance": variance != 0,
            "status": (
                "Variance Detected"
                if variance != 0
                else "No Variance"
            ),
            "explanation": (
                "No explanation provided by baseline system."
            )
        })

    return results
