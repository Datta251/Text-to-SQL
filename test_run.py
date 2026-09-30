from graph import AEMGOrchestrator

def main():
    print("Initializing AEMG Orchestrator...")
    orchestrator = AEMGOrchestrator()
    
    query = "Find total profit and revenue by region and market type"
    print(f"\n[Test Query]: '{query}'")
    
    state = orchestrator.run_pipeline(query)
    
    print("\n--- Pipeline Execution Summary ---")
    print(f"Success: {state.execution_success}")
    print(f"Retries: {state.retry_count}")
    print(f"Generated SQL:\n{state.generated_sql}")
    print(f"Rows Returned: {len(state.execution_result or [])}")
    if state.execution_result:
        print("Sample Result:", state.execution_result[:2])
    print(f"\nTotal Agent Logs: {len(state.agent_logs)}")
    for log in state.agent_logs:
        print(f"  [{log.timestamp}] [{log.status}] {log.agent_name}: {log.message}")

if __name__ == "__main__":
    main()
