"""
Test Suite: Evaluation Metrics & Benchmark Module
Verifies:
1. Dynamic benchmark execution without hardcoded values
2. Correct mathematical formula computation for accuracy and variance reduction
3. Feature comparison matrix consistency
"""

import pytest
from src.metrics import run_benchmark_experiment, EvaluationBenchmark
from src.data_generator import generate_synthetic_data


def test_benchmark_experiment_execution():
    """Verify evaluation benchmark executes and returns all structured metrics."""
    results = run_benchmark_experiment()

    assert "total_items_audited" in results
    assert "total_variance_cases" in results
    assert "correctly_explained_cases" in results
    assert "unexplained_cases" in results
    assert "baseline" in results
    assert "sparesync" in results
    assert "feature_comparison_df" in results
    assert "detailed_failures_df" in results

    assert results["total_items_audited"] > 0
    assert results["total_variance_cases"] > 0


def test_metric_formula_calculations():
    """Verify accuracy, unexplained variance rate, and variance reduction formulas."""
    results = run_benchmark_experiment()
    
    total_var = results["total_variance_cases"]
    explained = results["correctly_explained_cases"]
    unexplained = results["unexplained_cases"]

    # Verify counts sum
    assert explained + unexplained == total_var

    # Verify Baseline metrics
    assert results["baseline"]["unexplained_variance_rate_pct"] == 100.0
    assert results["baseline"]["explanation_accuracy_pct"] == 0.0

    # Verify SpareSync metrics
    expected_accuracy = round((explained / total_var) * 100.0, 1)
    expected_unexplained_rate = round((unexplained / total_var) * 100.0, 1)
    expected_reduction = round(100.0 - expected_unexplained_rate, 1)

    assert results["sparesync"]["explanation_accuracy_pct"] == expected_accuracy
    assert results["sparesync"]["unexplained_variance_rate_pct"] == expected_unexplained_rate
    assert results["sparesync"]["variance_reduction_pct"] == expected_reduction
    assert results["sparesync"]["processing_time_ms"] >= 0.0


def test_feature_comparison_table():
    """Verify feature comparison table contains all 8 required capability comparisons."""
    results = run_benchmark_experiment()
    df_feat = results["feature_comparison_df"]

    required_features = [
        "Detect Variance",
        "Explain Cause",
        "Analyse Transaction History",
        "Detect Missing Events",
        "Detect Duplicate Events",
        "Support Offline Transactions",
        "Provide Evidence",
        "Recommended Action"
    ]

    for feat in required_features:
        row = df_feat[df_feat["Feature"] == feat]
        assert not row.empty
        assert row.iloc[0]["SpareSync"] == "Yes"
