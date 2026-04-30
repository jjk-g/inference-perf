# Stale DB Scan Skill (v1)

This skill describes how to detect and clean up stale or orphaned test databases in a Dolt server.

## Process

### 1. Query Databases
Query the Dolt server to list all databases.

```sql
SHOW DATABASES;
```
*Note: Filter out Dolt internals (information_schema, mysql, dolt_cluster, __gc_probe).*

### 2. Classify Orphans
Identify databases matching known test or orphan patterns:
- `testdb_*`
- `beads_t*`
- `beads_pt*`
- `beads_vr*`
- `doctest_*`
- `doctortest_*`

### 3. Cleanup
If the orphan count is manageable (<= 50), clean up via SQL.

```sql
DROP DATABASE IF EXISTS `<orphan_name>`;
```

If the count is excessive (> 50), use the `gc dolt cleanup` command:
```bash
gc dolt cleanup --force --max <count>
```

### 4. Reporting
Generate a summary report including:
- Total databases
- Production databases (those referenced by rig registry)
- Orphan databases found
- Orphans removed
- Orphans remaining
