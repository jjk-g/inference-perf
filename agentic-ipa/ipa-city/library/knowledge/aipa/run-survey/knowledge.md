# Run Survey Pipeline

The `run-survey` is an overseer formula used to coordinate the full lifecycle of model performance evaluation.

## Overview

- **Formula Name**: `run-survey`
- **Type**: Overseer (delegates to other workers)
- **Primary Goal**: Generate manifests, deploy models, run benchmarks, and analyze results.

## Steps

### 1. Delegate Manifest Generation (`delegate-generation`)
The overseer creates a task for a generation worker to produce the Kubernetes manifests.
- **Command**: `bd create "Generate manifest for {{model}}" --label formula=generate-manifest`
- **Requirement**: Wait for completion and record manifest path.

### 2. Delegate Deployment and Health Check (`delegate-deployment`)
Once the manifest is ready, the overseer delegates the deployment and the subsequent health check.
- **Commands**:
  ```bash
  bd create "Deploy {{model}}" --label formula=apply-manifest
  bd create "Health check {{model}}" --label formula=wait-healthy
  ```

### 3. Delegate Benchmarking (`delegate-benchmarking`)
Once the server is healthy, the overseer delegates the benchmarking task.
- **Command**: `bd create "Benchmark {{model}}" --label formula=run-benchmark`

### 4. Delegate Archiving (`delegate-archiving`)
Once benchmarking is complete, the results are archived and indexed.
- **Command**: `bd create "Archive results for {{model}}" --label formula=archive-results`

## Relevant Skills

- `delegate_tasks`: For performing the delegation steps.
- `generate_manifest`: To understand what the generation step entails.
- `apply_manifest`: To understand what the deployment step entails.
- `wait_healthy`: To understand what the health check step entails.
