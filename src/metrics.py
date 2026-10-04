
"""
SpareSync Evaluation Metrics & Benchmarking Module

Compares the Baseline Auditor against the SpareSync
Rule-Based Reconciliation Engine.
"""

import time
from typing import Dict, Any, List

import pandas as pd

from src.data_generator import (
    TRANSACTIONS_FILE,
    PHYSICAL_COUNTS_FILE,
    generate_synthetic_data,
)
from src.baseline import compute_baseline_audit
from src.reconciliation_engine import ReconciliationEngine


class EvaluationBenchmark:
    """
    Executes evaluation experiments comparing Baseline vs SpareSync.
    """

    def __init__(
        self,
        df_transactions: pd.DataFrame,
        df_physical_counts: pd.DataFrame
    ):
        self.df_transactions = df_transactions.copy()
        self.df_physical_counts = df_physical_counts.copy()

        self.engine = ReconciliationEngine(
            self.df_transactions,
            self.df_physical_counts
        )

    def run_evaluation(self) -> Dict[str, Any]:
        """
        Runs network-wide evaluation and calculates performance metrics.
        """

        # 1. Run Baseline
        baseline_start = time.perf_counter()

        baseline_records = compute_baseline_audit(
            self.df_transactions,
            self.df_physical_counts
        )

        df_baseline = pd.DataFrame(baseline_records)

        baseline_time_ms = (
            time.perf_counter() - baseline_start
        ) * 1000.0

        # 2. Run SpareSync
        sparesync_start = time.perf_counter()

        df_sparesync = self.engine.reconcile_all()

        sparesync_time_ms = (
            time.perf_counter() - sparesync_start
        ) * 1000.0

        # 3. Prepare Ground Truth
       
        # 3. Prepare Ground Truth
        gt_subset = self.df_physical_counts[
            ["part_id", "location", "ground_truth"]
        ].drop_duplicates(
            subset=["part_id", "location"]
        )

        gt_subset = gt_subset.rename(
            columns={"ground_truth": "ground_truth_cause"}
        )
        
        # 4. Merge Predictions with Ground Truth
        df_merged = pd.merge(
            df_sparesync,
            gt_subset,
            on=["part_id", "location"],
            how="left"
        )

        df_merged["ground_truth_cause"] = (
            df_merged["ground_truth_cause"].fillna("NONE")
        )

        # 5. Identify Failure Cases
        failure_mask = (
            (df_merged["ground_truth_cause"] != "NONE") |
            (df_merged["variance"] != 0) |
            (df_merged["issue_type"] != "NONE")
        )

        df_failures = df_merged[failure_mask].copy()

        total_audited = len(df_merged)
        total_variance_cases = len(df_failures)

        # 6. Initialize Counters
        correctly_explained = 0
        false_positives = 0
        false_negatives = 0
        unexplained_cases = 0

        detailed_comparison: List[Dict[str, Any]] = []

        # 7. Compare Actual and Predicted Causes
        for _, row in df_failures.iterrows():

            gt = str(row["ground_truth_cause"])
            pred = str(row["issue_type"])

            is_match = (
                gt == pred
                and gt != "NONE"
                and pred != "UNEXPLAINED_VARIANCE"
            )

            if is_match:
                correctly_explained += 1

            elif gt == "NONE" and pred != "NONE":
                false_positives += 1
                unexplained_cases += 1

            elif gt != "NONE" and pred == "NONE":
                false_negatives += 1
                unexplained_cases += 1

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

        # 8. Calculate Metrics
        # Accuracy denominator follows the total evaluated failure cases.
        explanation_accuracy = (
            correctly_explained / total_variance_cases * 100.0
            if total_variance_cases > 0
            else 0.0
        )

        detection_denominator = (
            correctly_explained + false_negatives
        )

        detection_rate = (
            correctly_explained / detection_denominator * 100.0
            if detection_denominator > 0
            else 0.0
        )

        false_positive_rate = (
            false_positives / total_audited * 100.0
            if total_audited > 0
            else 0.0
        )

        # Baseline identifies variance but does not explain its cause.
        baseline_unexplained = total_variance_cases

        baseline_unexplained_rate = (
            100.0 if total_variance_cases > 0 else 0.0
        )

        prototype_unexplained_rate = (
            unexplained_cases / total_variance_cases * 100.0
            if total_variance_cases > 0
            else 0.0
        )

        variance_reduction = (
            baseline_unexplained_rate - prototype_unexplained_rate
        )

        # 9. Feature Capability Matrix
        feature_comparison = [
            {
                "Feature": "Detect Variance",
                "Baseline": "Yes",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Explain Cause",
                "Baseline": "No",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Analyse Transaction History",
                "Baseline": "No",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Detect Missing Events",
                "Baseline": "No",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Detect Duplicate Events",
                "Baseline": "No",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Support Offline Transactions",
                "Baseline": "No",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Provide Evidence",
                "Baseline": "No",
                "SpareSync": "Yes"
            },
            {
                "Feature": "Recommended Action",
                "Baseline": "No",
                "SpareSync": "Yes"
            }
        ]

        # 10. Return Results
        return {
            "total_items_audited": total_audited,
            "total_variance_cases": total_variance_cases,
            "correctly_explained_cases": correctly_explained,
            "unexplained_cases": unexplained_cases,
            "false_positives": false_positives,
            "false_negatives": false_negatives,
            "detection_rate_pct": round(detection_rate, 1),
            "false_positive_rate_pct": round(
                false_positive_rate, 1
            ),

            "baseline": {
                "explained_cases": 0,
                "unexplained_cases": baseline_unexplained,
                "explanation_accuracy_pct": 0.0,
                "unexplained_variance_rate_pct": round(
                    baseline_unexplained_rate, 1
                ),
                "processing_time_ms": round(
                    baseline_time_ms, 2
                )
            },

            "sparesync": {
                "explained_cases": correctly_explained,
                "unexplained_cases": unexplained_cases,
                "explanation_accuracy_pct": round(
                    explanation_accuracy, 1
                ),
                "unexplained_variance_rate_pct": round(
                    prototype_unexplained_rate, 1
                ),
                "variance_reduction_pct": round(
                    variance_reduction, 1
                ),
                "processing_time_ms": round(
                    sparesync_time_ms, 2
                )
            },

            "feature_comparison_df": pd.DataFrame(
                feature_comparison
            ),

            "detailed_failures_df": pd.DataFrame(
                detailed_comparison
            ),

            "full_audit_df": df_merged
        }


