# Generate Manifest Skill

This skill describes how to generate Kubernetes deployment manifests for model servers using Kustomize.

## Prerequisites
- `kustomize` installed.
- Access to the `packs/model-serving/overlays/kustomize` directory.

## Process
1. **Navigate to the target overlay**:
   Identify the model and server type (e.g., vLLM or JetStream) and navigate to its overlay directory.
   Example for vLLM:
   ```bash
   cd packs/model-serving/overlays/kustomize/vllm
   ```

2. **Generate the manifest**:
   Run `kustomize build` and redirect the output to a YAML file in the root or a designated folder.
   ```bash
   kustomize build . > ../../../generated-vllm-manifest.yaml
   ```

3. **Verify the output**:
   Ensure the generated file is not empty and contains valid Kubernetes resources (Deployment, Service, etc.).
