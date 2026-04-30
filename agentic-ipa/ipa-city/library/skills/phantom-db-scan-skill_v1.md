# Phantom DB Scan Skill (v1)

This skill describes how to detect phantom Dolt databases that can crash the server.

## Overview
A phantom database is a directory in the Dolt data directory (default `.dolt-data/`) that has a `.dolt/` subdirectory but is missing the `noms/manifest` file.

## Process

### 1. Scan for Phantoms
List all directories in the data directory and check for the phantom condition.

```bash
# List directories
ls -d .dolt-data/*/

# Check for phantom condition for each directory <dir>:
# If <dir>/.dolt/ exists AND <dir>/.dolt/noms/manifest does NOT exist:
# -> Phantom detected
```

### 2. Quarantine (Removal)
Remove the corrupted directory to prevent server crashes.

```bash
rm -rf .dolt-data/<phantom-name>
```
*Note: This is safe because phantom directories have no valid data.*

### 3. Reporting
Record and report:
- Total directories scanned
- Phantom databases found (names and paths)
- Valid databases found
- Phantoms quarantined
