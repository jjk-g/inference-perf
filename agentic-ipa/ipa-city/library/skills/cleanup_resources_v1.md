# Cleanup Resources Skill

This skill describes how to remove model server resources from the Kubernetes cluster after a task is complete.

## Prerequisites
- The manifest file used for deployment (e.g., `generated-llama3-8b-manifest.yaml`).
- `kubectl` configured with access to the cluster.

## Process

### 1. Delete using manifest
If the manifest file is available, use it to delete all associated resources:
```bash
kubectl delete -f <manifest-path>
```
Example:
```bash
kubectl delete -f library/knowledge/manifests/generated-vllm-llama3-8b.yaml
```

### 2. Manual Deletion
If the manifest is not available, delete the deployment and service by name:
```bash
kubectl delete deployment <deployment-name>
kubectl delete service <service-name>
```

### 3. Verify Deletion
Ensure the resources are no longer listed:
```bash
kubectl get deployment <deployment-name>
kubectl get service <service-name>
```
The commands should return an error like `Error from server (NotFound)`.

## Best Practices
- **Cleanup promptly**: Remove resources as soon as benchmarking and archiving are complete to free up cluster capacity.
- **Verification**: Always verify that the resources are actually gone.
- **Idempotency**: `kubectl delete` is generally idempotent; running it multiple times is safe.
