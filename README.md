# SpareSync – Inventory Transaction Reconciliation Engine

> **Operational Intelligence for Multi-Hub Spare Parts Repair Networks**  
> *Academic Milestone: Review 1 Prototype (~35% Complete Scope)*

---

## 1. Project Overview

**SpareSync** is a rule-based transaction reconciliation engine designed for multi-echelon repair networks holding expensive, slow-moving spare parts (e.g., turbine flow sensors, high-voltage inverters, hydraulic servo valves, optical gyroscopes).

In industrial maintenance networks, system-recorded inventory and physical stock frequently diverge. Standard enterprise systems merely flag the variance ($System - Physical \ne 0$) and demand costly manual cycle counts. **SpareSync** shifts the paradigm from simple discrepancy detection to automated root-cause investigation by analyzing the chronological stream of receipts, picks, transfers, and status logs to explain *why* the discrepancy occurred and recommend the most effective recovery action.

---

## 2. Business Problem

Repair networks face unique inventory synchronization challenges:
- **Unconfirmed Inter-Location Transfers:** Parts are dispatched from a source hub (`TRANSFER_OUT`) but never receipt-confirmed (`TRANSFER_IN`) at the destination hub.
- **Duplicate Barcode / System Scans:** Technicians accidentally scan the same delivery docket twice within minutes, artificially inflating system stock.
- **Network Synchronization Failures:** Edge handheld terminals record consumption picks during router/network outages, caching transactions in `PENDING_SYNC` status while the central ledger remains unaware.
- **Timestamp & Sequence Anomalies:** NTP clock drift on warehouse scanners causes receipts to be timestamped after subsequent pick events.
- **Clerical Count Errors:** Auditors transcribe manual count sheets incorrectly.

---

## 3. Key Features

- **Automated Root-Cause Diagnostic Engine:** Evaluates transaction streams against explainable rule routines.
- **Chronological Sequence Analysis:** Replays events in causal order to isolate the exact point of divergence.
- **Fact-Based Evidence Generation:** Supplies itemized transaction IDs, timestamps, and transfer tags supporting every diagnostic finding.
- **Transparent Confidence Scoring:** Computes deterministic confidence ratings (High / Medium) based on matching evidence strength.
- **Operational Decision Trade-Off Analysis:** Exposes multi-criteria trade-offs (**Cost, Time, Emissions, Reliability**) for every recommended recovery action.
- **Interactive Failure Simulation Sandbox:** Interactively injects and demonstrates supply chain failure modes with before/after state transitions.
- **Operational Resilience & Fallback Layer:** Edge SQLite store-and-forward queueing during network outages and manual fallback data entry for scanner/sensor failures.
- **Quantitative Benchmark & Evaluation Framework:** Dynamically calculates Explanation Accuracy, Unexplained Variance Reduction, and computational latency against ground-truth labels.
- **Interactive Operations Dashboard:** Built with Streamlit and Plotly for high-visibility management reporting, transaction inspection, trade-off analysis, and comparative evaluation.

---

## 4. System Architecture

```
sparesync/
│
├── app.py                      # Multi-section Streamlit operations dashboard (6 pages)
├── requirements.txt            # Project dependencies
├── README.md                   # System documentation
│
├── data/
│   ├── transactions.csv        # 300+ synthetic transactions with failure cases
│   ├── physical_counts.csv     # Physical inventory count audit records
│   └── offline_queue.db        # Local SQLite queue for store-and-forward persistence
│
├── src/
│   ├── __init__.py             # Package initializer
│   ├── data_generator.py       # Reproducible data generator (seed=42)
│   ├── baseline.py             # Naive variance calculator (benchmark)
│   ├── reconciliation_engine.py# Rule-based diagnostic reconciliation engine
│   ├── failure_simulator.py    # Controlled failure scenario simulation routines
│   ├── fallback_handler.py     # Store-and-forward queue & manual fallback handler
│   ├── metrics.py              # Quantitative evaluation & benchmarking engine
│   └── tradeoffs.py            # Multi-criteria operational decision trade-off module
│
├── tests/
│   ├── __init__.py
│   ├── test_baseline.py        # Pytest suite for baseline calculation
│   ├── test_reconciliation.py  # Pytest suite for diagnostic rules
│   ├── test_failure_simulation.py # Pytest suite for failure state simulations
│   ├── test_fallback.py        # Pytest suite for store-and-forward & manual fallback
│   ├── test_metrics.py         # Pytest suite for evaluation metrics & formulas
│   └── test_tradeoffs.py       # Pytest suite for decision trade-off scoring
│
└── docs/
    └── evaluation_report.md    # Detailed experimental evaluation & benchmark report
```

