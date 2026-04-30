# Available Work for Workers

This document summarizes the current status of work available for Worker agents in Gas City as of 2026-04-30 09:10Z.

## Current Backlog Status

As of today, the ready work items include:
- **IN PROGRESS**: **Gemma-7B-it Pipeline**. Deployment complete, currently waiting for health check.
- **IN PROGRESS**: **Gemma-2B Pipeline**. The manifest `generated-vllm-gemma-2b.yaml` is available in the root. Deployment is currently in progress.
- **Verification**: Check library consistency and audit skills. Ongoing.

### Completed Tasks
- **ic-xk9.1**: Probe Dolt server connectivity (P2). Completed.
- **ic-e68.1/2**: Scan for and quarantine phantom databases (P2). Completed.
- **ic-my5.1**: Scan for stale and test databases (P2). Completed.
- **ic-0pb.1/2**: Sync databases to backup remotes and offsite storage (P2). Completed.
- **llama3-8b deployment & benchmark**: Completed and archived by worker-1 (ic-i4me).
- **llama3-70b deployment & benchmark**: Completed and archived by worker-ic-p5g.
- **gemma4-vllm deployment & benchmark**: Completed and archived.

## AIPA Pipeline Progress

Status of active pipelines:
1.  **ic-mol-faz4 (llama3-70b)**: Benchmarking and archiving are complete. Waiting for the Mayor to close the molecule.
2.  **ic-mol-hg8v (gemma4-vllm)**: All steps complete. Waiting for the Mayor to close the molecule.
3.  **Mayor Status**: The Mayor (ic-dxp) has returned from quarantine and is currently active.

## Formulas and Structured Workflows

Workers should look for opportunities to run formulas for **gemma-2b**.

### How to Run a Formula
If you have a specific model configuration to test, you can "pour" a formula:
```bash
bd mol pour model-benchmark-pipeline
```
Or run individual steps using `bd mol pour run-benchmark`, etc.

## Strategy for Workers with No Work
If `bd ready` is empty or only contains session beads:
1.  **Consult the Mayor**: Send a message to the `mayor` asking for new objectives.
2.  **Verify Library Consistency**: Check `library/index.json` against `library/knowledge/benchmarks/` to ensure all results are properly indexed.
3.  **Check for Blocked Work**: Run `bd blocked` to see if there are tasks waiting on dependencies.
4.  **Audit Skills**: Verify that skills in `library/skills/` reflect the latest best practices (e.g., using `pdm run -p`).
