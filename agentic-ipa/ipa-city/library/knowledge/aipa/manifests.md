# Model Manifest Inventory

This document tracks the available Kubernetes deployment manifests in the Gas City workspace.

## Active Manifests

| Model | Manifest File | Type | Status |
|-------|---------------|------|--------|
| Gemma 4 | `library/knowledge/manifests/manifest-gemma4-vllm.yaml` | vLLM | Benchmark Complete |
| Gemma 4 (GPU) | `library/knowledge/manifests/manifest-gemma4-vllm-gpu.yaml` | vLLM | Ready |
| Llama 3 8B | `library/knowledge/manifests/generated-vllm-llama3-8b.yaml` | vLLM | Benchmark Complete |
| Llama 3 70B | `library/knowledge/manifests/manifest-llama3-70b.yaml` | vLLM | Benchmark Complete |
| Gemma 2B | `library/knowledge/manifests/generated-vllm-gemma-2b.yaml` | vLLM | Benchmark Complete |
| Gemma 7B-it | `library/knowledge/manifests/generated-vllm-gemma-7b-it.yaml` | vLLM | Benchmark Complete |
| Llama 3.1 8B Instruct | `packs/model-serving/overlays/kustomize/vllm/llama-3.1-8b-instruct` | vLLM | Benchmark Complete |
| Mistral-7B-v0.3 | `packs/model-serving/overlays/kustomize/vllm/mistral-7b-v0.3` | vLLM | Overlay Drafted |

## Legacy or Test Manifests

- `library/knowledge/manifests/generated-llama3-8b-manifest.yaml` (Redundant?)
- `test.yaml`

## Naming Convention

New manifests should follow the naming convention: `generated-<server>-<model>.yaml`.
Example: `generated-vllm-gemma-2b.yaml`
