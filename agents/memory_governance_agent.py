"""
Agent 7: Memory Governance Agent
Interfaces between the execution workflow and the persistent governed memory store.
Reinforces successful memories, adds newly learned generalized repair rules,
and manages confidence scores and pruning.
"""

from datetime import datetime
from agents.state import AEMGState, AgentLog
from memory.governance import MemoryGovernance

class MemoryGovernanceAgent:
    def __init__(self, memory_governance: MemoryGovernance):
        self.memory_gov = memory_governance

    def run_pre_retrieval(self, state: AEMGState) -> AEMGState:
        """
        Retrieves top relevant generalized repair memories before SQL generation.
        """
        relevant_memories = self.memory_gov.retrieve_relevant_memories(
            query=state.query,
            active_tables=state.pruned_tables,
            top_k=3
        )
        
        state.retrieved_memories = [m.model_dump() for m in relevant_memories]
        state.applied_memory_ids = [m.id for m in relevant_memories]

        state.agent_logs.append(
            AgentLog(
                agent_name="MemoryGovernanceAgent",
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                status="INFO",
                message=f"Retrieved {len(relevant_memories)} active repair memories with high confidence.",
                details={
                    "retrieved_rule_ids": state.applied_memory_ids,
                    "rules": [m.generalized_rule for m in relevant_memories]
                }
            )
        )
        return state

    def run_post_execution(self, state: AEMGState) -> AEMGState:
        """
        Updates memory governance after execution outcome:
        - If query succeeded: reinforce applied memories (+confidence).
        - If query failed: penalize failing memories (-confidence) and register new repair rule.
        """
        if state.execution_success:
            # Reward applied memories
            for mem_id in state.applied_memory_ids:
                self.memory_gov.record_feedback(mem_id, success=True)
            
            state.agent_logs.append(
                AgentLog(
                    agent_name="MemoryGovernanceAgent",
                    timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    status="SUCCESS",
                    message="Query executed successfully. Confidence scores of applied repair memories boosted.",
                    details={"reinforced_ids": state.applied_memory_ids}
                )
            )
        else:
            # Penalize applied memories that failed to prevent the error
            for mem_id in state.applied_memory_ids:
                self.memory_gov.record_feedback(mem_id, success=False)

            # Store new learned repair knowledge
            if state.learned_repair_rule:
                new_item = self.memory_gov.add_memory(
                    error_category=state.learned_repair_rule["error_category"],
                    trigger_pattern=state.learned_repair_rule["trigger_pattern"],
                    generalized_rule=state.learned_repair_rule["generalized_rule"],
                    target_tables=state.learned_repair_rule.get("target_tables", []),
                    initial_confidence=0.88
                )
                
                state.agent_logs.append(
                    AgentLog(
                        agent_name="MemoryGovernanceAgent",
                        timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                        status="INFO",
                        message=f"Registered newly learned generalized repair rule '{new_item.id}' into memory store.",
                        details=new_item.model_dump()
                    )
                )

        return state
