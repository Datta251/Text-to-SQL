"""
Adaptive Error-Guided Memory Governance (AEMG)
Interactive Streamlit Dashboard & Multi-Agent Execution Environment
"""

import os
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import altair as alt
from graph import AEMGOrchestrator
from database.db_manager import DatabaseManager
from agents.sql_generator import SQLGenerationAgent
from benchmark.evaluator import AEMGBenchmark, BENCHMARK_QUERIES

st.set_page_config(
    page_title="AEMG Text-to-SQL Multi-Agent System",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for high-aesthetic enterprise UI
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .agent-card {
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        border-left: 4px solid #3B82F6;
        background-color: #F8FAFC;
    }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
    }
    .badge-success { background-color: #DCFCE7; color: #166534; }
    .badge-warning { background-color: #FEF3C7; color: #92400E; }
    .badge-error { background-color: #FEE2E2; color: #991B1B; }
    .badge-info { background-color: #DBEAFE; color: #1E40AF; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = AEMGOrchestrator()

orch = st.session_state.orchestrator

# Sidebar: System Configuration, Model Selection & Database Settings
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/database.png", width=60)
    st.title("AEMG Config")
    st.caption("Adaptive Error-Guided Memory Governance")

    # ----------------------------------------------------
    # SECTION 1: LLM Engine & Ollama Model Selector
    # ----------------------------------------------------
    st.subheader("🤖 LLM Engine & Model")
    
    # Check for installed local models in Ollama
    detected_models = SQLGenerationAgent.get_available_ollama_models()
    
    model_provider = st.radio(
        "Generation Mode:",
        ["Ollama (Local LLM)", "Offline Semantic Engine (Zero-Cloud)"],
        index=0 if detected_models else 1
    )
    
    if model_provider == "Ollama (Local LLM)":
        orch.generator_agent.provider = "ollama"
        if detected_models:
            st.success(f"Detected {len(detected_models)} local Ollama model(s)")
            selected_model = st.selectbox("Select Model:", detected_models)
        else:
            st.info("💡 Ollama running? You can specify any model tag below (e.g. `qwen2.5:7b`, `llama3.2:3b`).")
            selected_model = st.text_input("Ollama Model Tag:", value="qwen2.5:7b")
        
        # User can also type a custom model tag
        custom_tag = st.text_input("Or type custom tag (optional):", placeholder="e.g. qwen2.5-coder:7b")
        final_model_name = custom_tag.strip() if custom_tag.strip() else selected_model
        orch.generator_agent.model_name = final_model_name
        st.caption(f"Active Model: **`{final_model_name}`**")
    else:
        orch.generator_agent.provider = "offline"
        st.caption("Active Model: **Built-in Offline Semantic Engine** (No downloads needed)")

    st.divider()

    # ----------------------------------------------------
    # SECTION 2: Database Connection & Switching
    # ----------------------------------------------------
    st.subheader("🗄️ Database Connection")
    db_type = st.radio("Database Type:", ["SQLite", "PostgreSQL"], index=0)
    
    if db_type == "SQLite":
        current_db = getattr(orch.db_manager, "db_path", "datawarehouse.db")
        new_db_path = st.text_input("SQLite Database File:", value=current_db)
        c_db1, c_db2 = st.columns(2)
        with c_db1:
            if st.button("Connect DB", width="stretch"):
                orch.db_manager.set_sqlite_db(new_db_path)
                st.success(f"Switched to {os.path.basename(new_db_path)}")
                st.rerun()
        with c_db2:
            if st.button("Reseed Data", width="stretch"):
                orch.db_manager.init_sqlite_warehouse(force_recreate=True)
                st.success("Reseeded with 5,000 star-schema records!")
                st.rerun()
    else:
        st.caption("Enter PostgreSQL connection string:")
        pg_conn = st.text_input("PG Connection URI:", value="postgresql://postgres:postgres@localhost:5432/enterprise_dw")
        if st.button("Connect to PostgreSQL", width="stretch"):
            success, err_msg = orch.db_manager.set_postgres_db(pg_conn)
            if success:
                st.success("Successfully connected to PostgreSQL Enterprise Warehouse!")
                st.rerun()
            else:
                st.error(f"Connection failed: {err_msg}")

    st.caption(f"Active Engine: `{orch.db_manager.active_engine}`")

    st.divider()

    # ----------------------------------------------------
    # SECTION 3: Memory Hyperparameters
    # ----------------------------------------------------
    st.subheader("⚙️ Memory Hyperparameters")
    pruning_threshold = st.slider("Pruning Threshold (θ)", min_value=0.1, max_value=0.7, value=0.35, step=0.05)
    decay_lambda = st.slider("Exponential Decay Rate (λ)", min_value=0.01, max_value=0.20, value=0.05, step=0.01)
    max_retries = st.slider("Max Self-Healing Retries", min_value=1, max_value=5, value=3)

    orch.memory_gov.pruning_threshold = pruning_threshold
    orch.max_retries = max_retries

# Main Title Area
st.markdown('<div class="main-title">Adaptive Error-Guided Memory Governance (AEMG)</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">A Schema-Aware Multi-Agent Framework for Reliable Text-to-SQL Systems</div>', unsafe_allow_html=True)

# Top Metric Cards
mem_stats = orch.memory_gov.get_statistics()
col_m1, col_m2, col_m3, col_m4 = st.columns(4)
with col_m1:
    st.metric("Governed Memories", mem_stats["total_count"], delta=f"{len(mem_stats['category_counts'])} categories")
with col_m2:
    st.metric("Avg Memory Confidence", f"{mem_stats['avg_confidence'] * 100:.1f}%")
with col_m3:
    active_llm_label = orch.generator_agent.model_name if orch.generator_agent.provider == "ollama" else "Offline Engine"
    st.metric("Active LLM", active_llm_label, delta=orch.generator_agent.provider.upper())
with col_m4:
    st.metric("Active DB", os.path.basename(orch.db_manager.db_path) if not orch.db_manager.is_postgres else "PostgreSQL", delta="Star-Schema")

# Navigation Tabs
tab_query, tab_memory, tab_schema, tab_benchmark = st.tabs([
    "💬 Text-to-SQL Query Studio",
    "🧠 Governed Memory Lab",
    "🗄️ Star-Schema Explorer",
    "📊 Reliability Benchmark"
])

# ==============================================================================
# TAB 1: Query Studio
# ==============================================================================
with tab_query:
    col_input, col_examples = st.columns([2.5, 1.5])
    
    with col_examples:
        st.markdown("##### 📌 Research Paper Test Cases")
        preset_choice = st.selectbox(
            "Quick Load Example:",
            [
                "Custom Query...",
                "Case 1: Total profit and revenue by region and market type (Group By + Hallucination)",
                "Case 2: Top product categories by sales quantity and profit (Multi-Table Join)",
                "Case 3: Customer segment revenue and order volume (Customer Dimension)",
                "Case 4: Monthly revenue trends across years (Date Dimension Hierarchy)",
                "Case 5: Security Test (Attempt UPDATE/DELETE Statement)"
            ]
        )
        
        preset_mapping = {
            "Case 1: Total profit and revenue by region and market type (Group By + Hallucination)": "Find total profit and revenue by region and market type",
            "Case 2: Top product categories by sales quantity and profit (Multi-Table Join)": "Find top product categories by gross revenue and total quantity sold",
            "Case 3: Customer segment revenue and order volume (Customer Dimension)": "List total orders and gross revenue by customer segment and country",
            "Case 4: Monthly revenue trends across years (Date Dimension Hierarchy)": "Analyze monthly gross revenue and profit trends across years",
            "Case 5: Security Test (Attempt UPDATE/DELETE Statement)": "UPDATE fact_sales SET profit = 0"
        }

    with col_input:
        default_q = preset_mapping.get(preset_choice, "")
        user_query = st.text_area(
            "Natural Language Business Question:",
            value=default_q or "Find total profit and revenue by region and market type",
            height=90
        )
        run_btn = st.button("🚀 Execute AEMG Multi-Agent Pipeline", type="primary", width="stretch")

    if run_btn and user_query:
        with st.spinner("Multi-Agent Workflow executing..."):
            pipeline_state = orch.run_pipeline(user_query)

        st.divider()

        # Display Pipeline Execution Status
        if pipeline_state.execution_success:
            st.success(f"✨ **Execution Succeeded!** {pipeline_state.final_response} (Retries: {pipeline_state.retry_count})")
        else:
            st.error(f"❌ **Execution Failed:** {pipeline_state.final_response}")

        # Agent Workflow Tracing
        with st.expander("🔍 Multi-Agent Execution Trace & Governance Lifecycle", expanded=True):
            for log in pipeline_state.agent_logs:
                badge_class = {
                    "SUCCESS": "badge-success",
                    "WARNING": "badge-warning",
                    "ERROR": "badge-error",
                    "INFO": "badge-info"
                }.get(log.status, "badge-info")

                st.markdown(
                    f"""<div class="agent-card">
                        <span class="badge {badge_class}">{log.status}</span>
                        <strong>{log.agent_name}</strong> <small style="color:gray;">({log.timestamp})</small><br/>
                        {log.message}
                    </div>""",
                    unsafe_allow_html=True
                )
                if log.details:
                    with st.expander(f"Details: {log.agent_name}", expanded=False):
                        st.json(log.details)

        # SQL and Data Results
        st.subheader("Generated SQL & Result")
        st.code(pipeline_state.generated_sql, language="sql")

        if pipeline_state.execution_result:
            df = pd.DataFrame(pipeline_state.execution_result)
            st.dataframe(df, width="stretch")

            # Auto-visualize if chartable columns exist
            numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
            text_cols = df.select_dtypes(include=["object", "string", "str"]).columns.tolist()

            if len(text_cols) >= 1 and len(numeric_cols) >= 1:
                st.subheader("📈 Visual Insight")
                x_axis = text_cols[0]
                y_axis = numeric_cols[0]
                chart = alt.Chart(df).mark_bar().encode(
                    x=alt.X(x_axis, sort="-y"),
                    y=y_axis,
                    tooltip=df.columns.tolist()
                ).properties(height=320)
                st.altair_chart(chart, width="stretch")

# ==============================================================================
# TAB 2: Governed Memory Lab
# ==============================================================================
with tab_memory:
    st.subheader("Governed Repair Knowledge Base")
    st.caption("Unlike conventional systems that store failed SQL queries, AEMG extracts and stores generalized repair knowledge with self-governing confidence scores.")

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Apply Temporal Decay Step", width="stretch"):
            pruned = orch.memory_gov.apply_temporal_decay(decay_multiplier=1.0)
            st.info(f"Applied mathematical decay C(t) = C * e^(-λ). Pruned {len(pruned)} stale rule(s).")
            st.rerun()
    with col_btn2:
        if st.button("Prune Low Confidence (< θ)", width="stretch"):
            pruned = orch.memory_gov.prune_stale_memories()
            st.info(f"Pruned {len(pruned)} memory rule(s) below threshold {orch.memory_gov.pruning_threshold}.")
            st.rerun()
    with col_btn3:
        if st.button("Restore Default Foundational Rules", width="stretch"):
            orch.memory_gov._seed_default_foundational_memories()
            st.success("Default enterprise repair memories restored.")
            st.rerun()

    # List Memory Items
    memories = list(orch.memory_gov.memories.values())
    if not memories:
        st.warning("Memory store is currently empty. Execute queries with errors to trigger self-learning.")
    else:
        for mem in memories:
            with st.container():
                c1, c2, c3 = st.columns([1.2, 3, 1.2])
                with c1:
                    st.markdown(f"**ID:** `{mem.id}`")
                    st.markdown(f"**Category:** `{mem.error_category}`")
                    st.markdown(f"**Target Tables:** {', '.join(mem.target_tables) if mem.target_tables else 'All'}")
                with c2:
                    st.markdown(f"**Generalized Repair Rule:**\n> {mem.generalized_rule}")
                    st.caption(f"Trigger Keywords: `{mem.trigger_pattern}`")
                with c3:
                    st.markdown(f"**Confidence:** `{mem.confidence_score * 100:.1f}%`")
                    st.progress(mem.confidence_score)
                    st.caption(f"Used: {mem.usage_count} | Succeeded: {mem.success_count} | Failed: {mem.failure_count}")
                st.divider()

    # Manual Rule Addition
    with st.expander("➕ Register Custom Enterprise Repair Knowledge"):
        with st.form("add_rule_form"):
            new_cat = st.selectbox("Error Category", ["COLUMN_HALLUCINATION", "GROUP_BY_MISSING_COLUMN", "STAR_SCHEMA_JOIN", "SYNTAX_SAFETY", "GENERAL_SQL_ERROR"])
            new_pattern = st.text_input("Trigger Pattern / Keywords", "revenue turnover gross_revenue")
            new_rule = st.text_area("Generalized Repair Rule", "Always map monetary transaction queries to fact_sales.gross_revenue.")
            new_conf = st.slider("Initial Confidence", 0.5, 1.0, 0.85)
            if st.form_submit_button("Save Repair Rule"):
                orch.memory_gov.add_memory(
                    error_category=new_cat,
                    trigger_pattern=new_pattern,
                    generalized_rule=new_rule,
                    initial_confidence=new_conf
                )
                st.success("Custom rule added to AEMG knowledge base!")
                st.rerun()

# ==============================================================================
# TAB 3: Schema Explorer
# ==============================================================================
with tab_schema:
    st.subheader("Star-Schema Enterprise Data Warehouse")
    st.caption("Evaluated on a star-schema sales data warehouse containing dimension & fact tables.")

    schema = orch.db_manager.get_catalog_schema()
    for tbl_name, tbl_meta in schema.items():
        with st.expander(f"Table: {tbl_name} ({len(tbl_meta['columns'])} columns)", expanded=(tbl_name == "fact_sales")):
            c_cols, c_sample = st.columns([1.5, 2.5])
            with c_cols:
                st.markdown("**Columns & Types:**")
                col_df = pd.DataFrame(tbl_meta["columns"])[["name", "type", "pk", "notnull"]]
                st.dataframe(col_df, width="stretch")
                
                if tbl_meta["foreign_keys"]:
                    st.markdown("**Foreign Key Links:**")
                    for fk in tbl_meta["foreign_keys"]:
                        st.markdown(f"- `{fk['from_column']}` ➡️ `{fk['target_table']}.{fk['target_column']}`")
            with c_sample:
                st.markdown("**Sample Data Preview:**")
                sample_rows, _ = orch.db_manager.execute_query(f"SELECT * FROM {tbl_name} LIMIT 5")
                if sample_rows:
                    st.dataframe(pd.DataFrame(sample_rows), width="stretch")

# ==============================================================================
# TAB 4: Reliability Benchmark
# ==============================================================================
with tab_benchmark:
    st.subheader("AEMG Evaluation & Reliability Benchmark")
    st.caption("Directly evaluates the paper's core hypothesis: Adaptive Error-Guided Memory Governance delivers higher accuracy and fewer repeated correction attempts.")

    benchmark_suite = AEMGBenchmark()
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        if st.button("Run Benchmark: AEMG (With Memory Governance)", type="primary", width="stretch"):
            with st.spinner("Running benchmark suite with memory guidance..."):
                aemg_res = benchmark_suite.run_benchmark(enable_memory=True)
                st.session_state.last_benchmark_aemg = aemg_res
    with col_b2:
        if st.button("Run Benchmark: Baseline (Unguided / Without Memory)", width="stretch"):
            with st.spinner("Running unguided baseline benchmark..."):
                base_res = benchmark_suite.run_benchmark(enable_memory=False)
                st.session_state.last_benchmark_base = base_res

    if "last_benchmark_aemg" in st.session_state or "last_benchmark_base" in st.session_state:
        st.divider()
        b_col1, b_col2 = st.columns(2)
        
        with b_col1:
            if "last_benchmark_aemg" in st.session_state:
                res = st.session_state.last_benchmark_aemg
                st.markdown("### 🏆 AEMG Framework (Memory-Governed)")
                st.metric("Accuracy", f"{res['accuracy_pct']}%", delta=f"{res['successful_queries']}/{res['total_queries']} Succeeded")
                st.metric("Average Retries per Query", f"{res['avg_retries_per_query']}")
                st.dataframe(pd.DataFrame(res["detailed_results"])[["query_id", "query", "success", "retries"]], width="stretch")

        with b_col2:
            if "last_benchmark_base" in st.session_state:
                res = st.session_state.last_benchmark_base
                st.markdown("### ⚠️ Baseline System (Unguided Retries)")
                st.metric("Accuracy", f"{res['accuracy_pct']}%", delta=f"{res['successful_queries']}/{res['total_queries']} Succeeded")
                st.metric("Average Retries per Query", f"{res['avg_retries_per_query']}")
                st.dataframe(pd.DataFrame(res["detailed_results"])[["query_id", "query", "success", "retries"]], width="stretch")
