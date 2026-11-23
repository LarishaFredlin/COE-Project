
# SpareSync - Database Schema Documentation

## 1. Introduction

SpareSync uses SQLite as its database management system for persistent storage of inventory discrepancy investigations.

The database stores investigation details, inventory quantities, diagnostic information, investigation status, notes, and timestamps.

## 2. Database Configuration

| Property | Details |
|---|---|
| Database system | SQLite |
| Database name | sparesync.db |
| Database directory | data/ |
| Main table | investigations |
| Connection library | Python sqlite3 |
| Row representation | sqlite3.Row |

The database file is located at:

`data/sparesync.db`

The database is initialized automatically when the FastAPI application starts.

## 3. Database Table: investigations

The investigations table stores inventory discrepancy investigation records.

### Table Structure

| Column | Data Type | Constraints | Description |
|---|---|---|---|
| id | INTEGER | Primary Key, AUTOINCREMENT | Internal record identifier |
| investigation_id | TEXT | UNIQUE, NOT NULL | Unique investigation identifier |
| part_id | TEXT | NOT NULL | Inventory part identifier |
| part_name | TEXT | Optional | Inventory part name |
| location | TEXT | NOT NULL | Inventory storage or repair location |
| system_stock | INTEGER | NOT NULL | Quantity recorded in the system |
| physical_stock | INTEGER | NOT NULL | Quantity physically available |
| variance | INTEGER | NOT NULL | Difference between system and physical stock |
| root_cause | TEXT | Optional | Identified cause of discrepancy |
| recommended_action | TEXT | Optional | Suggested corrective action |
| confidence | REAL | Optional | Diagnostic confidence value |
| status | TEXT | NOT NULL, DEFAULT 'OPEN' | Current investigation status |
| notes | TEXT | Optional | Investigation notes |
| created_at | TEXT | NOT NULL | Investigation creation timestamp |
| updated_at | TEXT | NOT NULL | Last modification timestamp |

## 4. Primary Key and Constraints

### Primary Key

The `id` column is the primary key.

It uses SQLite AUTOINCREMENT to generate a unique internal numeric identifier for every record.

### Unique Constraint

The `investigation_id` column has a UNIQUE constraint to prevent duplicate investigation identifiers.

### NOT NULL Constraints

The following columns must contain values:

- investigation_id
- part_id
- location
- system_stock
- physical_stock
- variance
- status
- created_at
- updated_at

### Default Value

The status column has the default value:

`OPEN`

This status is assigned when an investigation is created without another status being specified.

## 5. Indexes

SpareSync creates two indexes to improve investigation lookup performance.

| Index Name | Column | Purpose |
|---|---|---|
| idx_investigations_part_id | part_id | Supports searches by inventory part |
| idx_investigations_status | status | Supports filtering by investigation status |

Both indexes are created using `CREATE INDEX IF NOT EXISTS`.

## 6. Data Relationships

The current investigation database implementation contains one main table.

There are no foreign-key relationships between investigation tables in the current schema.

The internal `id` is the database primary key, while `investigation_id` is the unique identifier used by the API and investigation service.

## 7. Variance Calculation

The variance represents the difference between the system stock and physical stock.

It is calculated using:

`Variance = System Stock - Physical Stock`

Example:

| Field | Value |
|---|---:|
| System Stock | 100 |
| Physical Stock | 95 |
| Variance | 5 |

A positive variance means the system records more stock than the physical count.

A negative variance means the physical count is greater than the system-recorded quantity.

A zero variance indicates that both quantities match.

The API creation schema calculates variance before the investigation record is stored.

## 8. Investigation Status Values

The API schema supports the following investigation statuses:

| Status | Description |
|---|---|
| OPEN | Investigation has been created |
| IN_PROGRESS | Investigation is being examined |
| RESOLVED | Investigation has been resolved |
| CLOSED | Investigation has been closed |
| ESCALATED | Investigation requires escalation |

The database column stores the status as TEXT.

## 9. Database Connection Management

Database operations are handled through `backend/database.py`.

The application provides two main functions:

### get_database_connection()

- Creates the SQLite database directory if required.
- Opens a database connection.
- Configures the connection timeout.
- Enables row access using column names.
- Enables SQLite foreign-key enforcement.

### get_db_connection()

This context manager manages database transactions.

Its responsibilities include:

- Committing successful transactions.
- Rolling back transactions when an exception occurs.
- Closing the connection after the operation.

This helps maintain database consistency.

## 10. Python Investigation Model

The `Investigation` dataclass in `backend/models.py` represents an investigation record in Python.

It contains the investigation fields stored in the database.

The `from_row()` class method converts a SQLite Row object into an Investigation object.

This separates database row handling from the investigation service logic.

## 11. Database Initialization

The `init_database()` function initializes the SpareSync database.

It performs the following operations:

1. Establishes a database connection.
2. Creates the investigations table if it does not already exist.
3. Creates the part_id index.
4. Creates the status index.
5. Commits the database initialization transaction.

The `CREATE TABLE IF NOT EXISTS` and `CREATE INDEX IF NOT EXISTS` statements allow initialization to run without recreating existing structures.

## 12. Database Testing

Database functionality is tested using pytest and temporary SQLite databases.

The database tests cover:

- Database initialization.
- Database connection creation.
- Row factory configuration.
- Transaction handling.
- Investigation model mapping.
- Investigation creation.
- Investigation retrieval.
- Investigation updates.
- Investigation deletion.

Temporary database files isolate tests from the actual application database.

## 13. Conclusion

The SpareSync database provides persistent storage for inventory discrepancy investigations.

SQLite offers a lightweight database solution suitable for the current project architecture.

The investigation table, constraints, indexes, connection management, and Python dataclass model provide the foundation for investigation record management through the FastAPI backend.
