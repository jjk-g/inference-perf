# Inference Performance Skill

This skill describes how to run inference performance tests against a model server using the `inference-perf` tool.

## Prerequisites
- `pdm` installed.
- Access to the `inference-perf` project directory.
- A running model server (e.g., vLLM).

## Process
The preferred method for running `inference-perf` is using a YAML configuration file.

1. **Create a configuration file** (e.g., `benchmark_config.yaml`). See the example below for the required structure.
2. **Run the benchmark**:
   ```bash
   pdm run -p ../inference-perf inference-perf --config benchmark_config.yaml
   ```

**Note on Connectivity**: If the model server is not directly reachable, use `kubectl port-forward` to map the service port to a local port. **Avoid using port 8001** as it is frequently in use; instead, use a unique port like `8002` or `8003`. 

**Warning on vLLM API Path**: When using `server.type: vllm` and `api.type: completion`, the `server.base_url` must **NOT** include the `/v1` suffix. The client automatically appends `/v1/completions` to the base URL. Including `/v1` in the base URL will result in an incorrect path like `/v1/v1/completions`.

## Troubleshooting

### Token Count Mismatches
If the benchmark report shows a high number of `token_count_mismatches`, especially for models like Llama 3.1:
- **BOS Token Inflation**: Ensure the client-side tokenizer is not adding BOS tokens to every streaming chunk during the count. This is a common issue with certain Llama tokenizer configurations in the `transformers` library.
- **Alignment Check**: If exact token alignment is not critical for your survey, you can set `tokenizer: null` in the configuration to bypass this check. This will use the server-reported `completion_tokens` count directly.

### Example Configuration (`benchmark_config.yaml`)
```yaml
server:
  type: vllm
  base_url: http://localhost:8002 # No /v1 suffix
  model_name: meta-llama/Meta-Llama-3.1-8B-Instruct
api:
  type: completion
  streaming: true
data:
  type: random
  input_distribution:
    min: 128
    max: 1024
    mean: 512
    type: uniform
  output_distribution:
    min: 16
    max: 256
    mean: 128
    type: uniform
load:
  type: constant
  stages:
  - rate: 10
    duration: 60
storage:
  local_storage:
    path: ./results
```

### Locating Results
The tool generates report files in the directory specified by `storage.local_storage.path`. To integrate with downstream tasks, ensure files like `summary_lifecycle_metrics.json` are preserved.

## Examples

### Running with a configuration file
```bash
pdm run -p ../inference-perf inference-perf --config benchmark_config.yaml
```
