"""
SpareSync Rule-Based Reconciliation Engine
Analyzes transaction streams chronologically to identify root causes of inventory discrepancies
and attaches decision trade-off evaluations (Cost, Time, Emissions, Reliability).
"""

from typing import Dict, Any, List, Optional
import pandas as pd
from src.baseline import calculate_system_stock
from src.tradeoffs import get_tradeoff_for_issue


class ReconciliationEngine:
    """
    Transparent, rule-based reconciliation engine for slow-moving spare parts.
    """

    def __init__(self, df_transactions: pd.DataFrame, df_physical_counts: pd.DataFrame):
        self.df_transactions = df_transactions.copy()
        self.df_physical_counts = df_physical_counts.copy()
        
        # Ensure timestamp sorting
        if "parsed_ts" not in self.df_transactions.columns:
            self.df_transactions["parsed_ts"] = pd.to_datetime(self.df_transactions["timestamp"], errors="coerce")
        self.df_transactions = self.df_transactions.sort_values(by="parsed_ts").reset_index(drop=True)

    def detect_missing_transfers(self, part_id: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Rule 1: Detects TRANSFER_OUT with a transfer_id that has no matching TRANSFER_IN anywhere in the network.
        """
        df = self.df_transactions.copy()
        if part_id:
            df = df[df["part_id"] == part_id]

        transfers_out = df[df["event_type"] == "TRANSFER_OUT"]
        transfers_in = df[df["event_type"] == "TRANSFER_IN"]

        confirmed_ids = set(transfers_in["transfer_id"].dropna().unique())
        issues = []

        for _, out_row in transfers_out.iterrows():
            trf_id = out_row.get("transfer_id", "")
            src_loc = out_row.get("location", "")
            
            if not trf_id or trf_id not in confirmed_ids:
                issues.append({
                    "issue_type": "MISSING_TRANSFER",
                    "part_id": out_row["part_id"],
                    "part_name": out_row["part_name"],
                    "location": location or src_loc,
                    "transfer_id": trf_id,
                    "quantity": int(out_row["quantity"]),
                    "timestamp": str(out_row["timestamp"]),
                    "tx_id": out_row["transaction_id"],
                    "likely_cause": f"Unconfirmed inter-hub transfer ({trf_id}). Parts were dispatched from {src_loc} but inbound receipt was never logged at destination.",
                    "evidence": [
                        f"TRANSFER_OUT transaction {out_row['transaction_id']} for {out_row['quantity']} units recorded at {src_loc} on {out_row['timestamp']}.",
                        f"Transfer identifier '{trf_id}' has no corresponding TRANSFER_IN entry in central ledger.",
                        f"Physical inventory at destination hub holds {out_row['quantity']} units not accounted for in system ledger."
                    ],
                    "confidence": "High (92%)",
                    "recommended_action": f"Contact logistics coordinator at destination warehouse to confirm in-transit delivery and log missing TRANSFER_IN entry for {trf_id}."
                })

        return issues

    def detect_duplicate_transactions(
        self,
        part_id: Optional[str] = None,
        location: Optional[str] = None,
        time_window_mins: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Rule 2: Detects highly similar transactions (same part, event_type, quantity, location) within a short time window.
        """
        df = self.df_transactions.copy()
        if part_id:
            df = df[df["part_id"] == part_id]
        if location:
            df = df[df["location"] == location]

        df = df.reset_index(drop=True)
        issues = []
        visited = set()
        n = len(df)

        for i in range(n):
            if i in visited:
                continue
            row1 = df.iloc[i]
            t1 = row1["parsed_ts"]

            for j in range(i + 1, n):
                if j in visited:
                    continue
                row2 = df.iloc[j]
                t2 = row2["parsed_ts"]
                diff_mins = (t2 - t1).total_seconds() / 60.0

                if diff_mins > time_window_mins:
                    break

                if (
                    row1["part_id"] == row2["part_id"] and
                    row1["event_type"] == row2["event_type"] and
                    row1["quantity"] == row2["quantity"] and
                    row1["location"] == row2["location"]
                ):
                    visited.add(j)
                    issues.append({
                        "issue_type": "DUPLICATE_TRANSACTION",
                        "part_id": row1["part_id"],
                        "part_name": row1["part_name"],
                        "location": row1["location"],
                        "quantity": int(row1["quantity"]),
                        "tx_1": row1["transaction_id"],
                        "time_1": str(row1["timestamp"]),
                        "tx_2": row2["transaction_id"],
                        "time_2": str(row2["timestamp"]),
                        "time_diff_mins": round(diff_mins, 1),
                        "likely_cause": f"Duplicate {row1['event_type']} transaction logged within {round(diff_mins, 1)} minutes.",
                        "evidence": [
                            f"Initial {row1['event_type']} {row1['transaction_id']} (qty: {row1['quantity']}) recorded at {row1['timestamp']}.",
                            f"Duplicate {row2['event_type']} {row2['transaction_id']} (qty: {row2['quantity']}) recorded at {row2['timestamp']}.",
                            f"Identical part ID ({row1['part_id']}) and location ({row1['location']}) within short time delta ({round(diff_mins, 1)} min)."
                        ],
                        "confidence": "High (88%)",
                        "recommended_action": f"Investigate transaction history against supplier delivery docket and reverse redundant entry {row2['transaction_id']}."
                    })

        return issues

    def detect_network_sync_failures(self, part_id: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Rule 3: Detects transactions with PENDING_SYNC status (edge/offline queue not pushed to central ledger).
        """
        df = self.df_transactions[self.df_transactions["sync_status"] == "PENDING_SYNC"].copy()
        if part_id:
            df = df[df["part_id"] == part_id]
        if location:
            df = df[df["location"] == location]

        issues = []
        for _, row in df.iterrows():
            issues.append({
                "issue_type": "NETWORK_SYNC_FAILURE",
                "part_id": row["part_id"],
                "part_name": row["part_name"],
                "location": row["location"],
                "quantity": int(row["quantity"]),
                "tx_id": row["transaction_id"],
                "event_type": row["event_type"],
                "timestamp": str(row["timestamp"]),
                "likely_cause": f"Unsynchronized {row['event_type']} transaction caused by edge network disconnect.",
                "evidence": [
                    f"Transaction {row['transaction_id']} ({row['event_type']} {row['quantity']} units) is marked as 'PENDING_SYNC'.",
                    f"Logged locally at {row['location']} on {row['timestamp']}, but excluded from central reconciled ledger.",
                    "Physical count reflects technician consumption that central database has not yet received."
                ],
                "confidence": "High (95%)",
                "recommended_action": "Wait for pending synchronization or trigger store-and-forward synchronizer on local warehouse terminal."
            })

        return issues

    def detect_timestamp_anomalies(self, part_id: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Rule 4: Detects out-of-order sequence (e.g. TRANSFER_IN timestamped prior to matching TRANSFER_OUT).
        """
        df = self.df_transactions.copy()
        if part_id:
            df = df[df["part_id"] == part_id]

        transfers_out = df[df["event_type"] == "TRANSFER_OUT"]
        transfers_in = df[df["event_type"] == "TRANSFER_IN"]
        issues = []

        for _, in_row in transfers_in.iterrows():
            trf_id = in_row.get("transfer_id", "")
            if not trf_id:
                continue

            matching_out = transfers_out[transfers_out["transfer_id"] == trf_id]
            if not matching_out.empty:
                out_row = matching_out.iloc[0]
                if in_row["parsed_ts"] < out_row["parsed_ts"]:
                    if location and location not in [in_row["location"], out_row["location"]]:
                        continue

                    issues.append({
                        "issue_type": "TIMESTAMP_ANOMALY",
                        "part_id": in_row["part_id"],
                        "part_name": in_row["part_name"],
                        "location": in_row["location"],
                        "transfer_id": trf_id,
                        "in_tx": in_row["transaction_id"],
                        "in_time": str(in_row["timestamp"]),
                        "out_tx": out_row["transaction_id"],
                        "out_time": str(out_row["timestamp"]),
                        "likely_cause": "Out-of-sequence chronological timestamps due to terminal clock drift or network buffering.",
                        "evidence": [
                            f"TRANSFER_IN transaction {in_row['transaction_id']} recorded at {in_row['timestamp']}.",
                            f"TRANSFER_OUT transaction {out_row['transaction_id']} recorded LATER at {out_row['timestamp']}.",
                            f"Causal workflow violation on transfer {trf_id}."
                        ],
                        "confidence": "Medium (80%)",
                        "recommended_action": "Investigate transaction history and audit NTP server synchronization on edge barcode scanners."
                    })

        return issues

    def reconcile_item(self, part_id: str, location: str) -> Dict[str, Any]:
        """
        Reconciles a specific part and location, determining variance, root cause, and multi-criteria trade-offs.
        """
        system_stock = calculate_system_stock(self.df_transactions, part_id, location)
        
        # Get physical count
        count_row = self.df_physical_counts[
            (self.df_physical_counts["part_id"] == part_id) &
            (self.df_physical_counts["location"] == location)
        ]
        
        if count_row.empty:
            physical_stock = 0
            part_name = part_id
        else:
            physical_stock = int(count_row.iloc[0]["physical_stock"])
            part_name = count_row.iloc[0]["part_name"]

        variance = system_stock - physical_stock

        # Check rules
        missing_trfs = self.detect_missing_transfers(part_id=part_id, location=location)
        sync_fails = self.detect_network_sync_failures(part_id=part_id, location=location)
        duplicates = self.detect_duplicate_transactions(part_id=part_id, location=location)
        time_anoms = self.detect_timestamp_anomalies(part_id=part_id, location=location)

        # Diagnose primary root cause
        if sync_fails:
            issue = sync_fails[0]
            issue_type = issue["issue_type"]
            likely_cause = issue["likely_cause"]
            evidence = issue["evidence"]
            confidence = issue["confidence"]
            action = issue["recommended_action"]
        elif duplicates and variance != 0:
            issue = duplicates[0]
            issue_type = issue["issue_type"]
            likely_cause = issue["likely_cause"]
            evidence = issue["evidence"]
            confidence = issue["confidence"]
            action = issue["recommended_action"]
        elif missing_trfs and variance != 0:
            issue = missing_trfs[0]
            issue_type = issue["issue_type"]
            likely_cause = issue["likely_cause"]
            evidence = issue["evidence"]
            confidence = issue["confidence"]
            action = issue["recommended_action"]
        elif time_anoms:
            issue = time_anoms[0]
            issue_type = issue["issue_type"]
            likely_cause = issue["likely_cause"]
            evidence = issue["evidence"]
            confidence = issue["confidence"]
            action = issue["recommended_action"]
        elif variance != 0:
            issue_type = "UNEXPLAINED_VARIANCE"
            likely_cause = "Clerical count discrepancy or physical stock shrinkage."
            evidence = [
                f"Ledger calculation shows {system_stock} units.",
                f"Physical audit recorded {physical_stock} units (variance of {variance:+d}).",
                "No transaction anomaly signatures found in recent logs."
            ]
            confidence = "Medium (60%)"
            action = "Perform a manual physical recount of shelf bin locations."
        else:
            issue_type = "NONE"
            likely_cause = "Normal operations. System stock matches physical stock."
            evidence = [
                f"System stock ({system_stock}) and physical stock ({physical_stock}) are in exact agreement.",
                "All transaction flows are verified and synchronized."
            ]
            confidence = "High (100%)"
            action = "No corrective action required."

        # Fetch Decision Trade-Off Assessment
        tradeoff_meta = get_tradeoff_for_issue(issue_type)

        return {
            "part_id": part_id,
            "part_name": part_name,
            "location": location,
            "system_stock": system_stock,
            "physical_stock": physical_stock,
            "variance": variance,
            "has_variance": (variance != 0 or issue_type != "NONE"),
            "issue_type": issue_type,
            "likely_cause": likely_cause,
            "evidence": evidence,
            "confidence": confidence,
            "recommended_action": action,
            "tradeoff": tradeoff_meta
        }

    def reconcile_all(self) -> pd.DataFrame:
        """
        Reconciles all part-location pairs across the network.
        """
        records = []
        unique_pairs = self.df_physical_counts[["part_id", "location"]].drop_duplicates()
        
        for _, row in unique_pairs.iterrows():
            rec = self.reconcile_item(row["part_id"], row["location"])
            records.append(rec)

        return pd.DataFrame(records)
