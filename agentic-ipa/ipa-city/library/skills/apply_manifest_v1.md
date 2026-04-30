# Apply Manifest Skill

This skill describes how to deploy a model server using a generated Kubernetes manifest.

## Prerequisites
- A generated manifest file (e.g., `generated-vllm-llama3-8b.yaml`).
- `kubectl` configured with access to the cluster.

## Process
1. **Locate the manifest file**: Ensure the manifest for the model is available in the current directory or specified path (typically `library/knowledge/manifests/`).
2. **Apply the manifest**:
   ```bash
   kubectl apply -f <manifest-path>
   ```
   Example:
   ```bash
   kubectl apply -f library/knowledge/manifests/generated-vllm-llama3-8b.yaml
   ```
3. **Verify Submission**:
   The command should output `service/<name> created` and `deployment/<name> created`.

## Cleanup
To remove a deployed model server and free up resources, use the `kubectl delete` command with the same manifest file. **Crucial**: Always delete the old deployment before applying a new one for the same model to ensure a clean state.

```bash
kubectl delete -f <manifest-path>
```
Example:
```bash
kubectl delete -f library/knowledge/manifests/generated-vllm-llama3-8b.yaml
```
This will remove the deployment, service, and any other resources defined in the manifest.
