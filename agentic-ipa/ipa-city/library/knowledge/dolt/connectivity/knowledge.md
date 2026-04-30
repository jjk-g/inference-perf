# Knowledge: Dolt Server Connectivity Probing

## Overview
Dolt is the underlying version-controlled database for the `bd` (beads) issue tracking system in Gas City. Probing connectivity and measuring latency is essential for ensuring system health.

## Tools and Commands

### Primary Tool: `bd dolt`
The `bd` CLI provides built-in commands for managing and testing the Dolt server.

- **Connection Test**: `bd dolt test`
  Returns a success or failure message regarding the server connection.
- **Configuration & Status**: `bd dolt show`
  Displays the current database name, host, port, user, and mode, along with a connection check.
- **Server Status**: `bd dolt status`
  Shows whether the Dolt SQL server is running and its PID.

### Latency Measurement
Standard SQL tools can be used against the Dolt SQL server (default port `30085`).

```bash
# Using 'bd sql' to run a simple query and time it
time bd sql -c "SELECT 1"
```

## Environment Variables
The following environment variables influence Dolt's behavior in this environment:

- `GC_DOLT_PORT`: The port on which the Dolt server is expected to run (default: `30085`).
- `BEADS_DOLT_SERVER_PORT`: Overrides the default port.
- `BEADS_DOLT_AUTO_START`: If set to `1`, `bd` will attempt to start the server automatically (default: `0` in some contexts, but `bd` often auto-starts transparently).

## Connection Details
- **Default Host**: `127.0.0.1`
- **Default Port**: `30085`
- **Default User**: `root`
- **Database Name**: Typically matches the issue prefix or is named `beads`. Use `bd dolt show` to confirm.
