"""
SpareSync Evaluation Metrics & Benchmarking Module
Measures empirical performance comparing the naive Baseline Auditor
against the SpareSync Rule-Based Reconciliation Engine.
"""

import time
from typing import Dict, Any, List
import pandas as pd

from src.data_generator import TRANSACTIONS_FILE, PHYSICAL_COUNTS_FILE, generate_synthetic_data
from src.baseline import compute_baseline_audit
from src.reconciliation_engine import ReconciliationEngine


class EvaluationBenchmark:
    """
    Executes automated evaluation experiments comparing Baseline vs. SpareSync against ground truth.
    """

    def __init__(self, df_transactions: pd.DataFrame, df_physical_counts: pd.DataFrame):
        self.df_transactions = df_transactions.copy()
        self.df_physical_counts = df_physical_counts.copy()
        self.engine = ReconciliationEngine(self.df_transactions, self.df_physical_counts)

    def run_evaluation(self) -> Dict[str, Any]:
        """
        Runs network-wide evaluation and calculates performance metrics dynamically.
        """
        start_time = time.perf_counter()

        # 1. Run Baseline
        baseline_records = compute_baseline_audit(self.df_transactions, self.df_physical_counts)
        df_baseline = pd.DataFrame(baseline_records)

        # 2. Run SpareSync Engine
        df_sparesync = self.engine.reconcile_all()

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # 3. Merge with Ground Truth Labels
        if "ground_truth_cause" in self.df_physical_counts.columns:
            gt_subset = self.df_physical_counts[["part_id", "location", "ground_truth_cause"]].drop_duplicates()
        else:
            # Fallback ground truth definition for known injected cases
            gt_subset = pd.DataFrame([
                {"part_id": "SP-001", "location": "Bangalore Repair Hub", "ground_truth_cause": "MISSING_TRANSFER"},
                {"part_id": "SP-002", "location": "Mumbai Repair Hub", "ground_truth_cause": "DUPLICATE_TRANSACTION"},
                {"part_id": "SP-003", "location": "Chennai Repair Hub", "ground_truth_cause": "NETWORK_SYNC_FAILURE"},
                {"part_id": "SP-004", "location": "Bangalore Repair Hub", "ground_truth_cause": "TIMESTAMP_ANOMALY"},
            ])

        df_merged = pd.merge(df_sparesync, gt_subset, on=["part_id", "location"], how="left")
        df_merged["ground_truth_cause"] = df_merged["ground_truth_cause"].fillna("NONE")

        # 4. Filter failure/variance cases
        failure_cases_mask = (
            (df_merged["ground_truth_cause"] != "NONE") |
            (df_merged["variance"] != 0) |
            (df_merged["issue_type"] != "NONE")
        )
        df_failures = df_merged[failure_cases_mask].copy()

        total_audited = len(df_merged)
        total_variance_cases = len(df_failures)

        # Calculate Correctly Explained Cases
        correctly_explained = 0
        unexplained_cases = 0
        detailed_comparison: List[Dict[str, Any]] = []

        for _, row in df_failures.iterrows():
            gt = str(row["ground_truth_cause"])
            pred = str(row["issue_type"])
            is_match = (gt == pred) and (pred != "UNEXPLAINED_VARIANCE")

            if is_match:
                correctly_explained += 1
            else:
                unexplained_cases += 1

            detailed_comparison.append({
                "part_id": row["part_id"],
                "part_name": row["part_name"],
                "location": row["location"],
                "system_stock": row["system_stock"],
                "physical_stock": row["physical_stock"],
                "variance": row["variance"],
                "ground_truth_cause": gt,
                "sparesync_cause": pred,
                "is_correctly_explained": is_match,
                "confidence": row["confidence"],
                "action_recommended": row["recommended_action"]
            })

        # Metric Calculations
        total_known_failures = max(1, total_variance_cases)
        explanation_accuracy = (correctly_explained / total_known_failures) * 100.0
        
        baseline_unexplained_rate = 100.0 if total_variance_cases > 0 else 0.0
        prototype_unexplained_rate = (unexplained_cases / total_known_failures) * 100.0
        variance_reduction = baseline_unexplained_rate - prototype_unexplained_rate

        # Feature Capability Matrix
        feature_comparison = [
            {"Feature": "Detect Variance", "Baseline": "Yes", "SpareSync": "Yes"},
            {"Feature": "Explain Cause", "Baseline": "No", "SpareSync": "Yes"},
            {"Feature": "Analyse Transaction History", "Baseline": "No", "SpareSync": "Yes"},
            {"Feature": "Detect Missing Events", "Baseline": "No", "SpareSync": "Yes"},
            {"Feature": "Detect Duplicate Events", "Baseline": "No", "SpareSync": "Yes"},
            {"Feature": "Support Offline Transactions", "Baseline": "No", "SpareSync": "Yes"},
            {"Feature": "Provide Evidence", "Baseline": "No", "SpareSync": "Yes"},
            {"Feature": "Recommended Action", "Baseline": "No", "SpareSync": "Yes"}
        ]

        return {
            "total_items_audited": total_audited,
            "total_variance_cases": total_variance_cases,
            "correctly_explained_cases": correctly_explained,
            "unexplained_cases": unexplained_cases,
            "baseline": {
                "explained_cases": 0,
                "unexplained_cases": total_variance_cases,
                "explanation_accuracy_pct": 0.0,
                "unexplained_variance_rate_pct": round(baseline_unexplained_rate, 1)
            },
            "sparesync": {
                "explained_cases": correctly_explained,
                "unexplained_cases": unexplained_cases,
                "explanation_accuracy_pct": round(explanation_accuracy, 1),
                "unexplained_variance_rate_pct": round(prototype_unexplained_rate, 1),
                "variance_reduction_pct": round(variance_reduction, 1),
                "processing_time_ms": round(elapsed_ms, 2)
            },
            "feature_comparison_df": pd.DataFrame(feature_comparison),
            "detailed_failures_df": pd.DataFrame(detailed_comparison),
            "full_audit_df": df_merged
        }


def run_benchmark_experiment() -> Dict[str, Any]:
    """Helper to load current dataset and execute benchmark."""
    if not TRANSACTIONS_FILE.exists() or not PHYSICAL_COUNTS_FILE.exists():
        df_t, df_c = generate_synthetic_data()
    else:
        df_t = pd.read_csv(TRANSACTIONS_FILE)
        df_c = pd.read_csv(PHYSICAL_COUNTS_FILE)

    bench = EvaluationBenchmark(df_t, df_c)
    return bench.run_evaluation()


if __name__ == "__main__":
    results = run_benchmark_experiment()
    print("=" * 60)
    print(" SPARESYNC EVALUATION BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total Audits Evaluated:      {results['total_items_audited']}")
    print(f"Total Variance Cases:        {results['total_variance_cases']}")
    print(f"Correctly Explained Cases:   {results['correctly_explained_cases']}")
    print(f"Unexplained Variance Cases:  {results['unexplained_cases']}")
    print(f"Baseline Unexplained Rate:   {results['baseline']['unexplained_variance_rate_pct']}%")
    print(f"Prototype Unexplained Rate:  {results['sparesync']['unexplained_variance_rate_pct']}%")
    print(f"Variance Reduction:          {results['sparesync']['variance_reduction_pct']}%")
    print(f"Explanation Accuracy:        {results['sparesync']['explanation_accuracy_pct']}%")
    print(f"Processing Latency:          {results['sparesync']['processing_time_ms']} ms")
    print("=" * 60)
