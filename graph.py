"""
AEMG Multi-Agent Orchestrator
Implements the LangGraph-style stateful multi-agent execution loop with adaptive error-guided self-correction.
"""

from typing import Optional, Dict, Any, Callable
from agents.state import AEMGState, AgentLog
from database.db_manager import DatabaseManager
from memory.governance import MemoryGovernance
from agents.schema_introspection import SchemaIntrospectionAgent
from agents.schema_pruning import SchemaPruningAgent
from agents.sql_generator import SQLGenerationAgent
from agents.sql_validator import SQLValidationAgent
from agents.execution_agent import ExecutionAgent
from agents.error_diagnosis import ErrorDiagnosisAgent
from agents.memory_governance_agent import MemoryGovernanceAgent

class AEMGOrchestrator:
    def __init__(
        self,
        db_path: str = "datawarehouse.db",
        memory_store_path: str = "memory_store.json",
        ollama_url: str = "http://127.0.0.1:11434",
        model_name: str = "qwen2.5:7b",
        max_retries: int = 3
    ):
        self.db_manager = DatabaseManager(db_path=db_path)
        self.memory_gov = MemoryGovernance(persistence_path=memory_store_path)
        
        # Instantiate 7 Specialized Agents
        self.introspection_agent = SchemaIntrospectionAgent(self.db_manager)
        self.pruning_agent = SchemaPruningAgent()
        self.generator_agent = SQLGenerationAgent(ollama_url=ollama_url, model_name=model_name)
        self.validator_agent = SQLValidationAgent(dialect="sqlite")
        self.execution_agent = ExecutionAgent(self.db_manager)
        self.diagnosis_agent = ErrorDiagnosisAgent()
        self.governance_agent = MemoryGovernanceAgent(self.memory_gov)
        
        self.max_retries = max_retries

    def run_pipeline(
        self,
        query: str,
        step_callback: Optional[Callable[[str, AEMGState], None]] = None
    ) -> AEMGState:
        """
        Executes the full AEMG multi-agent workflow:
        Introspection -> Pruning -> Memory Retrieval -> Generation -> Validation -> Execution -> (Diagnosis & Memory Update if error)
        """
        state = AEMGState(query=query, max_retries=self.max_retries)

        def notify(step_name: str):
            if step_callback:
                step_callback(step_name, state)

        # Step 1: Schema Introspection
        notify("Schema Introspection")
        state = self.introspection_agent.run(state)

        # Step 2: Schema Pruning
        notify("Schema Pruning")
        state = self.pruning_agent.run(state)

        # Retry loop for Adaptive Error-Guided Execution
        while state.retry_count <= state.max_retries:
            # Step 3: Memory Governance Pre-Retrieval
            notify(f"Memory Retrieval (Attempt {state.retry_count + 1})")
            state = self.governance_agent.run_pre_retrieval(state)

            # Step 4: SQL Generation
            notify(f"SQL Generation (Attempt {state.retry_count + 1})")
            state = self.generator_agent.run(state)

            # Step 5: SQL Validation (SQLGlot)
            notify(f"SQLGlot Validation (Attempt {state.retry_count + 1})")
            state = self.validator_agent.run(state)

            if not state.is_valid_sql:
                # Validation error -> Trigger Diagnosis
                notify("Error Diagnosis (Validation Failure)")
                state = self.diagnosis_agent.run(state)
                state = self.governance_agent.run_post_execution(state)
                state.retry_count += 1
                if state.retry_count > state.max_retries:
                    break
                continue

            # Step 6: Execution
            notify(f"Database Execution (Attempt {state.retry_count + 1})")
            state = self.execution_agent.run(state)

            if state.execution_success:
                # Success -> Reinforce applied memories and finish
                notify("Memory Governance Reinforcement")
                state = self.governance_agent.run_post_execution(state)
                state.final_response = f"Successfully executed query and retrieved {len(state.execution_result or [])} record(s)."
                break
            else:
                # Database error -> Trigger Diagnosis & Memory Learning
                notify("Error Diagnosis (Execution Failure)")
                state = self.diagnosis_agent.run(state)
                state = self.governance_agent.run_post_execution(state)
                state.retry_count += 1
                if state.retry_count > state.max_retries:
                    break

        if not state.execution_success:
            state.final_response = f"Pipeline terminated after {state.retry_count} correction attempts. Last error: {state.execution_error or state.validation_error}"

        notify("Pipeline Completed")
        return state
