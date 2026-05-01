# Gemma Models

## gemma4-vllm
The `gemma4-vllm` configuration is used for deploying the Gemma 4 model using the vLLM serving engine.

- **Manifest**: `generated-vllm-gemma4.yaml`
- **Model ID**: `google/gemma-2b` (Note: Currently points to gemma-2b in manifest)
- **Deployment Name**: `gemma4-vllm-vllm-deployment`
- **Service Name**: `gemma4-vllm-vllm-service`
- **Status**: Benchmark Complete (100% Success Rate)
- **Metrics (Latest)**:
  - Request Latency (Mean): 8.53s
  - Time to First Token (Mean): 8.02s
  - Throughput (Output Tokens/sec): 359.00
  - Success Rate: 100% (150/150 requests)
- **Metrics (Baseline - High Load)**:
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
- **Status**: 
  - **vLLM GPU**: Benchmark Failed (0% success rate).
  - **vLLM CPU**: **Fixed**. A crash was identified in v0.6.6 on CPU (is_async_output_supported).
- **Troubleshooting Recommendations**:
  - **CPU Deployment**: Use `--enforce-eager`, `--disable-async-output-proc`, `--worker-cls=vllm.worker.cpu_worker.CPUWorker`, `--disable-frontend-multiprocessing`, and `--block-size 16` flags in the vLLM arguments. These resolve `NotImplementedError`, ZMQ errors with `uvloop`, and `TypeError` related to `block_size` being `None` on CPU. Also set `VLLM_DEVICE=cpu` and `VLLM_TARGET_DEVICE=cpu` environment variables.
  - **Memory Limit**: Consider increasing to 64Gi if OOM kills are observed (similar to Llama-3.1-8B-Instruct).
  - **Readiness Probe**: Increase `failureThreshold` to 120 to allow more time for model weights to load.
- **Research Note**: A discrepancy was found between the archived log (port 8001, 14.8% error) and the indexed results (port 8005, 100% failure). This suggests the port 8005 deployment was unstable or incorrectly configured. Switching to JetStream for GPU is currently in progress.
- **Resources**: 
  - **GPU**: 1 NVIDIA GPU (RTX 6000)
  - **CPU**: 4-8 CPUs, 16-32Gi memory
  - **TPU**: TPU v5e 2x4 (JetStream)
- **Benchmark Results**: [summary_lifecycle_metrics.json](../../benchmarks/gemma-7b-it/summary_lifecycle_metrics.json)
