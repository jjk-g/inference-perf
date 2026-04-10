# Copyright 2026 The Kubernetes Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import ast
import json
import yaml
from typing import List, Dict, Any
import polars as pl
from pydantic import BaseModel, Field

class MetricDef(BaseModel):
    name: str
    formula: str

class GlobalDef(BaseModel):
    name: str
    column: str
    operation: str

class TagDef(BaseModel):
    name: str
    condition: str

class WorkloadPolicy(BaseModel):
    metrics: List[MetricDef] = Field(default_factory=list)
    global_context: List[GlobalDef] = Field(default_factory=list)
    tags: List[TagDef] = Field(default_factory=list)

class PolarsTranslator(ast.NodeVisitor):
    def translate(self, formula: str):
        tree = ast.parse(formula, mode='eval')
        return self.visit(tree.body)

    def visit_Name(self, node):
        return pl.col(node.id)

    def visit_Constant(self, node):
        return pl.lit(node.value)

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        
        if isinstance(node.op, ast.Add):
            return left + right
        elif isinstance(node.op, ast.Sub):
            return left - right
        elif isinstance(node.op, ast.Mult):
            return left * right
        elif isinstance(node.op, ast.Div):
            return left / right
        elif isinstance(node.op, ast.BitAnd):
            return left & right
        elif isinstance(node.op, ast.BitOr):
            return left | right
        else:
            raise NotImplementedError(f"Unsupported binary operator: {type(node.op)}")

    def visit_Compare(self, node):
        left = self.visit(node.left)
        right = self.visit(node.comparators[0])
        op = node.ops[0]
        
        if isinstance(op, ast.Gt):
            return left > right
        elif isinstance(op, ast.Lt):
            return left < right
        elif isinstance(op, ast.Eq):
            return left == right
        elif isinstance(op, ast.GtE):
            return left >= right
        elif isinstance(op, ast.LtE):
            return left <= right
        else:
            raise NotImplementedError(f"Unsupported comparison operator: {type(op)}")

    def visit_BoolOp(self, node):
        values = [self.visit(v) for v in node.values]
        if isinstance(node.op, ast.And):
            res = values[0]
            for v in values[1:]:
                res = res & v
            return res
        elif isinstance(node.op, ast.Or):
            res = values[0]
            for v in values[1:]:
                res = res | v
            return res
        else:
            raise NotImplementedError(f"Unsupported boolean operator: {type(node.op)}")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        else:
            raise NotImplementedError(f"Unsupported unary operator: {type(node.op)}")

    def generic_visit(self, node):
        raise NotImplementedError(f"Unsupported AST node: {type(node)}")

def load_policy(config_path: str) -> WorkloadPolicy:
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    return WorkloadPolicy(**config_data)

def load_otel_trace(file_path: str) -> pl.LazyFrame:
    import json
    with open(file_path, 'r') as f:
        data = json.load(f)
    spans = data.get("spans", [])
    df = pl.DataFrame(spans)
    if "attributes" in df.columns:
        df = df.unnest("attributes")
    
    rename_map = {}
    if "gen_ai.usage.prompt_tokens" in df.columns:
        rename_map["gen_ai.usage.prompt_tokens"] = "input_tokens"
    if "gen_ai.usage.completion_tokens" in df.columns:
        rename_map["gen_ai.usage.completion_tokens"] = "output_tokens"
        
    if rename_map:
        df = df.rename(rename_map)
        
    return df.lazy()

