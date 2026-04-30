# Benchmark vLLM Skill

This skill describes how to run a benchmark against a vLLM server using the `inference-perf` tool.

## Prerequisites
- `pdm` installed.
- Access to the `inference-perf` project directory.
- A running vLLM server.

## Process
Run the following command from the `ipa-city` root, adjusting the `--server.base_url` and load parameters as needed.

**Note on Connectivity**: If the model server is not directly reachable, use `kubectl port-forward` to map the service port to `localhost:8001` (or another local port).

```bash
pdm run -p ../inference-perf inference-perf \
  --server.type vllm \
  --server.base_url http://localhost:8001 \
  --data.type random \
  --data.input_distribution.min 128 \
  --data.input_distribution.max 1024 \
  --data.input_distribution.mean 512 \
  --data.input_distribution.type uniform \
  --data.output_distribution.min 16 \
  --data.output_distribution.max 256 \
  --data.output_distribution.mean 128 \
  --data.output_distribution.type uniform \
  --load.type constant \
  --load.stages '[{"rate": 10, "duration": 60}]' \
  --api.streaming true
```
