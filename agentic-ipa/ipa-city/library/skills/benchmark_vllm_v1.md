# Benchmark vLLM Skill

This skill describes how to run a benchmark against a vLLM server using the `inference-perf` tool.

## Prerequisites
- `pdm` installed.
- Access to the `inference-perf` project directory.
- A running vLLM server.

## Process
Run the following command, adjusting the `base_url` and `load.stages` as needed:

```bash
pdm --project ../inference-perf run inference-perf \
  --server.type vllm \
  --server.base_url <VLLM_URL> \
  --data.type random \
  --load.type constant \
  --load.stages '[{"rate": 10, "duration": 60}]' \
  --api.streaming true
```
