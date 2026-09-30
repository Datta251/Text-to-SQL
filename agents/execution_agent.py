"""
Agent 5: Execution Agent
Executes validated SQL against the database engine with SQLite fallback.
"""

from datetime import datetime
from agents.state import AEMGState, AgentLog
from database.db_manager import DatabaseManager

class ExecutionAgent:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def run(self, state: AEMGState) -> AEMGState:
        if not state.is_valid_sql:
            state.execution_success = False
            state.execution_error = state.validation_error or "Query failed SQLGlot validation."
            return state

        t0 = datetime.now()
        results, err = self.db_manager.execute_query(state.generated_sql)
        elapsed_ms = (datetime.now() - t0).total_seconds() * 1000

        if err:
            state.execution_success = False
            state.execution_error = err
            state.execution_result = None
            state.agent_logs.append(
                AgentLog(
                    agent_name="ExecutionAgent",
                    timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    status="ERROR",
                    message=f"Database execution error: {err}",
                    details={"error": err, "failed_sql": state.generated_sql}
                )
            )
        else:
            state.execution_success = True
            state.execution_error = None
            state.execution_result = results
            state.agent_logs.append(
                AgentLog(
                    agent_name="ExecutionAgent",
                    timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    status="SUCCESS",
                    message=f"Execution succeeded in {elapsed_ms:.2f}ms. Returned {len(results or [])} row(s).",
                    details={"row_count": len(results or []), "sample": results[:3] if results else []}
                )
            )

        return state
