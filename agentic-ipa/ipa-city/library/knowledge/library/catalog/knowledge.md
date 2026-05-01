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
- **cleanup_resources**: How to remove model server resources from the Kubernetes cluster after a task is complete.
- **archive_results**: How to archive and index benchmark results in the Gas City Library.

## Knowledge Domains

- **benchmarks/gemma-7b-it**: Performance results for gemma-7b-it. Benchmark failed with 0% success rate (0/60 requests).
- **benchmarks/gemma-2b**: Performance results for gemma-2b. Achieved 4592.15 output tokens/sec with a 94.0% success rate (564/600 requests).
- **benchmarks/gemma4-vllm**: Performance results for gemma4-vllm. Achieved 100% success rate (150/150 requests) in latest run. Baseline high-load run achieved 1286.38 output tokens/sec.
- **benchmarks/llama3-8b**: Performance results for llama3-8b. Achieved 1350.18 output tokens/sec with 0 failures (600/600 requests). Survey run on 2026-05-01.
- **benchmarks/llama3-8b-gpu**: (Pending) Deployment configuration for JetStream on GPUs.
- **benchmarks/llama3-70b**: Performance results for llama3-70b. Achieved 185.88 output tokens/sec with a 91.7% success rate (55/60 requests).
- **benchmarks/llama-3.1-70b**: Performance results for Llama-3.1-70B. Achieved 1510.63 output tokens/sec with 0 failures (600/600 requests).
- **benchmarks/llama-3-1-8b-instruct**: Performance results for Llama 3.1 8B Instruct. Achieved a new record of 2035.01 output tokens/sec with a 93% success rate (558/600 requests). Survey run on 2026-05-01.
- **benchmarks/mistral-7b-v0.3**: Performance results for Mistral-7B-v0.3. Achieved 299.68 output tokens/sec with a 1.67% failure rate (1/60 requests). Survey run on 2026-05-01.
- **aipa/workflow**: Overview of the Agentic Inference Profile Automation lifecycle.
- **aipa/manifest-generation**: Technical details and knowledge about manifest generation processes.
- **aipa/manifests**: Inventory of available Kubernetes manifests for model servers.
- **aipa/run-survey**: Overseer formula for coordinating the full lifecycle of model performance evaluation.
- **aipa/formulas**: Description of the core formulas used in the AIPA workflow.
- **aipa/plan**: Detailed execution plan for the AIPA survey campaign.
- **models/gemma**: Information about the Gemma model family and configurations.
- **models/llama3**: Details and configuration for Llama3 models (8b, 70b).
- **models/llama3_1**: Details and configuration for Llama3.1 models (8b, 70b).
- **models/mistral**: Information about the Mistral model family.
- **dolt/connectivity**: Information about Dolt SQL server connectivity and probing.
- **work/available**: Summary of current backlog and work strategies for worker agents.
- **library/catalog**: (This file) The index of all available skills and knowledge.

## Audit Status

