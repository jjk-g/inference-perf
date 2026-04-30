# Available Work for Workers

This document summarizes the current status of work available for Worker agents in Gas City as of 2026-04-30.

## Current Backlog Status

As of today, the ready work items include:
- **ic-my5.1**: Scan for stale and test databases (P2). Infrastructure task to identify orphaned databases.
- **ic-e68.2**: Quarantine phantom databases (P2). Infrastructure task to remove corrupted database directories.
- **ic-0pb.2**: Sync backups to offsite storage (P2).

### Completed Tasks
- **ic-xk9.1**: Probe Dolt server connectivity (P2). Completed by worker-adhoc-5580185628. Server reachable on port 30085.
- **ic-e68.1**: Scan for phantom databases (P2). Completed.

## AIPA Pipeline Progress

Two `run-survey` pipelines are currently active:
1.  **ic-mol-faz4**: Manifest generation (ic-mol-m8id) is complete. Next step: Delegate Deployment (ic-mol-pq33).
2.  **ic-mol-hg8v**: Manifest generation (ic-mol-omp4) is complete. Next step: Delegate Deployment (ic-mol-a2kv).

## Formulas and Structured Workflows

Workers should look for opportunities to run formulas if no individual tasks are available. Formulas represent repeatable units of work in the AIPA (Agentic Inference Profile Automation) lifecycle.

### Available AIPA Formulas
1.  **generate-manifest**: Generate K8s deployment manifests for model servers.
2.  **apply-manifest**: Apply a generated K8s manifest to the cluster.
3.  **wait-healthy**: Wait for a deployment to become healthy.
4.  **run-benchmark**: Run inference performance tests.
5.  **archive-results**: Archive and index benchmark results.
6.  **model-benchmark-pipeline**: A meta-formula that orchestrates the above steps.

### How to Run a Formula
If you have a specific model configuration to test (e.g., from a request or a backlog item), you can "pour" a formula:
```bash
bd mol pour model-benchmark-pipeline
```

## Strategy for Workers with No Work
If `bd ready` is empty or only contains session beads:
1.  **Consult the Mayor**: Send a message to the `mayor` asking for new objectives or task generation.
2.  **Verify Manifests**: Check for existing `.yaml` manifests in the root directory and verify if they have been successfully deployed and benchmarked by checking `results.json`.
3.  **Check for Blocked Work**: Run `bd blocked` to see if there are tasks waiting on dependencies that you can help resolve.
4.  **Audit the Library**: Assist the Librarian by verifying that skills and knowledge files are accurate and up-to-date.
