# Llama-3.1 Models

## Llama-3.1-8B-Instruct

- **Model ID**: `meta-llama/Meta-Llama-3.1-8B-Instruct`
- **vLLM Overlay**: `packs/model-serving/overlays/kustomize/vllm/llama-3.1-8b-instruct`
- **Status**: Benchmark Complete (Baseline)
- **Metrics**:
  - Request Latency (Mean): 14.38s
  - Time to First Token (Mean): 7.94s
  - Throughput (Output Tokens/sec): 1135.81
  - Success Rate: 88.5% (531/600 requests)
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/llama-3-1-8b-instruct/summary_lifecycle_metrics.json)

## Llama-3.1-70B

- **Model ID**: `meta-llama/Meta-Llama-3.1-70B-Instruct`
- **vLLM Overlay**: `packs/model-serving/overlays/kustomize/vllm/llama-3.1-70b`
- **Status**: Benchmark Complete (New Record)
- **Metrics**:
  - Request Latency (Mean): 141.97s
  - Time to First Token (Mean): 16.29s
  - Throughput (Output Tokens/sec): 1510.63
  - Success Rate: 100% (600/600 requests)
- **Resources**: 8 NVIDIA GPUs (RTX 6000 recommended)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/llama-3.1-70b/summary_lifecycle_metrics.json)