class WorkloadClassifier:
    def __init__(self, policy: WorkloadPolicy):
        self.policy = policy
        self.translator = PolarsTranslator()

    def classify(self, df: pl.LazyFrame) -> Dict[str, Any]:
        # Phase 1: Metric Derivation
        for metric in self.policy.metrics:
            expr = self.translator.translate(metric.formula)
            df = df.with_columns(expr.alias(metric.name))

        # Phase 2: Global Context Aggregation
        globals_dict = {}
        
        # Check if RPS is needed
        use_rps = False
        for g in self.policy.global_context:
            if g.column == "requests_per_second":
                use_rps = True
                break
                
        if use_rps:
            schema_names = df.collect_schema().names()
            ts_col = None
            if "start_time" in schema_names:
                ts_col = "start_time"
            elif "timestamp" in schema_names:
                ts_col = "timestamp"
                
            if ts_col:
                rps_expr = pl.col(ts_col)
                if ts_col == "start_time":
                    rps_expr = pl.col(ts_col).str.slice(0, 19)
                
                rps_df = df.group_by(rps_expr.alias("second")).agg(pl.len().alias("requests_per_second"))
                
                for g in self.policy.global_context:
                    if g.column == "requests_per_second":
                        col = pl.col("requests_per_second")
                        if g.operation == "mean":
                            agg_expr = col.mean().alias(g.name)
                        elif g.operation == "p90":
                            agg_expr = col.quantile(0.9).alias(g.name)
                        elif g.operation == "std":
                            agg_expr = col.std().alias(g.name)
                        elif g.operation == "median":
                            agg_expr = col.median().alias(g.name)
                        else:
                             raise NotImplementedError(f"Unsupported operation for RPS: {g.operation}")
                             
                        val = rps_df.select(agg_expr).collect().to_dicts()[0][g.name]
                        globals_dict[g.name] = val
            else:
                raise ValueError("requests_per_second requested but no timestamp or start_time column found.")

        global_aggs = []
        for g in self.policy.global_context:
            if g.column == "requests_per_second":
                continue
            col = pl.col(g.column)
            if g.operation == "mean":
                agg_expr = col.mean().alias(g.name)
            elif g.operation == "std":
                agg_expr = col.std().alias(g.name)
            elif g.operation == "median":
                agg_expr = col.median().alias(g.name)
            elif g.operation == "p90":
                agg_expr = col.quantile(0.9).alias(g.name)
            else:
                 raise NotImplementedError(f"Unsupported operation: {g.operation}")
            global_aggs.append(agg_expr)

        if global_aggs:
            agg_df = df.select(global_aggs).collect()
            globals_dict.update(agg_df.to_dicts()[0])

        for name, val in globals_dict.items():
             df = df.with_columns(pl.lit(val).alias(name))

        # Phase 3: Tag Evaluation
        for tag in self.policy.tags:
            expr = self.translator.translate(tag.condition)
            df = df.with_columns(expr.alias(tag.name))

        metric_names = [m.name for m in self.policy.metrics]
        summary_exprs = []
        for m in metric_names:
            col = pl.col(m)
            summary_exprs.extend([
                col.mean().alias(f"{m}_mean"),
                col.quantile(0.1).alias(f"{m}_p10"),
                col.quantile(0.5).alias(f"{m}_p50"),
                col.quantile(0.9).alias(f"{m}_p90"),
                col.std().alias(f"{m}_std_dev"),
                col.min().alias(f"{m}_min"),
                col.max().alias(f"{m}_max"),
            ])

        tag_names = [t.name for t in self.policy.tags]
        final_exprs = summary_exprs + [pl.col(t).first().alias(t) for t in tag_names]

        final_df = df.select(final_exprs).collect()
        result = final_df.to_dicts()[0]

        workload_card = {
            "base_metrics": {},
            "tags": {}
        }

        for m in metric_names:
            workload_card["base_metrics"][m] = {
                "mean": result.get(f"{m}_mean"),
                "p10": result.get(f"{m}_p10"),
                "p50": result.get(f"{m}_p50"),
                "p90": result.get(f"{m}_p90"),
                "std_dev": result.get(f"{m}_std_dev"),
                "min": result.get(f"{m}_min"),
                "max": result.get(f"{m}_max"),
            }

        for t in tag_names:
            workload_card["tags"][t] = result.get(t)

        return workload_card
