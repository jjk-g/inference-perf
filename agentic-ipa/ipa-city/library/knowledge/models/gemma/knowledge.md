# Gemma Models

## gemma4-vllm
The `gemma4-vllm` configuration is used for deploying the Gemma 4 model using the vLLM serving engine.

- **Manifest**: `generated-vllm-gemma4.yaml`
- **Model ID**: `google/gemma-2b` (Note: Currently points to gemma-2b in manifest)
- **Deployment Name**: `gemma4-vllm-vllm-deployment`
- **Service Name**: `gemma4-vllm-vllm-service`
- **Status**: Benchmark Complete
- **Metrics**:
  - Request Latency (Mean): 0.85s
  - Time to First Token (Mean): 0.12s
  - Throughput (Output Tokens/sec): 1286.38
  - Success Rate: 95.2% (571/600 requests)
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/gemma4-vllm/summary_lifecycle_metrics.json)

## gemma-2b-vllm
The `gemma-2b-vllm` configuration is used for deploying the Gemma 2b model using the vLLM serving engine.

- **Manifest**: `manifest-gemma-2b.yaml`
- **Model ID**: `google/gemma-2b`
- **Deployment Name**: `gemma-2b-vllm-deployment`
- **Status**: Benchmark Complete
- **Metrics**:
  - Request Latency (Mean): 2.71s
  - Time to First Token (Mean): 0.12s
  - Throughput (Output Tokens/sec): 4592.15
  - Success Rate: 94.0% (564/600 requests)
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/gemma-2b/summary_lifecycle_metrics.json)

## gemma-7b-it
The `gemma-7b-it` configuration is used for deploying the Gemma 7b Instruction Tuned model.

- **vLLM Overlay**: `packs/model-serving/overlays/kustomize/vllm/gemma-7b-it`
- **JetStream Overlay**: `packs/model-serving/overlays/kustomize/jetstream/gemma-7b-it`
- **Status**: Benchmark Failed (0% success rate)
- **Research Note**: A discrepancy was found between the archived log (port 8001, 14.8% error) and the indexed results (port 8005, 100% failure). This suggests the port 8005 deployment was unstable or incorrectly configured.
- **Resources**: 1 NVIDIA GPU (RTX 6000) or TPU v5e 2x4 (JetStream)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/gemma-7b-it/summary_lifecycle_metrics.json)