---

## 5. Decision Trade-Off Analysis

For each recommended recovery action, SpareSync evaluates the multi-criteria trade-offs across four operational dimensions:
1. **Financial Cost:** Labor, freight, or clerical expenditures required.
2. **Resolution Time:** Duration to execute the recovery action and verify stock.
3. **Carbon Emissions:** Environmental footprint associated with logistics/transport.
4. **Audit Reliability:** Likelihood that the recovery action produces permanent reconciliation.

### Recovery Actions Multi-Criteria Matrix

| Recovery Action Alternative | Cost | Time | Carbon Emissions | Audit Reliability | Description |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Manual Physical Recount** | Low | High | Low | High | Deploy warehouse personnel to perform an independent blind recount of shelf bin locations. |
| **Investigate Transaction History** | Low | Medium | Low | High | Audit ERP logs, delivery dockets, and duplicate barcode scans to isolate clerical discrepancies. |
| **Wait for Pending Synchronization** | Low | Low | Low | Very High | Allow edge handheld terminal network queue to flush automatically upon gateway reconnection. |
| **Contact Destination Warehouse** | Low | Medium | Low | High | Initiate inter-hub logistics inquiry to confirm receipt and log missing `TRANSFER_IN` entry. |
| **Emergency Replacement Shipment** | High | Low | High | High | Dispatch expedited air freight replacement directly from OEM supplier to prevent repair downtime. |

> ⚠️ **Disclaimer:** *Prototype decision-support estimates for comparison purposes.*

---

## 6. Baseline vs. SpareSync Comparison

| Capability | Baseline Auditor | SpareSync Engine |
| :--- | :---: | :---: |
| **Calculate System Stock** | Yes | Yes |
| **Detect Inventory Variance** | Yes | Yes |
| **Explain Root Cause** | No | **Yes** |
| **Analyse Chronological Stream** | No | **Yes** |
| **Detect Missing Events** | No | **Yes** |
| **Detect Duplicate Events** | No | **Yes** |
| **Identify Network Sync Failures** | No | **Yes** |
| **Identify Out-of-Order Timestamps** | No | **Yes** |
| **Provide Factual Audit Evidence** | No | **Yes** |
| **Assign Confidence Ratings** | No | **Yes** |
| **Expose Decision Trade-Offs (Cost, Time, Emissions, Reliability)** | No | **Yes** |
| **Simulate Supply Chain Failures** | No | **Yes** |
| **Support Offline Store-and-Forward** | No | **Yes** |
| **Manual Fallback Workflows** | No | **Yes** |

---

## 7. Measured Evaluation Results

*Measured on the 341-transaction synthetic dataset:*

- **Baseline Unexplained Variance Rate:** `100.0%`
- **SpareSync Unexplained Variance Rate:** `20.0%`
- **Unexplained Variance Reduction:** `80.0%`
- **Explanation Accuracy:** `80.0%`
- **Average Processing Latency:** `< 100 ms`

