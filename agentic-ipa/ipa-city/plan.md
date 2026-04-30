# Agentic Inference Profile Automation (AIPA)

This document outlines the end-to-end workflow for autonomous inference profiling using Gas City. The goal is to automate the lifecycle of deploying model servers, benchmarking them, and analyzing results to find optimal configurations.

## Workflow Overview

The AIPA workflow consists of four main phases executed by Gas City agents:

1.  **Generate Manifests**: Create K8s deployment manifests for specific model configurations (e.g., Gemma 4, vLLM).
2.  **Deploy & Validate**: Apply the manifests to a GKE cluster and wait for the serving endpoint to be healthy.
3.  **Benchmark**: Run performance tests (load generation) against the healthy endpoint.
4.  **Persist & Index**: Save raw results to a cloud storage bucket and index the metadata in a queryable store.

---

## Phase 1: Manifest Generation
*   **Pack**: `model-serving` (or imported Kustomize templates)
*   **Action**: The agent uses Kustomize overlays to generate a complete Kubernetes manifest.
*   **Output**: A YAML file ready for application (e.g., `vllm-gemma4-deployment.yaml`).

## Phase 2: Deployment & Health Check
*   **Pack**: `k8s-deploy` (Hypothetical)
*   *Task*: Apply the manifest and monitor rollout.
*   **Commands**:
    ```bash
    kubectl apply -f vllm-gemma4-deployment.yaml
    kubectl rollout status deployment/gemma4-vllm-deployment
    ```
*   **Validation**: The agent pings the health endpoint (e.g., `/health` or `/v1/models`) to ensure the server is ready to accept traffic.

## Phase 3: Benchmarking
*   **Pack**: `inference-perf` (Hypothetical)
*   *Task*: Run a load generator (e.g., standard benchmarking script or `ipa-cli`) against the model server.
*   **Parameters**: Batch size, prompt length, concurrency levels.
*   **Output**: JSON or CSV file containing latency, throughput, and error rate metrics.

## Phase 4: Persistence & Indexing
*   **Pack**: `perf-analysis` (Hypothetical)
*   *Task*: Save results and update the central index.

### Result Persistence
Raw benchmark results, generated manifests, and logs are uploaded to a Google Cloud Storage (GCS) bucket.
*   **Path Structure**: `gs://[BUCKET_NAME]/runs/[TIMESTAMP]-[MODEL_ID]-[CONFIG_HASH]/`

### Indexing Store
To allow easy querying of past runs, metadata about the run is inserted into an indexing store.
*   **Options**:
    *   **BigQuery**: Ideal for large-scale analysis and SQL queries.
    *   **Beads (Dolt)**: If using the default Gas City store, run metadata can be tracked as specialized beads in a Dolt database, allowing SQL queries over the run history.
*   **Indexed Fields**: Run ID, Timestamp, Model ID, Framework (vLLM/JetStream), QPS achieved, P99 Latency, Cost per request, GCS URI to raw results.

---

## Agent Autonomy & Self-Healing (Try-Verify-Fix)

To enable agents to improve the implementation and handle failures autonomously, formulas should be designed with a "Try-Verify-Fix" loop.

*   **Goal-Oriented Prompts**: Agents are instructed with the ultimate goal (e.g., "Deploy a working server") rather than just a static sequence of commands.
*   **Authorization to Modify**: Agents have permission to modify Kustomize templates, formulas, and configurations within the packs to resolve errors.
*   **Self-Correction**: If a command fails (e.g., `kustomize build` errors), the agent reads the error from the transcript, identifies the fix, applies it to the source files in the pack, and retries.

Example Formula Step:
```toml
[[steps]]
id = "generate-and-verify"
title = "Generate and Verify Manifest"
description = """
1. Attempt to generate the manifest using Kustomize.
2. If it fails, read the error, modify the Kustomize files in the pack to fix the error, and try again.
3. Once generated, run `kubectl apply --dry-run=client` to verify it is valid.
"""
```

---

## Multi-Pack Architecture

To implement this, Gas City uses a high-level **Orchestration Pack** (e.g., `aipa-survey`) that composes specialized packs.

### Component Packs

*   **`model-serving`**: (Created) Contains Kustomize templates and formulas for generating manifests.
*   **`k8s-deploy`**: (Hypothetical) Contains formulas for `kubectl apply`, rollout monitoring, and health check validation.
*   **`inference-perf`**: (Hypothetical) Contains formulas for running benchmarking tools (e.g., `ipa-cli`) against the endpoint.
*   **`perf-analysis`**: (Hypothetical) Contains formulas for uploading results to GCS and indexing metadata in BigQuery or Dolt/Beads.

### Orchestration Configuration (`pack.toml`)

```toml
[pack]
name = "aipa-survey"
schema = 2

[imports.serving]  source = "../model-serving"
[imports.deploy]   source = "../k8s-deploy"
[imports.perf]     source = "../inference-perf"
[imports.analysis] source = "../perf-analysis"
```

Agents assigned to the `aipa-survey` pack (like a `surveyor` agent) execute high-level formulas that chain these steps together, ensuring that data flows correctly from manifest generation all the way to the indexing store using the Task Store (Beads) as the communication medium.
