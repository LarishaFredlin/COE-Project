# SpareSync – Inventory Transaction Reconciliation Engine

> **Operational Intelligence for Multi-Hub Spare Parts Repair Networks**

## 1. Project Overview

**SpareSync** is an inventory transaction reconciliation and investigation management system designed for multi-location spare parts repair networks.

The system identifies discrepancies between system-recorded inventory and physical stock. It analyzes chronological transaction records, detects potential operational failures, generates evidence-based root-cause explanations, and recommends recovery actions.

SpareSync combines rule-based diagnostics, operational decision support, failure simulation, offline transaction handling, and persistent investigation management.

## 2. Business Problem

Multi-location repair networks face several inventory synchronization challenges:

- **Unconfirmed Inter-Location Transfers:** Parts are dispatched from a source location but the destination receipt is not recorded.
- **Duplicate Transactions:** Repeated scans can artificially increase system-recorded stock.
- **Network Synchronization Failures:** Transactions recorded during network outages may remain pending synchronization.
- **Timestamp Anomalies:** Incorrect timestamps can cause transaction events to appear in the wrong chronological order.
- **Physical Count Discrepancies:** Manual counting and data-entry errors can create differences between recorded and actual stock.

Traditional inventory systems identify stock differences but may not explain the operational events responsible for them.

SpareSync addresses this limitation through transaction analysis and evidence-based diagnostics.

## 3. Key Features

### Inventory Reconciliation
- Calculates system stock and compares it with physical inventory.
- Identifies inventory discrepancies.
- Analyzes chronological transaction sequences.

### Advanced Diagnostics
- Uses transparent, rule-based diagnostic logic.
- Prioritizes potential root causes.
- Provides supporting transaction evidence and confidence information.

### Investigation Workbench
- Provides an interface for investigating discrepancy cases.
- Displays diagnostic evidence and recommended actions.
- Supports investigation status and notes.

### Data Quality and Audit
- Validates transaction data.
- Identifies data quality issues.
- Supports audit-oriented analysis.

### Scenario Planner
- Supports what-if inventory adjustment analysis.
- Helps evaluate possible changes without modifying original source data.

### Operational Decision Support
- Compares recovery alternatives using cost, time, emissions, and reliability.
- Provides information to support operational decisions.

### Failure Simulation
- Simulates missing transfers, duplicate receipts, network failures, and timestamp anomalies.
- Demonstrates how the reconciliation engine responds to different failure scenarios.

### Operational Resilience
- Uses SQLite-based offline transaction queueing.
- Supports store-and-forward synchronization.
- Provides manual fallback transaction entry.

### FastAPI Investigation Backend
- Provides REST API endpoints for investigation management.
- Supports creating, retrieving, updating, and deleting investigations.
- Uses Pydantic schemas for request validation.
- Stores investigation records in SQLite.

### Automated Testing
- Uses pytest to validate core modules, database operations, API endpoints, and frontend API client behavior.

## 4. Technology Stack

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Frontend | Streamlit |
| API Framework | FastAPI |
| API Client | HTTPX |
| Database | SQLite |
| Data Processing | Pandas |
| Visualizations | Plotly |
| Data Validation | Pydantic |
| Testing | Pytest |
| Development Environment | Visual Studio Code |

## 5. System Architecture

SpareSync follows a modular architecture consisting of the following components:

1. **Presentation Layer:** Streamlit application.
2. **Processing Layer:** Inventory reconciliation, diagnostics, metrics, trade-offs, and simulation modules.
3. **API Layer:** FastAPI endpoints for investigation management.
4. **Service Layer:** Investigation business logic and CRUD operations.
5. **Database Layer:** SQLite persistent investigation storage.

The FastAPI backend and Streamlit application are currently maintained as separate components. The frontend API client is available, and complete integration with the main Streamlit application remains part of the final development work.

For more details, see [System Architecture](docs/architecture.md).

## 6. Project Directory Structure

```text
COE Project/
│
├── app.py
├── requirements.txt
├── README.md
├── pytest.ini
├── .gitignore
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── investigations.py
│   └── services/
│       ├── __init__.py
│       └── investigation_service.py
│
├── frontend/
│   └── api_client.py
│
├── src/
│   ├── __init__.py
│   ├── data_generator.py
│   ├── baseline.py
│   ├── reconciliation_engine.py
│   ├── failure_simulator.py
│   ├── fallback_handler.py
│   ├── metrics.py
│   └── tradeoffs.py
│
├── tests/
│   ├── __init__.py
│   ├── test_baseline.py
│   ├── test_reconciliation.py
│   ├── test_failure_simulation.py
│   ├── test_fallback.py
│   ├── test_metrics.py
│   ├── test_tradeoffs.py
│   ├── test_api.py
│   ├── test_database.py
│   └── test_api_client.py
│
├── data/
│   ├── transactions.csv
│   ├── physical_counts.csv
│   ├── offline_queue.db
│   └── sparesync.db
│
├── docs/
│   ├── architecture.md
│   ├── api_documentation.md
│   ├── database_schema.md
│   ├── testing_strategy.md
│   └── evaluation_report.md
│
└── assets/
```

