# AIPA Formulas

This document describes the core formulas used in the Agentic Inference Profile Automation (AIPA) workflow.

## apply-manifest
Deploys a model server to the cluster using a generated manifest.

- **Action**: Runs `kubectl apply -f <manifest-path>`.
- **Worker**: Deployment Worker.
- **Labels**: `formula=apply-manifest`.

## wait-healthy
Wait for the deployed model server to be healthy and ready to accept traffic.

- **Action**: Runs `kubectl rollout status deployment/<name>` and checks the `/health` endpoint.
- **Worker**: Health Check Worker.
- **Labels**: `formula=wait-healthy`.

## run-benchmark
Executes a performance benchmark against a healthy model server.

- **Action**: Uses `pdm run inference-perf`.
- **Worker**: Benchmarking Worker.
- **Labels**: `formula=run-benchmark`.

## archive-results
Archives and indexes the results of a benchmark run.

- **Action**: Moves results to the storage bucket and updates the index.
- **Worker**: Archiving Worker.
- **Labels**: `formula=archive-results`.
