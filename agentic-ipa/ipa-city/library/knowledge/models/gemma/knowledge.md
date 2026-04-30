# Gemma Models

## gemma4-vllm
The `gemma4-vllm` configuration is used for deploying the Gemma 4 model using the vLLM serving engine.

- **Location**: `packs/model-serving/overlays/kustomize/vllm/gemma4-vllm`
- **Model ID**: `google/gemma4-vllm`

## gemma-2b-vllm
The `gemma-2b-vllm` configuration is used for deploying the Gemma 2b model using the vLLM serving engine.

- **Manifest**: `manifest-gemma-2b.yaml`
- **Model ID**: `google/gemma-2b`
- **Deployment Name**: `gemma-2b-vllm-deployment`
- **Resources**: 1 NVIDIA GPU (RTX 6000 recommended)
