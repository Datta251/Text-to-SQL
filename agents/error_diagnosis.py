"""
Agent 6: Error Diagnosis Agent
Analyzes execution & validation errors, detects root causes (schema hallucinations,
GROUP BY structural mismatches, missing joins), and synthesizes generalized repair knowledge.
"""

import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from agents.state import AEMGState, AgentLog

class ErrorDiagnosisAgent:
    def __init__(self):
        # Column mappings for common schema hallucinations
        self.column_synonyms = {
            "revenue": ("gross_revenue", "fact_sales"),
            "sales_amount": ("gross_revenue", "fact_sales"),
            "turnover": ("gross_revenue", "fact_sales"),
            "sales": ("gross_revenue", "fact_sales"),
            "cost": ("unit_cost", "dim_product"),
            "market": ("market_type", "dim_store"),
            "client_name": ("customer_name", "dim_customer"),
            "item_name": ("product_name", "dim_product")
        }

    def diagnose(self, state: AEMGState) -> Tuple[str, str, Dict[str, Any]]:
        """
        Diagnoses error cause and extracts generalized repair rule.
        Returns: (error_category, root_cause_explanation, learned_rule_dict)
        """
        err_msg = state.execution_error or state.validation_error or "Unknown error"
        sql = state.generated_sql or ""
        
        # 1. Missing Column / Column Hallucination
        col_match = re.search(r"no such column:\s*([\w\.]+)", err_msg, re.IGNORECASE)
        if col_match:
            missing_col = col_match.group(1).split(".")[-1].lower()
            
            # Check if there is a known synonym
            suggested_col, table_name = self.column_synonyms.get(missing_col, (None, None))
            
            # Check pruned/full schema for closest match
            if not suggested_col:
                all_cols = []
                for t, meta in state.full_schema.items():
                    for c in meta.get("column_names", []):
                        all_cols.append((c, t))
                for c, t in all_cols:
                    if missing_col in c.lower() or c.lower() in missing_col:
                        suggested_col = c
                        table_name = t
                        break

            root_cause = f"Schema Hallucination: The column '{missing_col}' does not exist in the database."
            if suggested_col and table_name:
                generalized_rule = (
                    f"In table '{table_name}', do not use '{missing_col}'. "
                    f"The valid column name for this concept is '{suggested_col}'."
                )
                trigger_pattern = f"{missing_col} {suggested_col} {table_name}"
            else:
                generalized_rule = (
                    f"Column '{missing_col}' does not exist. Inspect schema tables "
                    f"and use only verified columns from: {list(state.pruned_schema.keys())}."
                )
                trigger_pattern = f"{missing_col} column missing"

            return "COLUMN_HALLUCINATION", root_cause, {
                "error_category": "COLUMN_HALLUCINATION",
                "trigger_pattern": trigger_pattern,
                "generalized_rule": generalized_rule,
                "target_tables": [table_name] if table_name else list(state.pruned_schema.keys())
            }

        # 2. GROUP BY structural mismatch
        # e.g., SELECT region, market_type, SUM(profit) GROUP BY region
        has_aggregate = bool(re.search(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\(", sql, re.IGNORECASE))
        has_group_by = bool(re.search(r"\bGROUP\s+BY\b", sql, re.IGNORECASE))
        
        # Check if non-aggregated columns are missing from GROUP BY
        select_clause_match = re.search(r"SELECT\s+(.*?)\s+FROM", sql, re.IGNORECASE | re.DOTALL)
        if select_clause_match and has_aggregate:
            select_items = [s.strip() for s in select_clause_match.group(1).split(",")]
            non_agg_items = [
                item for item in select_items 
                if not re.search(r"\b(SUM|AVG|COUNT|MIN|MAX)\s*\(", item, re.IGNORECASE)
            ]
            
            if non_agg_items:
                if not has_group_by:
                    root_cause = "SQL Structural Error: Query contains aggregate function but omits GROUP BY clause for selected dimension attributes."
                    rule = "Whenever an aggregate function is used alongside dimension attributes in SELECT, include a GROUP BY clause listing all non-aggregated columns."
                    return "GROUP_BY_MISSING_CLAUSE", root_cause, {
                        "error_category": "GROUP_BY_MISSING_CLAUSE",
                        "trigger_pattern": "GROUP BY aggregate dimension attributes",
                        "generalized_rule": rule,
                        "target_tables": list(state.pruned_schema.keys())
                    }
                else:
                    # Check if any non_agg item is absent from GROUP BY
                    group_by_match = re.search(r"GROUP\s+BY\s+(.*?)(?:ORDER|LIMIT|HAVING|$)", sql, re.IGNORECASE | re.DOTALL)
                    if group_by_match:
                        group_cols = group_by_match.group(1).lower()
                        missing_in_group = [col for col in non_agg_items if col.lower() not in group_cols]
                        if missing_in_group or "market_type" in sql and "market_type" not in group_cols:
                            root_cause = "SQL Structural Error: Non-aggregated column in SELECT was omitted from the GROUP BY clause."
                            rule = (
                                "Whenever an aggregated column is selected with non-aggregated columns, "
                                "ensure ALL non-aggregated columns appear inside the GROUP BY clause."
                            )
                            return "GROUP_BY_MISSING_COLUMN", root_cause, {
                                "error_category": "GROUP_BY_MISSING_COLUMN",
                                "trigger_pattern": "GROUP BY market_type region aggregation",
                                "generalized_rule": rule,
                                "target_tables": ["dim_store", "fact_sales"]
                            }

        # 3. Security Guardrail Violation
        if "Security Violation" in err_msg:
            root_cause = f"Safety Violation: Non-SELECT operation blocked by SQLGlot guardrails ({err_msg})."
            rule = "Only generate read-only SELECT queries. Modifying data (UPDATE, DELETE, INSERT, DROP) is strictly forbidden."
            return "SECURITY_VIOLATION", root_cause, {
                "error_category": "SECURITY_VIOLATION",
                "trigger_pattern": "UPDATE DELETE DROP ALTER security",
                "generalized_rule": rule,
                "target_tables": list(state.pruned_schema.keys())
            }

        # 4. Generic Syntax or Join Error
        root_cause = f"Execution Failure: {err_msg}"
        rule = f"Avoid syntax pattern that led to: {err_msg}. Verify star-schema foreign key join relationships."
        return "GENERAL_SQL_ERROR", root_cause, {
            "error_category": "GENERAL_SQL_ERROR",
            "trigger_pattern": "join syntax schema relation",
            "generalized_rule": rule,
            "target_tables": list(state.pruned_schema.keys())
        }

    def run(self, state: AEMGState) -> AEMGState:
        category, root_cause, rule_dict = self.diagnose(state)
        state.root_cause = root_cause
        state.learned_repair_rule = rule_dict

        state.agent_logs.append(
            AgentLog(
                agent_name="ErrorDiagnosisAgent",
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                status="WARNING",
                message=f"Root Cause Identified: {root_cause}",
                details={
                    "error_category": category,
                    "generalized_repair_rule": rule_dict["generalized_rule"]
                }
            )
        )
        return state
