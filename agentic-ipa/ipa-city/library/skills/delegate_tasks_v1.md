# Delegate Tasks Skill

This skill describes how to delegate sub-tasks in the AIPA workflow using the `bd` tool.

## Prerequisites
- `bd` tool installed and initialized.

## Process
When a master task requires sub-tasks (e.g., health check after deployment), use `bd create` with the appropriate formula label.

### Deployment and Health Check
To delegate deployment and its subsequent health check:
```bash
bd create "Deploy <model-name>" --label formula=apply-manifest
bd create "Health check <model-name>" --label formula=wait-healthy
```

### Benchmarking
To delegate a benchmark run once the server is healthy:
```bash
bd create "Benchmark <model-name> - <description>" --label formula=run-benchmark
```

### Archiving
To delegate result archiving:
```bash
bd create "Archive results for <model-name>" --label formula=archive-results
```
