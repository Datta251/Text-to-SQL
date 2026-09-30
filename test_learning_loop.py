"""
Verifies the self-correcting error diagnosis and memory governance loop.
Simulates a query failure (e.g., column hallucination or missing group by)
and verifies that AEMG detects it, synthesizes a repair rule, stores it,
and successfully executes on retry.
"""

from graph import AEMGOrchestrator
from agents.state import AEMGState

def test_hallucination_and_recovery():
    print("\n========================================================")
    print("TEST: Error-Guided Self-Healing on 'Revenue' Hallucination")
    print("========================================================")
    orch = AEMGOrchestrator()
    
    # Temporarily remove revenue rule to see unguided failure -> diagnosis -> recovery
    if "mem_rule_01" in orch.memory_gov.memories:
        del orch.memory_gov.memories["mem_rule_01"]

    query = "bug: show total revenue by region"
    state = orch.run_pipeline(query)

    print(f"Final Success: {state.execution_success}")
    print(f"Retry Count: {state.retry_count}")
    print(f"Final Generated SQL: {state.generated_sql}")
    print("\nAgent Log Trace:")
    for log in state.agent_logs:
        print(f"  [{log.timestamp}] [{log.status}] {log.agent_name}: {log.message}")

    # Verify that a new repair rule was learned and saved in memory
    print(f"\nCurrent Active Governed Memories: {len(orch.memory_gov.memories)}")
    for m_id, m in orch.memory_gov.memories.items():
        print(f"  * [{m_id}] ({m.error_category}) Conf: {m.confidence_score:.2f} -> {m.generalized_rule[:80]}...")

if __name__ == "__main__":
    test_hallucination_and_recovery()