For the complete technical breakdown, see [docs/evaluation_report.md](file:///Users/larisha/COE%20Project/docs/evaluation_report.md).

---

## 8. Installation & Quick Start

### Prerequisites
- Python 3.10+ (Tested on Python 3.11 / 3.13)
- `pip` package manager

### Step 1: Clone or Navigate to Directory
```bash
cd "COE Project"
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run Test Suite
```bash
pytest -v tests/
```

### Step 4: Launch the Streamlit Dashboard
```bash
streamlit run app.py
```

The application will launch locally at `http://localhost:8501`.

---

## 9. Dashboard Walkthrough

The Streamlit dashboard is organized into six interactive sections:

1. **📊 Dashboard:**
   - Top-level operational KPIs (Total Transactions, Monitored Parts, Variance Cases Detected, Issues Explained).
   - Plotly visualizations: Root cause distribution donut chart and transaction volume by repair hub.
   - Comprehensive network audit status table.

2. **🔍 Reconciliation:**
   - Select any spare part (e.g., `SP-001` Turbine Flow Sensor) and hub location (Chennai, Bangalore, Mumbai).
   - Side-by-side comparison of System Stock vs. Audited Physical Stock with delta highlighting.
   - Root-cause callout banner, diagnostic confidence score, itemized evidence drawer, and recommended recovery action.
   - **Operational Trade-Off Analysis:** Real-time multi-criteria scorecard (Cost, Time, Emissions, Reliability), comparative Plotly grouped bar chart, and full decision matrix.
   - Localized transaction stream table for historical context.

3. **📋 Transaction Explorer:**
   - Multi-criteria filterable table (by Part ID, Location, Event Type, Sync Status).
   - Free-text search bar.
   - One-click CSV export of filtered transaction records.

4. **🧪 Failure Simulation:**
   - Interactive sandbox demonstrating 4 failure scenarios (Missing Transfer, Duplicate Receipt, Network Failure, Timestamp Inversion).
   - Clearly isolates **Normal State**, **Failure State**, **System Detection** (with status badges: `Detected`, `Explained`, `Action Required`), and **Recommended Recovery**.

5. **🛡️ Operational Fallback:**
   - **Section A (Network Outage & Store-and-Forward):** Simulates edge offline queueing and one-click restoration/sync.
   - **Section B (Manual Fallback Entry):** Structured forms for manual transaction entry during hardware breakdowns with `MANUAL_PENDING_VERIFICATION` status.

6. **⚖️ Baseline Comparison:**
   - Feature comparison matrix between Baseline and SpareSync.
   - KPI metrics: Baseline Unexplained Rate, SpareSync Unexplained Rate, Variance Reduction, and Explanation Accuracy.
   - Plotly comparative bar and resolution distribution charts.
   - Comprehensive Error Analysis and Limitations section.

---

## 10. Operational Resilience and Fallback

SpareSync includes dedicated fallback mechanisms (`src/fallback_handler.py`) to ensure business continuity during technology outages:

```
[Event Triggered]
       │
       ▼
[Network Check] ──(Offline)──► [Edge SQLite Queue] ──► Status: PENDING_SYNC
       │                              │
    (Online)                     (Restored)
       │                              │
       ▼                              ▼
[Central Database] ◄────────── [Queue Synchronizer] ──► Status: SYNCED
```

---

## 11. Current Progress – Review 1 (~35% Scope)

### ✅ Completed in Review 1:
- Problem analysis and stakeholder requirement mapping for repair networks.
- Synthetic dataset generation (300+ realistic multi-location transactions with controlled failure injections).
- Baseline variance computation engine (`baseline.py`).
- Rule-based reconciliation engine with 4 core anomaly rules (`reconciliation_engine.py`).
- Operational decision trade-off analysis framework (`tradeoffs.py`).
- Interactive failure simulation sandbox with 4 dedicated scenarios (`failure_simulator.py`).
- Operational fallback module with SQLite store-and-forward and manual fallback (`fallback_handler.py`).
- Evaluation and benchmarking framework (`metrics.py`).
- Automated Pytest test suite with 22/22 tests passing.
- Streamlit interactive operations intelligence UI with 6 dedicated pages (`app.py`).

---

## 12. Limitations & Future Work

### Limitations:
- **Rule Rigidity:** Current reconciliation relies on deterministic heuristics; compound failure cases where multiple errors affect the same part concurrently may produce lower confidence.
- **Batch Processing:** Processes static snapshots from CSV/SQLite rather than live Kafka/MQTT streaming queues.

### Future Work (Review 2 & Final Implementation):
- **Machine Learning & Sequence Models:** Introduce Transformer / LSTM sequence models to learn normal transaction patterns and flag probabilistic anomalies without explicit manual rules.
- **Automated Ledger Self-Healing:** Implement write-back mechanisms to automatically post corrective journal entries upon supervisor authorization.
- **Real-Time IoT & RFID Integration:** Connect edge RFID readers and store-and-forward queue listeners.
- **Multi-Criteria Optimization:** Expand trade-off models to optimize dynamic warehouse stocking policies.
