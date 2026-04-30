# Generate Manifest Skill

This skill describes how to generate Kubernetes deployment manifests for model servers using Kustomize.

## Prerequisites
- `kustomize` installed.
- Access to the `packs/model-serving/overlays/kustomize` directory.

## Process
1. **Navigate to the target overlay**:
   Identify the model and server type (e.g., vLLM or JetStream) and navigate to its overlay directory. **Crucial**: You must navigate to the subdirectory that contains the `kustomization.yaml` file, which is often an environment-specific folder like `gke`.
   Example for vLLM:
   ```bash
   cd packs/model-serving/overlays/kustomize/vllm/gemma4-vllm/gke
   ```

2. **Generate the manifest**:
   Run `kustomize build` and redirect the output to a YAML file in the `packs/model-serving` directory. Adjust the relative path as needed (e.g., `../../../../../` if you are in a `gke` subdirectory).

   
   Naming convention: `generated-<server>-<model>.yaml` (e.g., `generated-vllm-llama3-70b.yaml`).

   Example:
   ```bash
   # From packs/model-serving/overlays/kustomize/vllm/llama3-70b
   kustomize build . > ../../../../../generated-vllm-llama3-70b.yaml
   ```

3. **Verify the output**:
   Ensure the generated file is not empty and contains valid Kubernetes resources (Deployment, Service, etc.).

## Troubleshooting: Missing Overlay
If a model overlay does not exist for your target server type (vLLM or JetStream):
1. **Find a similar model**: Identify an existing overlay for the same server type (e.g., `gemma-2b` for `vllm`).
2. **Copy and adapt**: Copy the entire directory structure of the similar model to a new directory named after your target model.
3. **Update patches**: Modify the `.patch.yaml` files in the new directory to point to the correct model name and deployment identifiers.
4. **Update kustomization**: Ensure the `kustomization.yaml` correctly references the base and components.