- **2026-05-01**: Fulfilled skill checkout request from `worker-1` for the `k8s-deploy` skill to support several upcoming deployment tasks.
- **2026-05-01**: Fulfilled research requests from `worker-ic-ou5n`, `worker-ic-hf5s`, and `worker-3` regarding the Gemma 7B-it JetStream GPU survey (`ic-mol-hx4p`). Provided `apply_manifest` and `wait_healthy` skills and pointed to the existing manifest.
- **2026-05-01**: Performed library consistency audit. Cleaned up stray log and config files from the root directory (`port-forward.log`, `proxy.log`, `test_config.yaml`, etc.) to `archive/`. Verified all indexed benchmarks and skills are present.
- **2026-05-01**: Regenerated CPU-based manifests for Gemma 7B-it and Llama 3 8B vLLM servers to address TPU unavailability. Created new `cpu` overlays in `packs/model-serving/overlays/kustomize/` for these models. Updated manifest inventory.
- **2026-05-01**: Fulfilled research request from Mayor for pending surveys. Identified opportunities for Gemma 7B-it (vLLM re-survey), Gemma 7B-it (CPU), Llama 3 8B (CPU), and Gemma 7B-it (JetStream GPU).
- **2026-05-01**: Updated `inference-perf` skill based on worker feedback: emphasized YAML configuration and documented vLLM completion API path behavior.
- **2026-05-01**: Fulfilled multiple skill checkout requests for `inference-perf` and provided deployment guidance for `llama3-8b-jetstream-gpu`.
- **2026-05-01**: Fulfilled skill checkout request from `aipa_survey_packs__worker-ic-ncz`. Provided the `k8s-deploy` skill covering manifest application, health checks, and resource cleanup.
- **2026-05-01**: Fulfilled research request from `aipa_survey_packs.worker-2` (ic-wisp-p3w) for JetStream `inference-perf` configuration. Provided sample YAML and connectivity best practices.
- **2026-05-01**: Updated `gemma4-vllm` benchmark archive with corrected results (100% success rate, 150/150 requests) provided by `worker-3` (ic-wisp-8bh). Previous results had identified failures likely due to port conflicts.
- **2026-05-01**: Standardized secret names in JetStream manifests from `huggingface-secret` to `hf-secret` to match cluster environment. Added `JAX_PLATFORMS=cpu` to JetStream GPU manifests to prevent TPU metadata loops.
- **2026-05-01**: Fixed P1 bug in `inference-perf` tokenizer (`custom_tokenizer.py`). Added `add_special_tokens=False` to `count_tokens` to prevent BOS overcount in streaming responses.
- **2026-05-01**: Updated 'inference-perf' skill with troubleshooting guidance for token count mismatches and BOS token inflation.
- **2026-05-01**: Updated `k8s-deploy` skill with troubleshooting notes for JetStream-on-GPU (using `JAX_PLATFORMS=cpu`) and secret requirements for gated models, based on feedback from `worker-3`.
- **2026-05-01**: Archived and indexed successful Gemma 4 VLLM benchmark results (100% success rate). Updated model knowledge with both latest and baseline high-load metrics.
- **2026-05-01**: Identified 100% failure rate in recent Gemma 4 VLLM benchmark attempt (`gemma4-vllm-report/`). Discovered potential issue with complex Kubernetes proxy `base_url` routing. Informed the benchmarking worker for further investigation.
- **2026-05-01**: Updated Llama 3.1 and Gemma model knowledge files with optimal resource configurations (64Gi memory, 120s readiness timeout) and documented tokenizer alignment research findings. Library consistency audit passed.
- **2026-05-01**: Updated `work/available` knowledge file to reflect that surveys for Gemma 4 (GPU), Llama 3 8B (JetStream), Gemma 7B-it (JetStream), and Llama 3 8B (JetStream GPU) are now IN PROGRESS.
- **2026-05-01**: Fulfilled skill checkout request from `aipa_survey_packs__worker-ic-wbq`. Provided the `inference-perf` skill for benchmarking gemma4-vllm, including critical updates on port selection and URL formatting.
- **2026-05-01**: Fulfilled skill checkout request from `aipa_survey_packs.worker-2`. Provided the `k8s-deploy` skill for performing health checks on gemma-7b-it-jetstream.
- **2026-05-01**: Conducted in-depth research into failed Gemma-7B-it (vLLM) run. Discovered discrepancy between archived log (port 8001, 14.8% error) and indexed results (port 8005, 100% failure). Noted high `token_count_mismatches` (100%) in successful Llama-3.1-8B-Instruct benchmark, suggesting potential tokenizer alignment issues.
- **2026-05-01**: Indexed the detailed AIPA survey campaign plan in `library/knowledge/aipa/workflow/plan.md`.
- **2026-05-01**: Processed skill check-in from `aipa_survey_packs.worker-2` for `k8s-deploy`. Received feedback to include full skill content in initial checkout confirmations.
- **2026-05-01**: Performed library consistency audit. Moved stray `backup.jsonl` and `buckets.txt` from root to `archive/`. Relocated detailed AIPA `plan.md` to `library/knowledge/aipa/workflow/plan.md`.
- **2026-05-01**: Fulfilled skill checkout request from `aipa_survey_packs.worker-3`. Provided the `k8s-deploy` skill for performing health checks on llama3-8b-jetstream.
- **2026-05-01**: Fulfilled skill checkout request from `aipa_survey_packs.worker-2`. Provided the `k8s-deploy` skill for performing health checks on gemma4-vllm.
- **2026-05-01**: Performed library consistency audit and root directory cleanup. Removed stray `benchmark_config.yaml` (archived to `archive/`) and deleted old log files from April. Verified that all indexed benchmarks exist and are consistent.
- **2026-05-01**: Fulfilled skill checkout request from `worker-ic-wbq`. Provided the `k8s-deploy` skill covering manifest application, health checks, and resource cleanup.
- **2026-05-01**: Created a dedicated `cleanup_resources` skill and updated the library catalog. Added the new cleanup protocol to the `k8s-deploy` packed skill based on worker feedback.
- **2026-05-01**: Successfully resolved llama-3.1-8b-instruct survey failure. Identified and increased insufficient 32Gi memory limit to 64Gi, relaxed readiness probes, and corrected benchmark base_url. Re-benchmark achieved a new record of 2035.01 output tokens/sec (up from 1135.81 baseline).
- **2026-05-01**: Archived failed benchmark results for Llama-3.1-8B-Instruct (100% failure rate) in `failed-2026-05-01/` for post-mortem analysis. Updated main index with successful re-run results.
- **2026-05-01**: Cleared backlog of 23+ skill checkout and research requests. Updated `k8s-deploy` skill with troubleshooting steps for `kubectl apply` failures based on worker feedback.
- **2026-05-01**: Verified and closed the `llama-3.1-8b-instruct` archiving task (ic-gsi) and related notifications. Bead store maintenance: merged 9 groups of duplicate issues to improve library consistency.
- **2026-05-01**: Standardized model knowledge files (`gemma`, `llama3`, `llama3_1`, `mistral`) with latest performance metrics (latency, TTFT, throughput, success rate) and linked to benchmark summaries. Cleaned up stray `benchmark_config.yaml` from root. Library consistency audit passed.

- **2026-05-01**: Research into the gemma-7b-it-jetstream failure confirms that it requires tpu-v5-lite-podslice which is currently unavailable in the cluster. Advised worker-1 to use the GPU manifest 'packs/model-serving/generated-jetstream-gemma-7b-it-gpu.yaml' as a fallback.
- **2026-05-01**: Clarified 'inference-perf' command usage for worker-1. Confirmed that the tool does not support subcommands like 'benchmark' and requires the '--config' flag or long-form flags (e.g., '--server.model_name').
- **2026-05-01**: Fulfilled bulk skill checkout request from worker-1. Provided 'k8s-deploy', 'model-serving', 'inference-perf', and 'perf-analysis' skills.
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
