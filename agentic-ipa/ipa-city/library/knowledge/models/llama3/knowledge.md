# Llama3 Models

## Llama3-8b

- **Model ID**: `meta-llama/Meta-Llama-3-8B`
- **Manifest**: `generated-llama3-8b-manifest.yaml`
- **Deployment Name**: `llama3-8b-vllm-deployment`
- **Service Name**: `llama3-8b-vllm-service`
- **Status**: Benchmark Complete
- **Metrics**:
  - Request Latency (Mean): 12.53s
  - Time to First Token (Mean): 6.99s
  - Throughput (Output Tokens/sec): 1350.19
  - Success Rate: 100% (600/600 requests)
- **Resources**: 1 NVIDIA GPU (L4 recommended)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/llama3-8b/summary_lifecycle_metrics.json)

## Llama3-70b

- **Model ID**: `meta-llama/Meta-Llama-3-70B`
- **Manifest**: `generated-vllm-llama3-70b.yaml`
- **Deployment Name**: `llama3-70b-vllm-deployment`
- **Service Name**: `llama3-70b-vllm-service`
- **Status**: Benchmark Complete
- **Metrics**:
  - Request Latency (Mean): 5.27s
  - Time to First Token (Mean): 0.46s
  - Throughput (Output Tokens/sec): 185.88
  - Success Rate: 91.7% (55/60 requests)
- **Resources**: 8 NVIDIA GPUs (RTX 6000 recommended)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/llama3-70b/summary_lifecycle_metrics.json)
