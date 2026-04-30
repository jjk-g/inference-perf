# Archive Results Skill

This skill describes how to archive and index benchmark results in the Gas City Library.

## Prerequisites
- A directory containing benchmark results (e.g., `reports-YYYYMMDD-HHMMSS`).
- A model name associated with the results (e.g., `gemma4-vllm`).

## Process

1. **Create the target directory**:
   Create a directory for the model results in the library.
   ```bash
   mkdir -p library/knowledge/benchmarks/<model-name>
   ```

2. **Move the results**:
   Move the report files into the newly created directory.
   ```bash
   mv -f reports-<timestamp>/* library/knowledge/benchmarks/<model-name>/
   ```

3. **Update the Library Index**:
   Add the new knowledge entry to `library/index.json`.
   ```json
   "benchmarks": {
     "<model-name>": "library/knowledge/benchmarks/<model-name>/summary_lifecycle_metrics.json"
   }
   ```
   *(Note: Adjust the path if multiple files are indexed)*

4. **Update the Library Catalog**:
   Add a summary of the new results to `library/knowledge/library/catalog/knowledge.md`.

5. **Clean up**:
   Remove the empty reports directory.
   ```bash
   rm -rf reports-<timestamp>
   ```