def run_benchmark_experiment() -> Dict[str, Any]:
    """
    Loads the current dataset and executes the benchmark.
    """

    if (
        not TRANSACTIONS_FILE.exists()
        or not PHYSICAL_COUNTS_FILE.exists()
    ):
        df_t, df_c = generate_synthetic_data()

    else:
        df_t = pd.read_csv(TRANSACTIONS_FILE)
        df_c = pd.read_csv(PHYSICAL_COUNTS_FILE)

    benchmark = EvaluationBenchmark(df_t, df_c)

    return benchmark.run_evaluation()


if __name__ == "__main__":

    results = run_benchmark_experiment()

    print("=" * 60)
    print(" SPARESYNC EVALUATION BENCHMARK RESULTS")
    print("=" * 60)

    print(
        f"Total Audits: {results['total_items_audited']}"
    )

    print(
        f"Total Failure Cases: {results['total_variance_cases']}"
    )

    print(
        f"Correctly Explained: {results['correctly_explained_cases']}"
    )

    print(
        f"Unexplained Cases: {results['unexplained_cases']}"
    )

    print(
        f"False Positives: {results['false_positives']}"
    )

    print(
        f"False Negatives: {results['false_negatives']}"
    )

    print(
        f"Detection Rate: {results['detection_rate_pct']}%"
    )

    print(
        f"False Positive Rate: {results['false_positive_rate_pct']}%"
    )

    print(
        f"Explanation Accuracy: "
        f"{results['sparesync']['explanation_accuracy_pct']}%"
    )

    print(
        f"Baseline Processing Time: "
        f"{results['baseline']['processing_time_ms']} ms"
    )

    print(
        f"SpareSync Processing Time: "
        f"{results['sparesync']['processing_time_ms']} ms"
    )

    print(
        f"Unexplained Variance Reduction: "
        f"{results['sparesync']['variance_reduction_pct']}%"
    )

    print("=" * 60)