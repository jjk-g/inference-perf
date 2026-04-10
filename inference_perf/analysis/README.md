# Workload Classifier

The Workload Classifier is a tool for analyzing inference traces and classifying the workload based on configurable policies. It helps in identifying traffic patterns (e.g., bursty or smooth) and workload characteristics (e.g., prefill heavy or decode heavy).

## Features

- **Metric Derivation**: Derives new columns from existing trace data using Polars expressions.
- **Global Context Aggregation**: Computes dataset-wide statistics like `mean`, `std`, `median`, and `p90`.
- **Time-Based Aggregation**: Automatically derives `requests_per_second` by binning requests into 1-second intervals based on `timestamp` or `start_time` columns.
- **Tag Evaluation**: Evaluates boolean conditions involving global aggregates to apply descriptive tags to the workload.

## Configuration Format

The classifier is driven by a YAML policy file with three main sections:

```yaml
metrics:
  - name: "total_tokens"
    formula: "input_tokens + output_tokens"

global_context:
  - name: "avg_isl"
    column: "input_tokens"
    operation: "mean"
  - name: "p90_rps"
    column: "requests_per_second"
    operation: "p90"
  - name: "mean_rps"
    column: "requests_per_second"
    operation: "mean"

tags:
  - name: "prefill_heavy"
    condition: "avg_isl > 100"
  - name: "traffic_bursty"
    condition: "p90_rps > (2 * mean_rps)"
```

### Supported Operations in `global_context`
- `mean`
- `std`
- `median`
- `p90`

## Usage

You can run the classifier using the `inference-perf` CLI:

```bash
python -m inference_perf.main \
  --classify-trace path/to/trace.json \
  --classify-config path/to/config.yaml \
  --classify-format otel
```

Supported formats are `jsonl` (default) and `otel`.
