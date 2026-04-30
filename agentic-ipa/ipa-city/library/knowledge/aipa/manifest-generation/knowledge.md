# Manifest Generation Knowledge

Manifest generation is the first step in the AIPA (Agentic Inference Profile Automation) workflow. It involves creating Kubernetes deployment manifests from Kustomize templates.

## Formula Details

- **Formula Name**: `generate-manifest`
- **Location**: `packs/model-serving/formulas/generate-manifest.toml`
- **Purpose**: To generate K8s deployment manifests for model servers using Kustomize.

## Execution Steps

The standard process for generating a vLLM manifest is:

1. **Navigate to the specific model overlay directory**:
   Navigate to the directory containing the `kustomization.yaml` file (often in a `gke` subdirectory).
   Example for Gemma 4:
   ```bash
   cd packs/model-serving/overlays/kustomize/vllm/gemma4-vllm/gke
   ```

2. **Run Kustomize build**:
   Redirect the output to the `packs/model-serving` directory.
   ```bash
   kustomize build . > ../../../../../generated-vllm-gemma4-vllm.yaml
   ```

3. **Verify Output**:
   Ensure that the generated YAML file has been created and contains valid Kubernetes resource definitions.

## Key Paths

- **Source Overlays**: `packs/model-serving/overlays/kustomize/vllm/<model>`
- **Output Manifest**: `packs/model-serving/generated-vllm-<model>.yaml`
