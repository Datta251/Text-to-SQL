"""
Agent 2: Schema Pruning Agent
Selects only the tables and columns relevant to the user query.
Dramatically reduces context window size, inference latency, and hallucination.
"""

import re
from datetime import datetime
from typing import Dict, List, Set, Any
from agents.state import AEMGState, AgentLog

class SchemaPruningAgent:
    def __init__(self):
        # Table alias / semantic hints
        self.semantic_keywords = {
            "dim_customer": ["customer", "client", "buyer", "segment", "country", "city", "state"],
            "dim_product": ["product", "item", "category", "sub_category", "unit_cost", "laptops", "chairs", "furniture", "technology"],
            "dim_store": ["store", "region", "market_type", "market", "outlet", "retail", "enterprise", "size"],
            "dim_date": ["date", "year", "quarter", "month", "month_name", "day", "weekly", "annual", "2024", "2025", "2026"],
            "fact_sales": ["sale", "sales", "revenue", "gross_revenue", "profit", "quantity", "unit_price", "discount", "margin", "total"]
        }

    def run(self, state: AEMGState) -> AEMGState:
        query_text = state.query.lower()
        selected_tables: Set[str] = set()

        # Check for direct keyword matches
        for tbl, keywords in self.semantic_keywords.items():
            if tbl in state.full_schema:
                for kw in keywords:
                    if re.search(r"\b" + re.escape(kw) + r"\b", query_text):
                        selected_tables.add(tbl)
                        break

        # Check for column name matches
        for tbl, meta in state.full_schema.items():
            for col in meta.get("column_names", []):
                if re.search(r"\b" + re.escape(col.lower()) + r"\b", query_text):
                    selected_tables.add(tbl)

        # In a star-schema analytical warehouse, fact_sales is almost always required for metric aggregation
        if not selected_tables:
            selected_tables = set(state.full_schema.keys())
        else:
            # If any dimension is selected, ensure fact_sales is present for metric aggregation
            selected_tables.add("fact_sales")

        # Construct pruned schema
        pruned_schema: Dict[str, Any] = {}
        for tbl in selected_tables:
            if tbl in state.full_schema:
                pruned_schema[tbl] = state.full_schema[tbl]

        state.pruned_tables = list(selected_tables)
        state.pruned_schema = pruned_schema

        original_table_count = len(state.full_schema)
        pruned_table_count = len(pruned_schema)
        reduction_pct = round((1 - (pruned_table_count / max(1, original_table_count))) * 100, 1)

        state.agent_logs.append(
            AgentLog(
                agent_name="SchemaPruningAgent",
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                status="SUCCESS",
                message=f"Pruned schema from {original_table_count} to {pruned_table_count} tables ({reduction_pct}% reduction).",
                details={
                    "retained_tables": list(pruned_schema.keys()),
                    "omitted_tables": list(set(state.full_schema.keys()) - selected_tables)
                }
            )
        )
        return state
