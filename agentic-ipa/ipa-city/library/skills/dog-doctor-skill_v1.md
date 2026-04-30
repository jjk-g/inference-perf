# Dog Doctor Skill (v1)

This skill describes how to perform comprehensive health checks on a Dolt SQL server.

## Prerequisites
- Dolt CLI installed.
- Access to the Dolt server (default host: 127.0.0.1, default port: 30085).
- Environment variables: `GC_DOLT_HOST`, `GC_DOLT_PORT`, `GC_DOLT_USER`, `GC_DOLT_PASSWORD`.

## Process

### 1. Connectivity Probe
Check basic server health and measure latency.
```bash
# Probing connectivity and timing it
time dolt --host "${GC_DOLT_HOST:-127.0.0.1}" --port "${GC_DOLT_PORT:-30085}" --user "${GC_DOLT_USER:-root}" --no-tls sql -q "SELECT active_branch()"
```
*Note: Use port 30085 in this environment unless overridden.*

### 2. Resource Inspection
Run SQL queries to check connection counts and identify orphaned databases.

- **Connection Count**:
  ```sql
  SELECT COUNT(*) FROM information_schema.PROCESSLIST;
  ```
  *Threshold: Warn if >= 40 connections (80% of 50).*

- **Orphan Database Detection**:
  ```sql
  SHOW DATABASES;
  ```
  Identify databases matching test patterns: `testdb_*`, `beads_t*`, `beads_pt*`, `doctest_*`, `doctortest_*`.

### 3. Reporting
Generate a summary report including:
- Server status (Healthy/Degraded/Unreachable)
- Measured Latency
- Connection Count & Utilization
- Orphan Database Count & Names
- Backup Freshness
