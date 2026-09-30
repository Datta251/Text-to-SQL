"""
Agent 4: SQL Validation Agent
Uses SQLGlot to parse SQL AST and enforce strict enterprise safety guardrails.
Blocks UPDATE, DELETE, DROP, ALTER, INSERT, TRUNCATE statements.
Ensures only valid, syntactically clean SELECT queries proceed.
"""

from datetime import datetime
from typing import Tuple, Optional
import sqlglot
from sqlglot import exp
from agents.state import AEMGState, AgentLog

class SQLValidationAgent:
    def __init__(self, dialect: str = "sqlite"):
        self.dialect = dialect
        # Strictly disallowed SQL AST expression types
        self.forbidden_expressions = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Drop,
            exp.Alter,
            exp.TruncateTable,
            exp.Create,
            exp.Command
        )

    def validate(self, sql_query: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Parses SQL with SQLGlot, validates AST, and verifies safety.
        Returns: (is_valid, ast_representation, error_message)
        """
        if not sql_query or not sql_query.strip():
            return False, None, "SQL query string is empty."

        clean_sql = sql_query.strip().rstrip(";")

        # 1. Parse AST
        try:
            parsed_trees = sqlglot.parse(clean_sql, read=self.dialect)
            if not parsed_trees:
                return False, None, "SQLGlot was unable to parse query."
            
            tree = parsed_trees[0]
            if tree is None:
                return False, None, "Empty SQL syntax tree."
        except Exception as e:
            return False, None, f"SQLGlot Syntax Error: {str(e)}"

        # 2. Check for unsafe / mutating expressions
        for node in tree.walk():
            if isinstance(node, self.forbidden_expressions):
                forbidden_type = type(node).__name__.upper()
                return False, None, f"Security Violation: Statement contains forbidden mutation operator '{forbidden_type}'. Only read-only SELECT queries are allowed."

        # 3. Ensure root is a Select or Union of Selects
        if not isinstance(tree, (exp.Select, exp.Union)):
            return False, None, f"Security Violation: Root statement must be a SELECT query, found '{type(tree).__name__}'."

        ast_repr = repr(tree)
        return True, ast_repr, None

    def run(self, state: AEMGState) -> AEMGState:
        sql = state.generated_sql
        is_valid, ast_repr, err = self.validate(sql)

        state.is_valid_sql = is_valid
        state.ast_representation = ast_repr
        state.validation_error = err

        if is_valid:
            state.agent_logs.append(
                AgentLog(
                    agent_name="SQLValidationAgent",
                    timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    status="SUCCESS",
                    message="SQLGlot parsed query successfully. Security guardrails verified (Safe SELECT).",
                    details={"ast_snippet": (ast_repr[:200] + "...") if ast_repr and len(ast_repr) > 200 else ast_repr}
                )
            )
        else:
            state.agent_logs.append(
                AgentLog(
                    agent_name="SQLValidationAgent",
                    timestamp=datetime.now().strftime("%H:%M:%S.%f")[:-3],
                    status="ERROR",
                    message=f"Validation failed: {err}",
                    details={"failed_sql": sql, "error": err}
                )
            )

        return state
