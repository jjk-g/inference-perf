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
   ```bash
   inference-perf benchmark --model <model-id> --url <server-url>
   ```
   Example:
   ```bash
   inference-perf benchmark --model gemma-7b-it --url http://localhost:8000/v1
   ```

## General Inference Perf
General process for running inference performance tests.

### Process
1. **Configure targets**: Define the models and endpoints to test.
2. **Execute tests**: Run the `inference-perf` suite.
3. **Collect results**: Results are typically stored in JSON format for analysis.
