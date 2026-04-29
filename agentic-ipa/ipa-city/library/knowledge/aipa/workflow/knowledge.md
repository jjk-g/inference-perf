# AIPA Workflow Overview

The Agentic Inference Profile Automation (AIPA) workflow automates the lifecycle of:
1. Deploying model servers.
2. Benchmarking them.
3. Analyzing results to find optimal configurations.

## Main Phases

1.  **Generate Manifests**: Create K8s deployment manifests for specific model configurations (e.g., Gemma 4, vLLM) using Kustomize.
2.  **Deploy & Validate**: Apply the manifests to a GKE cluster and wait for the serving endpoint to be healthy.
3.  **Benchmark**: Run performance tests (load generation) against the healthy endpoint to collect metrics like latency, throughput, and error rate.
4.  **Persist & Index**: Save raw results to GCS and index metadata in a queryable store (BigQuery or Beads/Dolt).

## Multi-Pack Architecture

Gas City uses a high-level **Orchestration Pack** (e.g., `aipa-survey`) that composes specialized packs:
*   `model-serving`: Kustomize templates and formulas for generating manifests.
*   `k8s-deploy`: Formulas for deployment and health check validation.
*   `inference-perf`: Formulas for running benchmarking tools.
*   `perf-analysis`: Formulas for persistence and indexing.
