# SpareSync - Testing Strategy

## 1. Introduction

SpareSync is an inventory transaction reconciliation and investigation management system. Testing is performed to verify the correctness, reliability, and stability of its reconciliation logic, database operations, REST API, and frontend API communication.

The project uses pytest as its primary testing framework.

## 2. Testing Objectives

The main objectives are:

- Verify the correctness of inventory reconciliation calculations.
- Validate stock quantities and input data before processing.
- Test transaction processing and baseline calculations.
- Verify the investigation management API operations.
- Ensure database operations work correctly.
- Test offline transaction handling and synchronization.
- Verify error handling for invalid requests and API connection failures.
- Prevent regressions when new features are introduced.

## 3. Testing Tools and Technologies

| Tool / Technology | Purpose |
|---|---|
| pytest | Automated test execution |
| FastAPI TestClient | Testing REST API endpoints |
| Pydantic | Input validation testing |
| SQLite | Database operation testing |
| httpx | HTTP communication and API-client testing |
| monkeypatch | Replacing dependencies during tests |
| Temporary databases | Isolating database tests |

## 4. Types of Testing

### 4.1 Unit Testing

Unit tests verify individual functions and modules independently.

The following project components are tested:

- Inventory baseline calculations.
- Reconciliation logic.
- Trade-off analysis.
- Performance metrics.
- Failure simulation.
- Offline fallback handling.
- Database operations.

### 4.2 API Testing

The FastAPI backend is tested using FastAPI TestClient.

The investigation API supports the following operations:

| HTTP Method | Endpoint | Purpose |
|---|---|---|
| POST | /investigations/ | Create an investigation |
| GET | /investigations/ | Retrieve all investigations |
| GET | /investigations/{id} | Retrieve a specific investigation |
| PUT | /investigations/{id} | Update an investigation |
| DELETE | /investigations/{id} | Delete an investigation |

API tests verify successful requests, response data, status codes, and missing investigation handling.

### 4.3 API Client Testing

The frontend API client is tested independently using mocked HTTP responses.

The tests cover:

- API health-check communication.
- Retrieving investigations.
- Creating investigations.
- Updating investigations.
- Deleting investigations.
- Handling HTTP errors.
- Handling connection failures.

Mocking HTTP requests allows the API client to be tested without depending on a running backend server.

### 4.4 Database Testing

Database tests use temporary SQLite databases to avoid modifying the actual application database.

The tests verify:

- Database initialization.
- Database connection handling.
- Row access using column names.
- Transaction commit and rollback behaviour.
- Investigation creation.
- Investigation retrieval.
- Investigation updates.
- Investigation deletion.
- Database model mapping.

### 4.5 Input Validation Testing

Pydantic schemas validate investigation data before it is processed.

Validation tests cover:

- Negative stock quantities.
- Invalid confidence values.
- Invalid investigation statuses.
- Correct variance calculation.
- Valid investigation creation.

Baseline validation tests also check missing required columns, invalid quantities, and unsupported event types.

### 4.6 Error Handling Testing

Error handling tests verify that invalid operations fail safely and return meaningful errors.

Examples include:

- Invalid investigation identifiers return HTTP 404.
- Invalid input values are rejected by validation.
- HTTP errors are converted into APIClientError exceptions.
- API connection failures produce a clear error message.
- Database operations use transaction rollback when an exception occurs.

## 5. Test Organization

Automated tests are maintained in the tests directory.

| Test File | Testing Area |
|---|---|
| test_reconciliation.py | Inventory reconciliation |
| test_baseline.py | Baseline calculations and validation |
| test_tradeoffs.py | Trade-off analysis |
| test_metrics.py | Performance metrics |
| test_failure_simulation.py | Failure simulation |
| test_fallback.py | Offline fallback and synchronization |
| test_database.py | SQLite database operations |
| test_api.py | FastAPI endpoints and schema validation |
| test_api_client.py | Frontend API client communication |

## 6. Test Isolation and Reliability

The project uses temporary databases for database-related tests.

The pytest tmp_path fixture provides a separate temporary location for test database files.

The monkeypatch fixture replaces database connections and HTTP request functions during tests.

This approach helps to:

- Prevent test data from affecting the actual application database.
- Avoid depending on an external API server during API-client tests.
- Make tests repeatable.
- Reduce dependencies between individual test cases.

## 7. Running the Tests

Run all automated tests from the project root directory:

```bash
python3 -m pytest -v