"""
AEMG Evaluation & Benchmarking Suite
Evaluates SQL generation accuracy, repair efficiency, and memory convergence over analytical queries.
Compares Unguided Baseline (traditional retries) vs AEMG (Error-Guided Memory Governance).
"""

from typing import List, Dict, Any
from graph import AEMGOrchestrator
from memory.governance import MemoryGovernance

BENCHMARK_QUERIES = [
    {
        "id": "Q1",
        "category": "Metric & Aggregation",
        "query": "Show total revenue and profit across all market types",
        "description": "Tests column hallucination ('revenue' vs 'gross_revenue') and GROUP BY correctness"
    },
    {
        "id": "Q2",
        "category": "Star-Schema Join",
        "query": "Find top product categories by gross revenue and total quantity sold",
        "description": "Tests multi-table join between fact_sales and dim_product"
    },
    {
        "id": "Q3",
        "category": "Multi-Dimension Grouping",
        "query": "Calculate total profit and gross revenue by region and market type",
        "description": "Tests multi-column GROUP BY alignment with dimension attributes"
    },
    {
        "id": "Q4",
        "category": "Customer Analytics",
        "query": "List total orders and gross revenue by customer segment and country",
        "description": "Tests customer dimension filtering and order count aggregation"
    },
    {
        "id": "Q5",
        "category": "Time-Series Aggregation",
        "query": "Analyze monthly gross revenue and profit trends across years",
        "description": "Tests date dimension joins and calendar hierarchy grouping"
    }
]

class AEMGBenchmark:
    def __init__(self, db_path: str = "datawarehouse.db"):
        self.db_path = db_path

    def run_benchmark(self, enable_memory: bool = True) -> Dict[str, Any]:
        """Runs the benchmark suite with or without memory governance."""
        orch = AEMGOrchestrator(db_path=self.db_path)
        
        if not enable_memory:
            # Clear memories for unguided baseline test
            orch.memory_gov.memories.clear()

        results = []
        total_queries = len(BENCHMARK_QUERIES)
        successful_queries = 0
        total_retries = 0

        for item in BENCHMARK_QUERIES:
            state = orch.run_pipeline(item["query"])
            is_success = state.execution_success
            if is_success:
                successful_queries += 1
            total_retries += state.retry_count
            
            results.append({
                "query_id": item["id"],
                "category": item["category"],
                "query": item["query"],
                "success": is_success,
                "retries": state.retry_count,
                "rows_returned": len(state.execution_result or []),
                "generated_sql": state.generated_sql,
                "error": state.execution_error or state.validation_error or None
            })

        accuracy = round((successful_queries / total_queries) * 100, 1)
        avg_retries = round(total_retries / total_queries, 2)

        return {
            "mode": "AEMG (Memory-Governed)" if enable_memory else "Baseline (Unguided)",
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "accuracy_pct": accuracy,
            "total_retries": total_retries,
            "avg_retries_per_query": avg_retries,
            "detailed_results": results,
            "memory_stats": orch.memory_gov.get_statistics()
        }
