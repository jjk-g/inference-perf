---
name: inference-perf
description: Instructions for benchmarking model servers using the inference-perf tool.
---

# Inference Perf Skill

This skill describes how to run inference performance tests and benchmarks on model servers.

## Benchmark vLLM
Instructions for benchmarking a vLLM server.

### Process
1. **Prepare the environment**: Ensure `inference-perf` is available.
2. **Run the benchmark**:
   It is recommended to use a YAML configuration file for complex benchmarks.
   ```bash
   inference-perf benchmark --config <config-path>
   ```
   Alternatively, use structured CLI arguments:
   ```bash
   inference-perf benchmark --server.type vllm --server.base_url <server-url> --model <model-id>
   ```

### Important Connectivity & URL Rules
- **base_url**: When using `type: completion`, the `base_url` must **NOT** include the `/v1` suffix (e.g., use `http://localhost:8000` instead of `http://localhost:8000/v1`), as the tool automatically appends it. Including it will result in an invalid `/v1/v1/completions` path.
- **Port Forwarding**: If the model server is not directly reachable, use `kubectl port-forward`. Avoid using port `8001` (often used by `kubectl proxy`); prefer unique ports like `8002` or `8003`.

## General Inference Perf
General process for running inference performance tests.

### Process
1. **Configure targets**: Define the models and endpoints to test in a YAML file.
2. **Execute tests**: Run the `inference-perf` suite.
3. **Collect results**: Results are typically stored in the directory specified in the config (e.g., `./results`).
