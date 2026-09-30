"""
AEMG Interactive CLI Runner
Allows running natural language queries, inspecting multi-agent logs,
and managing memory governance from the command line.
"""

import sys
from graph import AEMGOrchestrator

def main():
    print("=" * 70)
    print(" Adaptive Error-Guided Memory Governance (AEMG) CLI")
    print(" A Schema-Aware Memory Framework for Reliable Text-to-SQL Systems")
    print("=" * 70)
    
    orch = AEMGOrchestrator()
    
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = input("\nEnter Natural Language Query (or press Enter for default):\n> ").strip()
        if not query:
            query = "Find total profit and revenue by region and market type"

    print(f"\n[Processing Query]: '{query}'")
    state = orch.run_pipeline(query)

    print("\n" + "=" * 50)
    print(" MULTI-AGENT EXECUTION TRACE")
    print("=" * 50)
    for log in state.agent_logs:
        print(f"[{log.timestamp}] [{log.status:<7}] {log.agent_name:<24}: {log.message}")

    print("\n" + "=" * 50)
    print(" GENERATED SQL (SQLGlot Validated)")
    print("=" * 50)
    print(state.generated_sql)

    print("\n" + "=" * 50)
    print(" EXECUTION RESULTS")
    print("=" * 50)
    if state.execution_success:
        rows = state.execution_result or []
        print(f"Success! {len(rows)} record(s) returned.\n")
        if rows:
            headers = list(rows[0].keys())
            header_line = " | ".join(f"{h:<18}" for h in headers)
            print(header_line)
            print("-" * len(header_line))
            for r in rows[:10]:
                print(" | ".join(f"{str(r[h]):<18}" for h in headers))
            if len(rows) > 10:
                print(f"... and {len(rows) - 10} more rows.")
    else:
        print(f"FAILED: {state.execution_error or state.validation_error}")

if __name__ == "__main__":
    main()
