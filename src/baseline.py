"""
SpareSync Baseline Variance Detection
Calculates system stock from transactions, compares with physical stock, and calculates variance.
Does NOT attempt to explain the cause of any discrepancy.
"""

from typing import Dict, Any, List, Optional
import pandas as pd



def calculate_system_stock(
    df_transactions: pd.DataFrame,
    part_id: str,
    location: Optional[str] = None
) -> int:
    """
    Computes system stock from the transaction ledger.

    Only SYNCED transactions are included in central system stock.
    Physical counts are observations, not stock movements.
    """

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
        quantity = int(row["quantity"])

        if event_type in ["RECEIPT", "TRANSFER_IN"]:
            stock += quantity

        elif event_type in ["PICK", "TRANSFER_OUT"]:
            stock -= quantity

        elif event_type == "ADJUSTMENT":
            # Adjustment quantity must be signed:
            # +5 means increase, -5 means decrease.
            stock += quantity

        elif event_type == "PHYSICAL_COUNT":
            # A physical count is an observation.
            # It must not modify ledger stock.
            continue

    return stock

def compute_baseline_audit(
    df_transactions: pd.DataFrame,
    df_physical_counts: pd.DataFrame,
    part_id: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Audits inventory using the baseline formula:
    variance = system_stock - physical_stock
    """
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
        physical_stock = int(row["physical_stock"])

        system_stock = calculate_system_stock(df_transactions, p_id, loc)
        variance = system_stock - physical_stock

        results.append({
            "part_id": p_id,
            "part_name": p_name,
            "location": loc,
            "system_stock": system_stock,
            "physical_stock": physical_stock,
            "variance": variance,
            "has_variance": (variance != 0),
            "status": "Variance Detected" if variance != 0 else "No Variance",
            "explanation": "No explanation provided by baseline system."
        })

    return results
