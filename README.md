# Adaptive Error-Guided Memory Governance (AEMG) for Multi-Agent Analytical Reasoning

### *A Schema-Aware Memory Framework for Reliable Text-to-SQL Systems*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Multi-Agent](https://img.shields.io/badge/Architecture-LangGraph%20Multi--Agent-orange.svg)](#system-architecture)
[![Safety](https://img.shields.io/badge/Security-SQLGlot%20AST%20Guardrails-green.svg)](#4-sql-validation-agent)
[![Model](https://img.shields.io/badge/LLM-Ollama%20%7C%20Qwen2.5--7B-purple.svg)](#technology-stack)
[![Database](https://img.shields.io/badge/Warehouse-Star--Schema%20Enterprise-red.svg)](#star-schema-data-warehouse)

---

## Executive Summary

While Large Language Models (LLMs) make enterprise database querying accessible via natural language, conventional Text-to-SQL architectures face critical bottlenecks when deployed in production:
1. **Enterprise Data Privacy:** Strict regulations (GDPR, HIPAA) preclude shipping proprietary schemas and query streams to third-party cloud APIs.
2. **Schema Hallucinations:** Smaller local open-source models frequently hallucinate column names (e.g., using `revenue` instead of `gross_revenue`).
3. **SQL Structural Failures:** Models frequently generate invalid SQL, such as omitting non-aggregated columns (`market_type`) from `GROUP BY` clauses.
4. **Context Saturation:** Massive enterprise schemas inflate prompt size, increasing inference latency and hallucination rates.
5. **Absence of Long-Term Learning:** Traditional systems treat each query independently. When a query fails, they apply blind prompt retries without extracting generalized repair lessons.

**Adaptive Error-Guided Memory Governance (AEMG)** solves these issues through a stateful multi-agent workflow that learns from execution and validation failures. Instead of caching brittle raw SQL queries, AEMG extracts **generalized repair knowledge**, stores it in a governed memory system with mathematical confidence scoring, and applies temporal decay to maintain high knowledge quality.

---

## System Architecture

The framework coordinates seven specialized agents in an iterative self-healing cycle:

```mermaid
flowchart TD
    UserQuery([User Natural Language Query]) --> Agent1[1. Schema Introspection Agent]
    Agent1 --> Agent2[2. Schema Pruning Agent]
    Agent2 --> Agent7Pre[7. Memory Governance Agent\n(Pre-Retrieval)]
    
    subgraph MultiAgentLoop [Adaptive Self-Correction Loop]
        Agent7Pre --> Agent3[3. SQL Generation Agent\n(Ollama Qwen2.5-7B / Local Engine)]
        Agent3 --> Agent4[4. SQL Validation Agent\n(SQLGlot AST Guardrails)]
        Agent4 -- Invalid Syntax / Mutation --> Agent6[6. Error Diagnosis Agent]
        Agent4 -- Valid SELECT --> Agent5[5. Execution Agent\n(PostgreSQL / SQLite Fallback)]
        Agent5 -- Database Error --> Agent6
        Agent6 -- Synthesize Repair Knowledge --> Agent7Post[7. Memory Governance Agent\n(Register New Rule / Penalize)]
        Agent7Post -- Retry with Repair Context --> Agent3
    end
    
    Agent5 -- Success (Records Returned) --> Reinforce[Memory Governance Reinforcement\nBoost Confidence Score]
    Reinforce --> FinalResult([Formatted Result & Visual Dashboard])
```

### The 7 Specialized Agents

1. **Schema Introspection Agent:** Directly reads database catalogs (`sqlite_master`, `PRAGMA table_info`, `PRAGMA foreign_key_list`, or PostgreSQL `information_schema`) in sub-milliseconds without LLM overhead.
2. **Schema Pruning Agent:** Selects only relevant tables and columns for the query, reducing prompt token size by 60–80% and drastically cutting hallucinations.
3. **SQL Generation Agent:** Synthesizes SQL using the pruned schema along with high-confidence repair rules retrieved from memory.
4. **SQL Validation Agent:** Parses generated SQL with **SQLGlot** AST. Strictly blocks non-SELECT statements (`UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `INSERT`) and detects syntax errors before database execution.
5. **Execution Agent:** Runs validated SQL against the primary database (PostgreSQL) or automatically switches to the star-schema SQLite database on connection failure.
6. **Error Diagnosis Agent:** Triggered on failure. Dissects runtime or validation errors (e.g. missing columns, `GROUP BY` column omissions, foreign key join paths) and extracts generalized, reusable repair strategies.
7. **Memory Governance Agent:** Manages repair memories with confidence scores $C \in [0.0, 1.0]$. Boosts confidence on query success, penalizes on failure, applies exponential temporal decay $C(t) = C_0 \cdot e^{-\lambda t}$, and prunes stale memories.

---

## Star-Schema Data Warehouse

The prototype implements a star-schema enterprise sales data warehouse:

| Table | Type | Key Columns |
| :--- | :--- | :--- |
| `fact_sales` | Fact | `sale_id`, `customer_id`, `product_id`, `store_id`, `date_id`, `quantity`, `unit_price`, `discount`, `gross_revenue`, `profit` |
| `dim_customer` | Dimension | `customer_id`, `customer_name`, `customer_segment`, `country`, `city`, `state` |
| `dim_product` | Dimension | `product_id`, `product_name`, `category`, `sub_category`, `unit_cost` |
| `dim_store` | Dimension | `store_id`, `store_name`, `region`, `market_type`, `store_size` |
| `dim_date` | Dimension | `date_id`, `full_date`, `year`, `quarter`, `month`, `month_name`, `day_of_week` |

> [!NOTE]
> Column names intentionally mirror the exact scenarios from the paper (e.g., `gross_revenue` vs `revenue`, and `market_type` + `region` with `SUM(profit)`).

---

## Quick Start Guide

### 1. Installation & Environment

Navigate to the project directory:
```powershell
cd C:\Users\Datta\.gemini\antigravity-ide\scratch\aemg-text2sql
```

The core dependencies are pre-installed in your environment:
- `sqlglot`
- `pydantic`
- `streamlit`
- `pandas`
- `altair`

### 2. Launch the Streamlit Interactive Dashboard

Run:
```powershell
python -m streamlit run app.py
```

The dashboard will open at `http://localhost:8501` featuring:
- **💬 Text-to-SQL Query Studio:** Interactive query execution with step-by-step multi-agent visual trace.
- **🧠 Governed Memory Lab:** Real-time inspection of repair rules, confidence meters, and interactive decay simulation ($C(t) = C_0 \cdot e^{-\lambda t}$).
- **🗄️ Star-Schema Explorer:** Live schema explorer, foreign key visualizer, and data previews.
- **📊 Reliability Benchmark:** Automated evaluation comparing Unguided Baseline vs AEMG Memory Governance.

### 3. CLI Runner

You can also run queries directly in the terminal:
```powershell
python run_cli.py "Find total profit and revenue by region and market type"
```

To run the automated benchmark suite:
```powershell
python test_benchmark.py
```

To run the self-healing learning loop test:
```powershell
python test_learning_loop.py
```

---

## Connecting Local Ollama (Qwen2.5-7B)

The system is configured to run fully offline. If you have Ollama installed and want to run live model inference:

1. Pull the model:
   ```powershell
   ollama run qwen2.5:7b
   ```
2. Start or ensure the Ollama service is running on `http://127.0.0.1:11434`.
3. In the Streamlit sidebar, select **Ollama (Qwen2.5-7B Local)**.
4. When Ollama is offline or model weights are downloading, the system automatically falls back to the embedded zero-cloud analytical generator, ensuring continuous operation.
