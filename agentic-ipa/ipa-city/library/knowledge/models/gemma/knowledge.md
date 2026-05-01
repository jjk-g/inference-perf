# Gemma Models

## gemma4-vllm
The `gemma4-vllm` configuration is used for deploying the Gemma 4 model using the vLLM serving engine.

- **Manifest**: `generated-vllm-gemma4.yaml`
- **Model ID**: `google/gemma-2b` (Note: Currently points to gemma-2b in manifest)
- **Deployment Name**: `gemma4-vllm-vllm-deployment`
- **Service Name**: `gemma4-vllm-vllm-service`
- **Status**: Benchmark Completed
- **Metrics**:
  - Request Latency (Mean): 0.845s
  - Time to First Token (Mean): 0.116s
  - Throughput (Total Tokens/sec): 6294.37
  - Requests/sec: 9.36
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)

## gemma-2b-vllm
The `gemma-2b-vllm` configuration is used for deploying the Gemma 2b model using the vLLM serving engine.

- **Manifest**: `manifest-gemma-2b.yaml`
- **Model ID**: `google/gemma-2b`
- **Deployment Name**: `gemma-2b-vllm-deployment`
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)

## gemma-7b-it
The `gemma-7b-it` configuration is used for deploying the Gemma 7b Instruction Tuned model.

- **vLLM Overlay**: `packs/model-serving/overlays/kustomize/vllm/gemma-7b-it`
- **JetStream Overlay**: `packs/model-serving/overlays/kustomize/jetstream/gemma-7b-it`
- **Resources**: 1 NVIDIA GPU (RTX 6000) or TPU v5e 2x4 (JetStream)