## 7. Investigation Management API

The backend is implemented using FastAPI.

**Base URL:**

```text
http://127.0.0.1:8000
```

### Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API welcome information |
| GET | `/health` | API health check |
| POST | `/investigations/` | Create an investigation |
| GET | `/investigations/` | Retrieve all investigations |
| GET | `/investigations/{investigation_id}` | Retrieve one investigation |
| PUT | `/investigations/{investigation_id}` | Update an investigation |
| DELETE | `/investigations/{investigation_id}` | Delete an investigation |

### Example Investigation Request

```json
{
  "part_id": "SP-001",
  "part_name": "Turbine Flow Sensor",
  "location": "Chennai",
  "system_stock": 50,
  "physical_stock": 45,
  "root_cause": "Missing transfer confirmation",
  "recommended_action": "Verify destination receipt",
  "confidence": 0.92,
  "notes": "Investigation initiated"
}
```

The API calculates the inventory variance during investigation creation.

**Variance = System Stock - Physical Stock**

Interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

For complete endpoint details, request examples, and response structures, see [API Documentation](docs/api_documentation.md).

## 8. Database Design

SpareSync uses SQLite for persistent investigation management.

The primary database is:

```text
data/sparesync.db
```

The `investigations` table stores:

- Investigation ID
- Part ID and part name
- Location
- System stock and physical stock
- Inventory variance
- Root cause
- Recommended action
- Confidence score
- Investigation status
- Notes
- Creation and update timestamps

A separate database, `data/offline_queue.db`, supports offline transaction storage and synchronization.

For complete database details, see [Database Schema](docs/database_schema.md).

## 9. Testing and Reliability

SpareSync uses pytest for automated testing.

The test suite covers:

- Inventory reconciliation.
- Baseline calculations and input validation.
- Trade-off analysis.
- Metrics.
- Failure simulation.
- Offline fallback and synchronization.
- Database initialization and CRUD operations.
- FastAPI endpoint behavior.
- Frontend API client behavior.
- HTTP and connection error handling.

### Latest Verified Test Result

- **Total tests passed:** 52
- **Failed tests:** 0

Run the complete test suite using:

```bash
pytest -v tests/
```

For testing methodology, coverage areas, and known limitations, see [Testing Strategy](docs/testing_strategy.md).

## 10. Installation and Quick Start

### Prerequisites

- Python 3.10 or later
- pip package manager
- Visual Studio Code (recommended)

### Step 1: Navigate to the Project

```bash
cd "COE Project"
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run Automated Tests

```bash
pytest -v tests/
```

### Step 4: Start the Streamlit Application

```bash
streamlit run app.py
```

The Streamlit application will be available at:

```text
http://localhost:8501
```

### Step 5: Start the FastAPI Backend

Open a separate terminal in the project directory and run:

```bash
python3 -m uvicorn backend.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

The API and Streamlit application run as separate processes.

## 11. Documentation

Additional technical documentation is available in the `docs/` directory.

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System components and architecture |
| [API Documentation](docs/api_documentation.md) | REST API endpoints and request/response details |
| [Database Schema](docs/database_schema.md) | SQLite database structure |
| [Testing Strategy](docs/testing_strategy.md) | Testing approach and validation |
| [Evaluation Report](docs/evaluation_report.md) | Experimental evaluation and benchmarking |

## 12. Limitations and Future Enhancements

### Current Limitations

- The diagnostic engine uses deterministic rule-based logic.
- Transaction processing is primarily based on stored datasets rather than live streaming.
- Complete Streamlit-to-FastAPI integration is still pending.
- Authentication and authorization have not yet been implemented.
- API load testing and comprehensive test coverage measurement remain future validation tasks.

### Future Enhancements

- Complete integration of the Streamlit frontend with the FastAPI backend.
- Persistent investigation management through the Investigation Workbench.
- Authentication and role-based access control.
- Expanded diagnostic rules and advanced anomaly detection.
- Live transaction ingestion and IoT integration.
- API performance and load testing.

## 13. Conclusion

SpareSync combines inventory reconciliation, evidence-based diagnostics, operational decision support, failure simulation, and offline transaction handling into a modular application.

The addition of FastAPI and SQLite-based investigation management establishes a foundation for persistent investigation workflows and future frontend integration.

The project aims to improve inventory discrepancy analysis, investigation traceability, and operational decision-making in multi-location spare parts repair networks.
