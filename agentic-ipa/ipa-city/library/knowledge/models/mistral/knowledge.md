# Mistral Models

## Mistral-7B-v0.3

- **Model ID**: `mistralai/Mistral-7B-v0.3`
- **vLLM Overlay**: `packs/model-serving/overlays/kustomize/vllm/mistral-7b-v0.3`
- **Status**: Benchmark Complete
- **Metrics**:
  - Request Latency (Mean): 12.26s
  - Time to First Token (Mean): 9.56s
  - Throughput (Output Tokens/sec): 299.68
  - Success Rate: 98.3% (59/60 requests)
- **Manifest**: `library/knowledge/manifests/generated-vllm-mistral-7b-v0.3.yaml`
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/mistral-7b-v0.3/summary_lifecycle_metrics.json)
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)
