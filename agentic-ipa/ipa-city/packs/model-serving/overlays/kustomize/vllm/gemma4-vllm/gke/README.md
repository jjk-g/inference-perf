# Gemma4-vLLM

## Configuration
| Kind | Model Server | Model | Provider | Accelerator |
| --- | --- | --- | --- | --- |
| Deployment | vLLM | gemma4-vllm | GKE | GPU L4 |

## Usage

The template can be deployed with the following commands:

```
kustomize build core/deployment/vllm/gemma4-vllm/gke | kubectl apply -f -
```