# Phantom DB Scan Skill (v1)

This skill describes how to detect phantom Dolt databases that can crash the server.

## Overview
A phantom database is a directory in the Dolt data directory (default `.dolt-data/`) that has a `.dolt/` subdirectory but is missing the `noms/manifest` file.

## Process

### 0. Verify Data Directory
Before scanning, ensure the Dolt data directory exists.
```bash
# Check for common data directory locations
[ -d .dolt-data ] || [ -d .beads/dolt ] || echo "Warning: No Dolt data directory found."
```

### 1. Scan for Phantoms
List all directories in the data directory and check for the phantom condition. The data directory is typically `.dolt-data/` or `.beads/dolt/`.

```bash
# List directories
ls -d .beads/dolt/*/
```
# Sample command to check for manifests across all databases:
# ls -a .beads/dolt/*/.dolt/noms/manifest
# If a directory is missing the manifest, it's a phantom.
```

### 2. Quarantine (Removal)
Remove the corrupted directory to prevent server crashes.

```bash
rm -rf .beads/dolt/<phantom-name>
```
*Note: This is safe because phantom directories have no valid data.*

### 3. Reporting
Record and report:
- Total directories scanned
- Phantom databases found (names and paths)
- Valid databases found
- Phantoms quarantined
