"""
Agent 1: Schema Introspection Agent
Directly reads database metadata catalogs without LLM parsing overhead.
"""

from datetime import datetime
from typing import Dict, Any
from agents.state import AEMGState, AgentLog
from database.db_manager import DatabaseManager

class SchemaIntrospectionAgent:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def run(self, state: AEMGState) -> AEMGState:
        t0 = datetime.now()
        schema = self.db_manager.get_catalog_schema()
        elapsed_ms = (datetime.now() - t0).total_seconds() * 1000
        
        state.full_schema = schema
        state.agent_logs.append(
            AgentLog(
                agent_name="SchemaIntrospectionAgent",
                timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                status="SUCCESS",
                message=f"Direct catalog introspection retrieved {len(schema)} tables in {elapsed_ms:.2f}ms.",
                details={"tables": list(schema.keys())}
            )
        )
        return state
