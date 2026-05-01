# Library Catalog

This knowledge file maintains a list of available skills and knowledge domains within the Gas City Library.

## Available Skills

- **apply_manifest**: How to deploy a model server using a generated Kubernetes manifest.
- **benchmark_vllm**: Instructions for benchmarking a vLLM server using `inference-perf`.
- **core.gc-work**: Finding, creating, claiming, and closing work items (beads) using the `bd` tool.
- **delegate_tasks**: How to delegate sub-tasks in the AIPA workflow using the `bd` tool.
- **dog-doctor-skill**: Comprehensive health checks on a Dolt SQL server.
- **dolt-backup**: Synchronizing Dolt databases to backup remotes.
- **general_worker**: The core workflow for finding, claiming, and finishing work using `bd`.
- **generate_manifest**: How to generate Kubernetes deployment manifests for model servers using Kustomize.
- **inference-perf**: General process for running inference performance tests using the `inference-perf` tool.
- **phantom-db-scan-skill**: Detecting and quarantining phantom Dolt databases.
- **stale-db-scan-skill**: Detecting and cleaning up stale or orphaned test databases.
- **wait_healthy**: How to wait for a deployed model server to be healthy and ready.
- **archive_results**: How to archive and index benchmark results in the Gas City Library.

## Knowledge Domains

- **benchmarks/gemma-7b-it**: Performance results for gemma-7b-it. Benchmark failed with 0% success rate (0/60 requests).
- **benchmarks/gemma-2b**: Performance results for gemma-2b. Achieved 4592.15 output tokens/sec with a 94.0% success rate (564/600 requests).
- **benchmarks/gemma4-vllm**: Performance results for gemma4-vllm. Achieved 6294.37 total tokens/sec with a 95.2% success rate (571/600 requests).
- **benchmarks/llama3-8b**: Performance results for llama3-8b. Achieved 1350.18 output tokens/sec with 0 failures (600/600 requests). Survey run on 2026-05-01.
- **benchmarks/llama3-8b-gpu**: (Pending) Deployment configuration for JetStream on GPUs.
- **benchmarks/llama3-70b**: Performance results for llama3-70b. Achieved 185.88 output tokens/sec with a 91.7% success rate (55/60 requests).
- **benchmarks/llama-3.1-70b**: Performance results for Llama-3.1-70B. Achieved 1510.63 output tokens/sec with 0 failures (600/600 requests).
- **benchmarks/llama-3-1-8b-instruct**: Performance results for Llama 3.1 8B Instruct. (Note: 2026-05-01 attempt failed due to pod termination; currently points to April 30th baseline of 1135.81 tokens/sec).
- **benchmarks/mistral-7b-v0.3**: Performance results for Mistral-7B-v0.3. Achieved 299.68 output tokens/sec with a 1.67% failure rate (1/60 requests). Survey run on 2026-05-01.
- **aipa/workflow**: Overview of the Agentic Inference Profile Automation lifecycle.
- **aipa/manifest-generation**: Technical details and knowledge about manifest generation processes.
- **aipa/manifests**: Inventory of available Kubernetes manifests for model servers.
- **aipa/run-survey**: Overseer formula for coordinating the full lifecycle of model performance evaluation.
- **aipa/formulas**: Description of the core formulas used in the AIPA workflow.
- **models/gemma**: Information about the Gemma model family and configurations.
- **models/llama3**: Details and configuration for Llama3 models (8b, 70b).
- **models/llama3_1**: Details and configuration for Llama3.1 models (8b, 70b).
- **models/mistral**: Information about the Mistral model family.
- **dolt/connectivity**: Information about Dolt SQL server connectivity and probing.
- **work/available**: Summary of current backlog and work strategies for worker agents.
- **library/catalog**: (This file) The index of all available skills and knowledge.

## Audit Status

- **2026-05-01**: Archived failed benchmark results for Llama-3.1-8B-Instruct (100% failure rate). Results stored in `library/knowledge/benchmarks/llama-3-1-8b-instruct/failed-2026-05-01/`. Worker notified of `inference-perf` CLI corrections. Analysis indicates pod termination during startup.

- **2026-05-01**: Performed library consistency audit. Verified that all indexed benchmarks exist and match the manifest inventory. Updated catalog with missing performance metrics for Gemma 2B, Gemma 7B-it, Llama 3 70B, and Llama 3.1 8B Instruct.
- **2026-05-01**: Provided updated `inference-perf` skill to `worker-1` with detailed `pdm` commands, connectivity tips (avoiding port 8001), and pointed to baseline benchmark results for comparison.
- **2026-05-01**: Performed library consistency audit. Cleaned up temporary `port-forward-*.log` files and stray benchmark configs from the root directory. Verified that failed results for Llama-3.1-8B-Instruct were correctly archived and cleared the redundant `results/` directory.
- **2026-05-01**: Updated `generate_manifest` skill based on worker feedback to clarify navigation into environment-specific subdirectories (e.g., `gke/`).
- **2026-05-01**: Standardized manifest filenames in `library/knowledge/manifests/` to follow the `generated-<server>-<model>.yaml` convention. Updated references in the library catalog and model knowledge files. Redundant manifests removed.
- **2026-05-01**: Updated `archive_results` skill with explicit instructions for cleaning up temporary `port-forward-*.log` files from the root directory.
- **2026-05-01**: Updated llama3-8b benchmark results with new high-performance run (1350.18 tokens/sec).
- **2026-05-01**: Updated llama-3.1-70b benchmark results with new high-performance run (1510.63 tokens/sec).
- **2026-05-01**: Archived new Mistral-7B-v0.3 benchmark results from latest survey. Updated catalog summary with new performance metrics (299.68 tokens/sec).
- **2026-04-30**: Backlog of 40+ research and skill checkout requests cleared. Standardized cleanup and manifest locations communicated to workers.
- **2026-04-30**: JetStream overlays for Llama-3-8B and Gemma-7B-it updated with GPU configuration (RTX 6000) and documentation corrected. *Note: Current 'cloud-tpu-images' lack CUDA support for JAX; benchmarking will fall back to CPU. vLLM is recommended for GPU environments until optimized images are available.*
- **2026-04-30**: Library consistency verified. All benchmarks (Gemma, Llama, Mistral) are indexed.
- **2026-04-30**: Skill audit complete. `benchmark_vllm` and `inference-perf` updated with port best practices (avoiding 8001).
- **2026-04-30**: Library updated with JetStream GPU manifest and manifest cleanup instructions added to `apply_manifest` skill.
- **2026-04-30**: Archived new vLLM benchmark results for Llama 3 8B and Gemma 7B-it, replacing older runs. All library indices are consistent.
- **2026-04-30**: Updated `generate_manifest` and `archive_results` skills with explicit permission for workers to write to the library when following these skills.
- **2026-04-30**: (Shift 16:00Z) All pending skill checkout and research requests fulfilled. `generate_manifest` skill updated with feedback regarding manifest regeneration. Root directory cleaned and stray benchmark results archived.
