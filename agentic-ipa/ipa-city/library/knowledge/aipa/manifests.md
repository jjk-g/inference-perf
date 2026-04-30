# Model Manifest Inventory

This document tracks the available Kubernetes deployment manifests in the Gas City workspace.

## Active Manifests

| Model | Manifest File | Type | Status |
|-------|---------------|------|--------|
| Gemma 4 | `manifest-gemma4-vllm.yaml` | vLLM | Benchmark Complete |
| Gemma 4 (GPU) | `manifest-gemma4-vllm-gpu.yaml` | vLLM | Ready |
| Llama 3 8B | `generated-vllm-llama3-8b.yaml` | vLLM | Benchmark Complete |
| Llama 3 70B | `manifest-llama3-70b.yaml` | vLLM | Benchmark Complete |
| Gemma 2B | `generated-vllm-gemma-2b.yaml` | vLLM | Benchmark Complete |

## Legacy or Test Manifests

- `manifest-gemma-2b.yaml` (Older version?)
- `manifest-llama3-8b.yaml` (Older version?)
- `generated-llama3-8b-manifest.yaml` (Redundant?)
- `test.yaml`

## Naming Convention

New manifests should follow the naming convention: `generated-<server>-<model>.yaml`.
Example: `generated-vllm-gemma-2b.yaml`
