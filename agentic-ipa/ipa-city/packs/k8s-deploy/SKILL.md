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
2. **Apply the manifest**:
   ```bash
   kubectl apply -f <manifest-path>
   ```
3. **Verify Submission**:
   The command should output `service/<name> created` and `deployment/<name> created`.

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

   Example:
   ```bash
   kubectl proxy &
   PID=$!
   sleep 2
   # Using port number 8000
   curl http://localhost:8001/api/v1/namespaces/default/services/<service-name>:8000/proxy/health
   kill $PID
   ```
