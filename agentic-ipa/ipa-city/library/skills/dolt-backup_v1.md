# dolt-backup Skill (v1)

This skill provides instructions for synchronizing Dolt databases to backup remotes within the AIPA Gas City environment using the `bd` (beads) tool.

## Prerequisites
- `bd` CLI installed and initialized.
- Access to a backup destination (e.g., a filesystem path or a DoltHub repository URL).
- For DoltHub: `DOLT_REMOTE_USER` and `DOLT_REMOTE_PASSWORD` environment variables set.

## Steps

### 1. Initialize Backup Destination
If a backup destination hasn't been configured, initialize it:
```bash
# For filesystem backup
bd backup init /path/to/backup/directory

# For DoltHub backup
bd backup init https://doltremoteapi.dolthub.com/<user>/<repo>
```

### 2. Verify Backup Status
Check the current status and configuration:
```bash
bd backup status
```

### 3. Synchronize Database to Backup
Push the current state of the database to the configured backup remote:
```bash
bd backup sync
```

### 4. Verification
After the sync, verify the status again to ensure success:
```bash
bd backup status
```

## Troubleshooting
- **Connection Issues**: Run `bd dolt test` to ensure the local Dolt server is reachable.
- **Authentication**: Ensure `DOLT_REMOTE_USER` and `DOLT_REMOTE_PASSWORD` are correctly set for DoltHub.
- **Permissions**: Verify write permissions for filesystem-based backups.
