---
name: k8s-deploy
description: Skills for deploying and verifying model servers on Kubernetes.
---

# K8s Deploy Skill

This skill covers deploying model servers and waiting for them to become healthy.

## Apply Manifest
This process describes how to deploy a model server using a generated Kubernetes manifest.

### Prerequisites
- A generated manifest file (e.g., `generated-llama3-8b-manifest.yaml`).
- `kubectl` configured with access to the cluster.

### Process
1. **Locate the manifest file**: Ensure the manifest for the model is available in the current directory or specified path.
2. **Verify Secrets**: For gated models (e.g., Llama 3, Gemma), ensure the `hf-secret` exists in the namespace:
   ```bash
   kubectl get secret hf-secret
   ```
3. **Apply the manifest**:
   ```bash
   kubectl apply -f <manifest-path>
   ```
4. **Verify Submission**:
   The command should output `service/<name> created` and `deployment/<name> created`.

### Troubleshooting: `kubectl apply` Failures
If the command fails, check for the following common issues:
- **Unauthorized/Forbidden**: Ensure you have the correct context and permissions for the target namespace.
- **Invalid YAML**: Verify that the manifest file was not corrupted during generation or transfer. Run `kubectl apply --dry-run=client -f <manifest-path>` to check for syntax errors.
- **Connection Refused**: Ensure the cluster is reachable and your `kubeconfig` is properly configured.
- **Resource Conflict**: If a resource already exists and cannot be patched, you may need to delete it first using `kubectl delete -f <manifest-path>` before re-applying.
- **Immutable Jobs**: If using a `data-loader` job, it may be immutable. If you need to re-apply or switch manifests (e.g., from TPU to GPU), you must manually delete the existing job first: `kubectl delete job <job-name>`.
- **TPU Availability**: If a TPU deployment fails due to resource unavailability (e.g., `tpu-v5-lite-podslice`), consider switching to a GPU fallback manifest if available.
- **JetStream-on-GPU**: If using JetStream on GPUs, ensure `JAX_PLATFORMS=cpu` is set in the manifest to prevent TPU metadata loops.
- **Gated Models**: Ensure the `hf-secret` (formerly `huggingface-secret`) is present in the namespace for models requiring authentication (e.g., Llama 3, Gemma).

## Wait Healthy
This process describes how to wait for a deployed model server to be healthy and ready.

### Prerequisites
- `kubectl` configured.
- The name of the deployment or service to check.

### Process
1. **Wait for deployment rollout**:
   ```bash
   kubectl rollout status deployment/<deployment-name>
   ```

2. **Check health endpoint**:
   Use `curl` or a similar tool to check the `/health` or `/v1/models` endpoint of the service.
   Checking via the `kubectl proxy` method is recommended for reliability.

   Example:
   ```bash
   kubectl proxy &
   PID=$!
   sleep 2
   # Using port number 8000
   curl http://localhost:8001/api/v1/namespaces/default/services/<service-name>:8000/proxy/health
   kill $PID
   ```

## Cleanup Resources
This process describes how to remove the model server resources from the Kubernetes cluster.

### Prerequisites
- The manifest file used for deployment (e.g., `generated-llama3-8b-manifest.yaml`).
- `kubectl` configured with access to the cluster.

### Process
1. **Delete using manifest**:
   If the manifest file is available, use it to delete all associated resources:
   ```bash
   kubectl delete -f <manifest-path>
   ```
2. **Manual Deletion** (if manifest is unavailable):
   If the manifest is not available, delete the deployment and service by name:
   ```bash
   kubectl delete deployment <deployment-name>
   kubectl delete service <service-name>
   ```
3. **Verify Deletion**:
   Ensure the resources are no longer listed:
   ```bash
   kubectl get deployment <deployment-name>
   kubectl get service <service-name>
   ```
