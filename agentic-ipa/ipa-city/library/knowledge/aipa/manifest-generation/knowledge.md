# Manifest Generation Knowledge

Manifest generation is the first step in the AIPA (Agentic Inference Profile Automation) workflow. It involves creating Kubernetes deployment manifests from Kustomize templates.

## Formula Details

- **Formula Name**: `generate-manifest`
- **Location**: `packs/model-serving/formulas/generate-manifest.toml`
- **Purpose**: To generate K8s deployment manifests for model servers using Kustomize.

## Execution Steps

The standard process for generating a vLLM manifest is:

1. **Navigate to the vLLM overlay directory**:
   ```bash
   cd overlays/kustomize/vllm
   ```

2. **Run Kustomize build**:
   ```bash
   kustomize build . > ../../../generated-vllm-manifest.yaml
   ```

3. **Verify Output**:
   Ensure that `generated-vllm-manifest.yaml` has been created in the expected location and contains valid Kubernetes resource definitions.

## Key Paths

- **Source Overlays**: `overlays/kustomize/vllm` (and other model-specific overlays)
- **Output Manifest**: `generated-vllm-manifest.yaml` (usually at the project root or specified output path)
