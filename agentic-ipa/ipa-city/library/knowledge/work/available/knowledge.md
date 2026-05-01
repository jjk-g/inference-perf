# Available Work for Workers

This document summarizes the current status of work available for Worker agents in Gas City as of 2026-05-01.

## Current Backlog Status

As of today, the ready work items include:
- **Verification**: Library consistency audit and Mistral-7B-v0.3 survey archival complete (2026-05-01).
- **Librarian Status**: The Librarian is active, responsive, and has addressed all pending skill checkout and research requests.

### Completed Tasks
- **ic-xk9.1**: Probe Dolt server connectivity (P2). Completed.
- **ic-e68.1/2**: Scan for and quarantine phantom databases (P2). Completed.
- **ic-my5.1**: Scan for stale and test databases (P2). Completed.
- **ic-0pb.1/2**: Sync databases to backup remotes and offsite storage (P2). Completed.
- **gemma-2b deployment & benchmark**: Completed and archived.
- **llama3-8b deployment & benchmark**: Completed and archived by worker-1 (ic-i4me).
- **llama3-70b deployment & benchmark**: Completed and archived.
- **gemma4-vllm deployment & benchmark**: Completed and archived.
- **gemma-7b-it deployment & benchmark**: Completed and archived.
- **llama-3.1-8b-instruct deployment & benchmark**: Completed and archived.
- **llama-3.1-70b deployment & benchmark**: Completed and archived.

## AIPA Pipeline Progress

Status of active pipelines:
1.  **Gemma-2B**: Completed and archived.
2.  **Llama3-8B**: vLLM completed. **JetStream survey in progress** (ic-lwx1).
3.  **Llama3-70B**: Completed and archived.
4.  **Gemma4-VLLM**: Completed and archived.
5.  **Gemma-7B-it**: vLLM completed. **JetStream survey in progress** (ic-skij).
6.  **Llama-3.1-8B-Instruct**: Completed and archived.
7.  **Mistral-7B-v0.3**: Completed and archived.
8.  **Llama-3.1-70B**: Completed and archived.
9.  **Mayor Status**: The Mayor (ic-diz2) is active and overseeing city operations.

## Formulas and Structured Workflows

Workers should look for opportunities to run formulas for new model configurations as they become available.

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
