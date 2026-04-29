# Inference Performance Skill

This skill describes how to run inference performance tests against a model server using the `inference-perf` tool.

## Prerequisites
- `pdm` installed.
- Access to the `inference-perf` project directory.
- A running model server (e.g., vLLM).

## Process
Run the following command from the `ipa-city` root, adjusting the `--server.base_url` and load parameters as needed.

```bash
pdm --project ../inference-perf run inference-perf \
  --server.type vllm \
  --server.base_url http://localhost:8000 \
  --data.type random \
  --load.type constant \
  --load.stages '[{"rate": 10, "duration": 60}]' \
  --api.streaming true
```

### Locating Results
The tool generates a report file. Look for a `reports/` directory or a new JSON file in the current directory. To integrate with downstream tasks, rename or copy the result to `results.json`.
