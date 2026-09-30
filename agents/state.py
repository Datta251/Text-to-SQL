"""
State schema for the AEMG Multi-Agent Workflow.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class AgentLog(BaseModel):
    agent_name: str
    timestamp: str
    status: str  # "SUCCESS", "WARNING", "ERROR", "INFO"
    message: str
    details: Optional[Dict[str, Any]] = None

class AEMGState(BaseModel):
    query: str
    full_schema: Dict[str, Any] = Field(default_factory=dict)
    pruned_tables: List[str] = Field(default_factory=list)
    pruned_schema: Dict[str, Any] = Field(default_factory=dict)
    retrieved_memories: List[Dict[str, Any]] = Field(default_factory=list)
    
    # SQL Generation & Validation
    generated_sql: str = ""
    is_valid_sql: bool = False
    validation_error: Optional[str] = None
    ast_representation: Optional[str] = None
    
    # Execution
    execution_result: Optional[List[Dict[str, Any]]] = None
    execution_error: Optional[str] = None
    execution_success: bool = False
    
    # Error Diagnosis & Memory Governance
    retry_count: int = 0
    max_retries: int = 3
    root_cause: Optional[str] = None
    learned_repair_rule: Optional[Dict[str, Any]] = None
    applied_memory_ids: List[str] = Field(default_factory=list)
    
    # Trace Logs
    agent_logs: List[AgentLog] = Field(default_factory=list)
    final_response: str = ""
