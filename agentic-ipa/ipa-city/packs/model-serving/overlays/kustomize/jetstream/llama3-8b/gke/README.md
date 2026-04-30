# llama3-8b

## Configuration
| Kind | Model Server | Model | Provider | Accelerator |
| --- | --- | --- | --- | --- |
| Deployment | JetStream | llama3-8b | GKE | nvidia-rtx-pro-6000 |

## Usage
The bucket name is configured as `llama3-8b-jetstream` by default. If you need to use a different bucket, update `bucketName` in `deployment.patch.yaml` and the `-o` flag in `../base/job.patch.yaml`.

The example can be deployed by issuing the commands:

```
kustomize build core/deployment/jetstream/llama3-8b/gke | kubectl apply -f - --selector prerequisite=model-load &&
kubectl wait --for=condition=complete --timeout=1000s job/llama3-8b-jetstream-data-loader &&
kustomize build core/deployment/jetstream/llama3-8b/gke | kubectl apply -f - --selector app=llama3-8b-jetstream-inference-server
```
