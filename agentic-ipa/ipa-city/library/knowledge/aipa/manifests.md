# Model Manifest Inventory

This document tracks the available Kubernetes deployment manifests in the Gas City workspace.

## Active Manifests

| Model | Manifest File | Type | Status |
|-------|---------------|------|--------|
| Gemma 4 | `library/knowledge/manifests/manifest-gemma4-vllm.yaml` | vLLM | Benchmark Complete |
| Gemma 4 (GPU) | `library/knowledge/manifests/manifest-gemma4-vllm-gpu.yaml` | vLLM | Ready |
| Llama 3 8B | `library/knowledge/manifests/generated-vllm-llama3-8b.yaml` | vLLM | Benchmark Complete |
| Llama 3 8B (JetStream) | `library/knowledge/manifests/generated-jetstream-llama3-8b.yaml` | JetStream | Ready |
| Llama 3 70B | `library/knowledge/manifests/generated-vllm-llama3-70b.yaml` | vLLM | Updated |
| Gemma 2B | `library/knowledge/manifests/generated-vllm-gemma-2b.yaml` | vLLM | Benchmark Complete |
| Gemma 7B-it | `library/knowledge/manifests/generated-vllm-gemma-7b-it.yaml` | vLLM | Benchmark Complete |
| Gemma 7B-it (JetStream) | `library/knowledge/manifests/generated-jetstream-gemma-7b-it.yaml` | JetStream | Ready |
| Llama 3 8B (JetStream GPU) | `library/knowledge/manifests/generated-jetstream-llama3-8b-gpu.yaml` | JetStream | Ready (CPU Fallback*) |

*Note: JetStream GPU deployments currently fall back to CPU due to image limitations. vLLM is the recommended alternative for GPU benchmarking until optimized images are available.
| Llama 3.1 8B Instruct | `library/knowledge/manifests/generated-vllm-llama-3.1-8b-instruct.yaml` | vLLM | Benchmark Complete |
| Llama 3.1 70B | `library/knowledge/manifests/generated-vllm-llama-3.1-70b.yaml` | vLLM | Benchmark Complete |
| Mistral-7B-v0.3 | `library/knowledge/manifests/generated-vllm-mistral-7b-v0.3.yaml` | vLLM | Benchmark Complete |

## Legacy or Test Manifests

- `library/knowledge/manifests/generated-llama3-8b-manifest.yaml` (Redundant?)
- `test.yaml`

## Naming Convention

New manifests should follow the naming convention: `generated-<server>-<model>.yaml`.
Example: `generated-vllm-gemma-2b.yaml`
