# Apply Manifest Skill

This skill describes how to deploy a model server using a generated Kubernetes manifest.

## Prerequisites
- A generated manifest file (e.g., `generated-llama3-8b-manifest.yaml`).
- `kubectl` configured with access to the cluster.

## Process
1. **Locate the manifest file**: Ensure the manifest for the model is available in the current directory or specified path.
2. **Apply the manifest**:
   ```bash
   kubectl apply -f <manifest-path>
   ```
   Example:
   ```bash
   kubectl apply -f generated-llama3-8b-manifest.yaml
   ```
3. **Verify Submission**:
   The command should output `service/<name> created` and `deployment/<name> created`.
