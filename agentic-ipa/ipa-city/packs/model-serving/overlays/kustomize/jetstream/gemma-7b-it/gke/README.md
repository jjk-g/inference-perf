# Gemma-7b-it

## Configuration
| Kind | Model Server | Model | Provider | Accelerator |
| --- | --- | --- | --- | --- |
| Deployment | JetStream | gemma-7b-it | GKE | nvidia-rtx-pro-6000 |

## Usage
The bucket name is configured as `llama3-8b-jetstream` by default. If you need to use a different bucket, update the `-b` flag in `../base/job.patch.yaml` and the `load_parameters_path` in `../base/deployment.patch.yaml`.

The example can be deployed by issuing the commands:

```
kustomize build core/deployment/jetstream/gemma-7b-it/gke | kubectl apply -f - --selector prerequisite=model-load &&
kubectl wait --for=condition=complete --timeout=1000s job/gemma-7b-it-jetstream-data-loader &&
kustomize build core/deployment/jetstream/gemma-7b-it/gke | kubectl apply -f - --selector app=gemma-7b-it-jetstream-inference-server
```