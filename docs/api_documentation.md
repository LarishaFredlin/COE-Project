
# SpareSync - API Documentation

## 1. Introduction

SpareSync provides a REST API for managing inventory discrepancy investigations. The API is developed using FastAPI and uses SQLite for persistent investigation storage.

The API supports creating, retrieving, updating, and deleting investigation records.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| FastAPI | REST API framework |
| Pydantic | Request validation and response schemas |
| SQLite | Persistent data storage |
| Uvicorn | ASGI server |
| HTTPX | Frontend API communication |

## 3. Base URL

When running locally:

`http://127.0.0.1:8000`

Interactive API documentation:

`http://127.0.0.1:8000/docs`

## 4. Available Endpoints

### 4.1 Root Endpoint

- **Method:** GET
- **URL:** `/`
- **Purpose:** Returns API welcome information and running status.

### 4.2 Health Check

- **Method:** GET
- **URL:** `/health`
- **Purpose:** Checks whether the API is running.

Example response:

```json
{
  "status": "healthy",
  "application": "SpareSync"
}
```

### 4.3 Create Investigation

- **Method:** POST
- **URL:** `/investigations/`
- **Success status:** 201 Created
- **Purpose:** Creates a new inventory discrepancy investigation.

Example request:

```json
{
  "part_id": "SP-001",
  "part_name": "Brake Assembly",
  "location": "Chennai Repair Hub",
  "system_stock": 100,
  "physical_stock": 95,
  "root_cause": "Missing transfer",
  "recommended_action": "Verify transfer records",
  "confidence": 0.85,
  "notes": "Investigation created through API"
}
```

The variance is calculated automatically:

`Variance = System Stock - Physical Stock`

For the example above, the variance is 5.

### 4.4 Retrieve All Investigations

- **Method:** GET
- **URL:** `/investigations/`
- **Success status:** 200 OK
- **Purpose:** Retrieves all stored investigation records.

The response is a JSON array of investigation objects.

### 4.5 Retrieve an Investigation

- **Method:** GET
- **URL:** `/investigations/{investigation_id}`
- **Success status:** 200 OK
- **Purpose:** Retrieves an investigation using its unique ID.

Example:

`/investigations/INV-9872A40CB0`

If the investigation does not exist, the API returns 404 Not Found.

### 4.6 Update Investigation

- **Method:** PUT
- **URL:** `/investigations/{investigation_id}`
- **Success status:** 200 OK
- **Purpose:** Updates investigation details.

Example request:

```json
{
  "status": "IN_PROGRESS",
  "notes": "Verification started"
}
```

Supported investigation statuses:

- OPEN
- IN_PROGRESS
- RESOLVED
- CLOSED
- ESCALATED

### 4.7 Delete Investigation

- **Method:** DELETE
- **URL:** `/investigations/{investigation_id}`
- **Success status:** 200 OK
- **Purpose:** Deletes an investigation record.

Example response:

```json
{
  "message": "Investigation deleted successfully.",
  "investigation_id": "INV-9872A40CB0"
}
```

If the investigation does not exist, the API returns 404 Not Found.

## 5. Data Validation

Pydantic schemas validate incoming API requests.

### Investigation Creation Validation

| Field | Validation |
|---|---|
| part_id | Required, 1–50 characters |
| part_name | Optional, maximum 150 characters |
| location | Required, 1–150 characters |
| system_stock | Required, non-negative integer |
| physical_stock | Required, non-negative integer |
| confidence | Optional, value between 0 and 1 |
| variance | Automatically calculated |

### Investigation Update Validation

The update request supports:

- root_cause
- recommended_action
- confidence
- status
- notes

Confidence must be between 0 and 1 when provided. Status must match one of the supported investigation statuses.

Invalid request data is rejected by FastAPI/Pydantic validation.

## 6. Response Data Structure

Investigation responses contain:

| Field | Description |
|---|---|
| investigation_id | Unique investigation identifier |
| part_id | Inventory part identifier |
| part_name | Inventory part name |
| location | Inventory location |
| system_stock | Recorded system stock |
| physical_stock | Actual physical stock |
| variance | Difference between system and physical stock |
| root_cause | Identified discrepancy cause |
| recommended_action | Suggested corrective action |
| confidence | Diagnostic confidence value |
| status | Current investigation status |
| notes | Investigation notes |
| created_at | Investigation creation timestamp |
| updated_at | Last update timestamp |

## 7. HTTP Status Codes

| Status Code | Meaning |
|---|---|
| 200 | Request completed successfully |
| 201 | Investigation created successfully |
| 404 | Investigation not found |
| 422 | Request validation failed |
| 500 | Internal server error |

## 8. Running the API Server

From the project root directory, execute:

```bash
python3 -m uvicorn backend.main:app --reload
```

The API server starts at:

`http://127.0.0.1:8000`

Open the interactive Swagger interface:

`http://127.0.0.1:8000/docs`

The Swagger interface allows users to inspect endpoints, submit requests, and view responses.

## 9. Frontend API Client

The frontend communicates with the FastAPI backend through:

`frontend/api_client.py`

The client provides the following functions:

- `check_api_health()` - Checks API availability.
- `get_investigations()` - Retrieves investigation records.
- `create_investigation(payload)` - Creates an investigation.
- `update_investigation(investigation_id, payload)` - Updates an investigation.
- `delete_investigation(investigation_id)` - Deletes an investigation.

The client uses HTTPX for HTTP communication and converts HTTP and connection errors into `APIClientError` exceptions.

The API base URL can be configured using the `SPARESYNC_API_URL` environment variable. If it is not configured, the default URL is `http://127.0.0.1:8000`.

## 10. Conclusion

The SpareSync REST API provides structured investigation management through FastAPI and SQLite.

Pydantic validation helps ensure that incoming investigation data follows the defined schema. The frontend API client provides a separate communication layer for interacting with the backend.

The interactive Swagger documentation supports API inspection and manual testing during development.
