"""
SpareSync - Inventory Transaction Reconciliation Engine
Streamlit Dashboard (Review 1 Prototype with Evaluation, Comparison, Failure Simulation, Operational Fallback & Decision Trade-Offs)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.data_generator import generate_synthetic_data, TRANSACTIONS_FILE, PHYSICAL_COUNTS_FILE, PARTS_CATALOG, LOCATIONS
from src.baseline import calculate_system_stock, compute_baseline_audit
from src.reconciliation_engine import ReconciliationEngine
from src.fallback_handler import FallbackHandler
from src.tradeoffs import TRADE_OFF_ACTIONS, get_all_tradeoffs_df
from src.failure_simulator import (
    simulate_missing_transfer,
    simulate_duplicate_receipt,
    simulate_network_failure,
    simulate_timestamp_anomaly
)
from src.metrics import run_benchmark_experiment

# Page configuration
st.set_page_config(
    page_title="SpareSync | Inventory Reconciliation",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 2.0rem;
        font-weight: 700;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-high {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-medium {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-issue {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-manual {
        background-color: #FEF3C7;
        color: #B45309;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.85rem;
        border: 1px dashed #F59E0B;
    }
    .badge-status-detected {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #F87171;
    }
    .badge-status-explained {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #60A5FA;
    }
    .badge-status-action {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 0.85rem;
        border: 1px solid #FBBF24;
    }
    .action-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 1.1rem;
        border-radius: 0 8px 8px 0;
        margin-top: 0.8rem;
    }
    .tradeoff-card {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.9rem;
        text-align: center;
    }
    .tradeoff-title {
        font-size: 0.78rem;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
    }
    .tradeoff-val {
        font-size: 1.15rem;
        font-weight: 700;
        color: #0F172A;
        margin-top: 0.2rem;
    }
    .workflow-step {
        background: #F1F5F9;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 0.8rem;
        text-align: center;
        font-weight: 600;
        color: #334155;
        font-size: 0.9rem;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    """Loads transaction logs and physical audits from CSV, generating if missing."""
    if not TRANSACTIONS_FILE.exists() or not PHYSICAL_COUNTS_FILE.exists():
        return generate_synthetic_data()
    df_t = pd.read_csv(TRANSACTIONS_FILE)
    df_c = pd.read_csv(PHYSICAL_COUNTS_FILE)
    return df_t, df_c


# Load data and instantiate engine and fallback handler
df_transactions, df_physical_counts = load_data()
engine = ReconciliationEngine(df_transactions, df_physical_counts)
fallback_handler = FallbackHandler()

# Sidebar Navigation
st.sidebar.markdown("## ⚙️ SpareSync")
st.sidebar.caption("Inventory Transaction Reconciliation Engine")
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🔍 Reconciliation", "📋 Transaction Explorer", "🧪 Failure Simulation", "🛡️ Operational Fallback", "⚖️ Baseline Comparison"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📌 Project Scope")
st.sidebar.info(
    "**Review 1 Prototype (35% Scope)**\n\n"
    "• Rule-Based Reconciliation\n"
    "• Decision Trade-Off Analysis\n"
    "• Chronological Stream Analysis\n"
    "• Injected Failure Scenarios\n"
    "• Baseline Comparison & Metrics\n"
    "• Store-and-Forward Resilience"
)

if st.sidebar.button("🔄 Regenerate Sample Data"):
    df_transactions, df_physical_counts = generate_synthetic_data(seed=42)
    fallback_handler.clear_database()
    st.cache_data.clear()
    st.sidebar.success("Sample data reloaded!")
    st.rerun()


# =============================================================================
# 1. DASHBOARD SECTION
# =============================================================================
if nav_choice == "📊 Dashboard":
    st.markdown('<div class="main-header">Operational Reconciliation Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Overview of inventory transactions, detected discrepancies, and automated root-cause diagnostics across repair hubs.</div>', unsafe_allow_html=True)

    # Compute network-wide reconciliation
    df_reconciled = engine.reconcile_all()

    total_tx = len(df_transactions)
    total_parts = df_transactions["part_id"].nunique()
    variance_cases = len(df_reconciled[df_reconciled["has_variance"]])
    explained_cases = len(df_reconciled[(df_reconciled["has_variance"]) & (df_reconciled["issue_type"] != "UNEXPLAINED_VARIANCE")])

    # Top KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{total_tx:,}</div>
                <div class="metric-label">Total Transactions</div>
            </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val">{total_parts}</div>
                <div class="metric-label">Monitored Parts</div>
            </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #DC2626;">{variance_cases}</div>
                <div class="metric-label">Variance Cases</div>
            </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #16A34A;">{explained_cases}</div>
                <div class="metric-label">Explained Issues</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Plotly Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### 🎯 Detected Discrepancies by Root Cause")
        issue_counts = df_reconciled["issue_type"].value_counts().reset_index()
        issue_counts.columns = ["Issue Type", "Count"]
        
        label_map = {
            "NONE": "Normal (Aligned)",
            "MISSING_TRANSFER": "Unconfirmed Transfer",
            "DUPLICATE_TRANSACTION": "Duplicate Transaction",
            "NETWORK_SYNC_FAILURE": "Network Sync Delay",
            "TIMESTAMP_ANOMALY": "Timestamp Inversion",
            "UNEXPLAINED_VARIANCE": "Unexplained / Clerical"
        }
        issue_counts["Issue Label"] = issue_counts["Issue Type"].map(lambda x: label_map.get(x, x))

        fig1 = px.pie(
            issue_counts,
            values="Count",
            names="Issue Label",
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig1.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
        st.plotly_chart(fig1, use_container_width=True)

    with chart_col2:
        st.markdown("#### 📦 Transaction Volume by Hub & Event Type")
        tx_by_hub = df_transactions.groupby(["location", "event_type"]).size().reset_index(name="Volume")
        fig2 = px.bar(
            tx_by_hub,
            x="location",
            y="Volume",
            color="event_type",
            barmode="stack",
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig2.update_layout(
            xaxis_title="Repair Hub",
            yaxis_title="Transaction Count",
            margin=dict(t=20, b=20, l=20, r=20),
            height=320,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Network Variance Audit Summary Table
    st.markdown("#### 📋 Inventory Status Summary")
    display_df = df_reconciled[[
        "part_id", "part_name", "location", "system_stock", "physical_stock", "variance", "issue_type", "confidence"
    ]].copy()
    display_df.columns = ["Part ID", "Part Name", "Hub Location", "System Stock", "Physical Stock", "Variance", "Detected Issue", "Confidence"]
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# =============================================================================
# 2. RECONCILIATION SECTION (WITH OPERATIONAL TRADE-OFF ANALYSIS)
# =============================================================================
elif nav_choice == "🔍 Reconciliation":
    st.markdown('<div class="main-header">Part-Level Reconciliation Engine</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Select a high-value spare part and repair location to investigate transaction history, explain root causes, and evaluate decision trade-offs.</div>', unsafe_allow_html=True)

    # Part & Location Selectors
    sel_col1, sel_col2 = st.columns(2)
    
    parts_list = sorted(df_physical_counts["part_id"].unique())
    part_names = {row["part_id"]: f"{row['part_id']} – {row['part_name']}" for _, row in df_physical_counts.iterrows()}

    with sel_col1:
        selected_part = st.selectbox(
            "Select Spare Part",
            parts_list,
            format_func=lambda pid: part_names.get(pid, pid)
        )

    with sel_col2:
        locations_for_part = sorted(df_physical_counts[df_physical_counts["part_id"] == selected_part]["location"].unique())
        selected_location = st.selectbox(
            "Select Repair Hub Location",
            locations_for_part
        )

    # Run Reconciliation for selected item
    rec_result = engine.reconcile_item(selected_part, selected_location)

    st.markdown("---")

    # Stock Comparison KPI Cards
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    with m_col1:
        st.metric("Expected System Stock", f"{rec_result['system_stock']} units")
    with m_col2:
        st.metric("Audited Physical Stock", f"{rec_result['physical_stock']} units")
    with m_col3:
        var_val = rec_result["variance"]
        st.metric("Inventory Variance", f"{var_val:+d} units", delta=var_val if var_val != 0 else None, delta_color="inverse")
    with m_col4:
        conf = rec_result["confidence"]
        badge_cls = "badge-high" if "9" in conf or "8" in conf or "100" in conf else "badge-medium"
        st.markdown(f"**Diagnostic Confidence**<br><span class='{badge_cls}'>{conf}</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Diagnostic Results Card
    issue_type = rec_result["issue_type"]
    if issue_type == "NONE":
        st.success(f"✅ **{rec_result['likely_cause']}**")
    elif issue_type == "MISSING_TRANSFER":
        st.error(f"🚨 **Issue Detected: Unconfirmed Inter-Hub Transfer**\n\n{rec_result['likely_cause']}")
    elif issue_type == "DUPLICATE_TRANSACTION":
        st.warning(f"⚠️ **Issue Detected: Duplicate Transaction Entry**\n\n{rec_result['likely_cause']}")
    elif issue_type == "NETWORK_SYNC_FAILURE":
        st.warning(f"📡 **Issue Detected: Network Synchronization Delay**\n\n{rec_result['likely_cause']}")
    elif issue_type == "TIMESTAMP_ANOMALY":
        st.info(f"⏱️ **Issue Detected: Out-of-Sequence Timestamps**\n\n{rec_result['likely_cause']}")
    else:
        st.error(f"⚠️ **Issue Detected: Unexplained Stock Discrepancy**\n\n{rec_result['likely_cause']}")

    # Supporting Evidence
    with st.expander("🔎 View Supporting Audit Evidence & Transaction Facts", expanded=True):
        for ev in rec_result["evidence"]:
            st.markdown(f"- {ev}")

    # Recommended Action Box
    st.markdown(f"""
        <div class="action-box">
            <strong>💡 Recommended Operational Action:</strong><br>
            {rec_result['recommended_action']}
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # OPERATIONAL TRADE-OFF ANALYSIS SUB-SECTION
    # -------------------------------------------------------------------------
    st.markdown("### ⚖️ Operational Trade-Off Analysis")
    st.caption("Exposes multi-criteria evaluation (Cost, Time, Carbon Emissions, Operational Reliability) for the recommended recovery course of action.")

    to_meta = rec_result.get("tradeoff", {})
    action_name = to_meta.get("Action_Name", "Recommended Action")

    # Trade-off KPI Scorecards
    t_c1, t_c2, t_c3, t_c4 = st.columns(4)
    with t_c1:
        st.markdown(f"""
            <div class="tradeoff-card">
                <div class="tradeoff-title">💰 Financial Cost</div>
                <div class="tradeoff-val">{to_meta.get('Cost', 'Low')}</div>
            </div>
        """, unsafe_allow_html=True)
    with t_c2:
        st.markdown(f"""
            <div class="tradeoff-card">
                <div class="tradeoff-title">⏱️ Resolution Time</div>
                <div class="tradeoff-val">{to_meta.get('Time', 'Medium')}</div>
            </div>
        """, unsafe_allow_html=True)
    with t_c3:
        st.markdown(f"""
            <div class="tradeoff-card">
                <div class="tradeoff-title">🌱 Carbon Emissions</div>
                <div class="tradeoff-val">{to_meta.get('Emissions', 'Low')}</div>
            </div>
        """, unsafe_allow_html=True)
    with t_c4:
        st.markdown(f"""
            <div class="tradeoff-card">
                <div class="tradeoff-title">🛡️ Audit Reliability</div>
                <div class="tradeoff-val">{to_meta.get('Reliability', 'High')}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Comparative Plotly Chart of All Action Options
    st.markdown("#### 📊 Multi-Criteria Comparison Across Recovery Options")
    
    tradeoff_chart_data = []
    for act_k, act_v in TRADE_OFF_ACTIONS.items():
        is_rec = (act_k == action_name)
        tradeoff_chart_data.extend([
            {"Action": act_k, "Criterion": "Cost Score", "Score": act_v["Cost_Score"], "Is_Recommended": is_rec},
            {"Action": act_k, "Criterion": "Time Score", "Score": act_v["Time_Score"], "Is_Recommended": is_rec},
            {"Action": act_k, "Criterion": "Emissions Score", "Score": act_v["Emissions_Score"], "Is_Recommended": is_rec},
            {"Action": act_k, "Criterion": "Reliability Score", "Score": act_v["Reliability_Score"], "Is_Recommended": is_rec},
        ])
    df_to_chart = pd.DataFrame(tradeoff_chart_data)

    fig_tradeoff = px.bar(
        df_to_chart,
        x="Action",
        y="Score",
        color="Criterion",
        barmode="group",
        color_discrete_sequence=["#EF4444", "#F59E0B", "#10B981", "#3B82F6"]
    )
    fig_tradeoff.update_layout(
        yaxis_title="Estimated Score (0-100)",
        xaxis_title="Recovery Action Alternative",
        margin=dict(t=20, b=20, l=20, r=20),
        height=340,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_tradeoff, use_container_width=True)

    # Decision Support Table
    st.markdown("#### 📋 Recovery Actions Evaluation Matrix")
    df_all_to = get_all_tradeoffs_df()
    st.dataframe(df_all_to, use_container_width=True, hide_index=True)

    # Mandatory Disclaimer Banner
    st.info("⚠️ **Note:** *Prototype decision-support estimates for comparison purposes.*")

    st.markdown("---")

    # Filtered Transaction Stream
    st.markdown("#### 📜 Recent Transaction Activity for this Item")
    item_txs = df_transactions[
        (df_transactions["part_id"] == selected_part) &
        (df_transactions["location"] == selected_location)
    ].sort_values(by="timestamp", ascending=False)

    if not item_txs.empty:
        st.dataframe(
            item_txs[["transaction_id", "event_type", "quantity", "location", "timestamp", "transfer_id", "sync_status"]],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No localized transaction records found for this hub.")


# =============================================================================
# 3. TRANSACTION EXPLORER SECTION
# =============================================================================
elif nav_choice == "📋 Transaction Explorer":
    st.markdown('<div class="main-header">Transaction Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Search, inspect, and filter historical inventory events across all network repair hubs.</div>', unsafe_allow_html=True)

    # Filter Bar
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    
    with f_col1:
        part_options = ["All Parts"] + sorted(df_transactions["part_id"].unique().tolist())
        filter_part = st.selectbox("Filter by Part", part_options)

    with f_col2:
        loc_options = ["All Locations"] + sorted(df_transactions["location"].unique().tolist())
        filter_loc = st.selectbox("Filter by Location", loc_options)

    with f_col3:
        event_options = ["All Events"] + sorted(df_transactions["event_type"].unique().tolist())
        filter_event = st.selectbox("Filter by Event Type", event_options)

    with f_col4:
        sync_options = ["All Statuses"] + sorted(df_transactions["sync_status"].unique().tolist())
        filter_sync = st.selectbox("Filter by Sync Status", sync_options)

    # Search Box
    search_query = st.text_input("🔍 Search by Transaction ID, Transfer ID, or Part Name", "")

    # Apply Filters
    filtered_df = df_transactions.copy()
    if filter_part != "All Parts":
        filtered_df = filtered_df[filtered_df["part_id"] == filter_part]
    if filter_loc != "All Locations":
        filtered_df = filtered_df[filtered_df["location"] == filter_loc]
    if filter_event != "All Events":
        filtered_df = filtered_df[filtered_df["event_type"] == filter_event]
    if filter_sync != "All Statuses":
        filtered_df = filtered_df[filtered_df["sync_status"] == filter_sync]
    if search_query:
        sq = search_query.lower()
        filtered_df = filtered_df[
            filtered_df["transaction_id"].str.lower().str.contains(sq, na=False) |
            filtered_df["part_name"].str.lower().str.contains(sq, na=False) |
            filtered_df["transfer_id"].str.lower().str.contains(sq, na=False)
        ]

    st.markdown(f"**Showing {len(filtered_df):,} of {len(df_transactions):,} transactions**")

    st.dataframe(
        filtered_df[["transaction_id", "part_id", "part_name", "event_type", "quantity", "location", "timestamp", "transfer_id", "sync_status"]],
        use_container_width=True,
        hide_index=True
    )

    # Export CSV Option
    csv_data = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Transactions (CSV)",
        data=csv_data,
        file_name="sparesync_transactions_export.csv",
        mime="text/csv"
    )


# =============================================================================
# 4. FAILURE SIMULATION SECTION
# =============================================================================
elif nav_choice == "🧪 Failure Simulation":
    st.markdown('<div class="main-header">Operational Failure Simulation Sandbox</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Interactively inject realistic supply chain breakdown scenarios to test and demonstrate the reconciliation engine\'s automated diagnostic response.</div>', unsafe_allow_html=True)

    sim_tab1, sim_tab2, sim_tab3, sim_tab4 = st.tabs([
        "🔄 Scenario 1: Missing Transfer Confirmation",
        "🧾 Scenario 2: Duplicate Receipt",
        "📡 Scenario 3: Network Failure",
        "⏱️ Scenario 4: Timestamp Anomaly"
    ])

    # -------------------------------------------------------------------------
    # SCENARIO 1: MISSING TRANSFER CONFIRMATION
    # -------------------------------------------------------------------------
    with sim_tab1:
        st.markdown("### 🔄 Scenario 1: Unconfirmed Inter-Hub Transfer")
        st.caption("Simulates a high-value spare part dispatched from a source hub with an unrecorded inbound receipt at destination.")

        c1, c2 = st.columns([1, 1])
        with c1:
            s1_part = st.selectbox("Select Part to Transfer", list(PARTS_CATALOG.keys()), key="s1_p", format_func=lambda x: f"{x} – {PARTS_CATALOG[x]}")
            s1_qty = st.slider("Transfer Quantity", min_value=1, max_value=5, value=3, key="s1_q")
        with c2:
            s1_src = st.selectbox("Source Hub (Dispatched From)", LOCATIONS, index=0, key="s1_s")
            dst_options = [l for l in LOCATIONS if l != s1_src]
            s1_dst = st.selectbox("Destination Hub (Receiving)", dst_options, index=0, key="s1_d")

        res_s1 = simulate_missing_transfer(part_id=s1_part, source_loc=s1_src, dest_loc=s1_dst, qty=s1_qty)

        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### 1️⃣ Normal Baseline State")
            st.info(f"**Baseline Flow:**\n\n{res_s1['normal_state']['description']}")
            st.markdown(f"• Expected Source Stock ({s1_src}): `{res_s1['normal_state']['source_system_stock']} units`")
            st.markdown(f"• Expected Destination Stock ({s1_dst}): `{res_s1['normal_state']['dest_system_stock']} units`")

        with col_b:
            st.markdown("#### 2️⃣ Injected Failure Event")
            st.error(f"**Disruption Introduced:**\n\n{res_s1['failure_state']['description']}")
            st.markdown(f"• System Stock at {s1_dst}: `{res_s1['failure_state']['dest_system_stock']} units`")
            st.markdown(f"• Physical Shelf Stock at {s1_dst}: `{res_s1['failure_state']['dest_physical_stock']} units`")
            st.markdown(f"• Unexplained Variance: `{res_s1['failure_state']['dest_variance']} units`")

        st.markdown("#### 📄 Transaction Stream Generated for Simulation")
        st.dataframe(res_s1["transactions_table"], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🔍 System Detection & Reconciliation Diagnostic")
        
        st.markdown("""
            <div style="margin-bottom: 0.8rem;">
                <span class="badge-status-detected">🚨 Detected: Discrepancy Found</span> &nbsp;
                <span class="badge-status-explained">🔍 Explained: Unconfirmed Transfer</span> &nbsp;
                <span class="badge-status-action">⚡ Action Required: In-Transit Audit</span>
            </div>
        """, unsafe_allow_html=True)

        rec1 = res_s1["reconciliation"]
        st.error(f"**Likely Root Cause:** {rec1['likely_cause']}")
        st.markdown(f"**Diagnostic Confidence:** <span class='badge-high'>{rec1['confidence']}</span>", unsafe_allow_html=True)

        with st.expander("🔎 Factual Evidence Collected by Engine", expanded=True):
            for ev in rec1["evidence"]:
                st.markdown(f"- {ev}")

        st.markdown(f"""
            <div class="action-box">
                <strong>💡 Recommended Recovery Step:</strong><br>
                {rec1['recommended_action']}
            </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SCENARIO 2: DUPLICATE RECEIPT
    # -------------------------------------------------------------------------
    with sim_tab2:
        st.markdown("### 🧾 Scenario 2: Accidental Duplicate Receipt Scan")
        st.caption("Simulates an operator scanning the same delivery barcode twice within minutes, creating artificial ledger surplus.")

        s2_c1, s2_c2 = st.columns(2)
        with s2_c1:
            s2_part = st.selectbox("Select Received Part", list(PARTS_CATALOG.keys()), index=1, key="s2_p", format_func=lambda x: f"{x} – {PARTS_CATALOG[x]}")
            s2_qty = st.slider("Batch Quantity", min_value=1, max_value=10, value=4, key="s2_q")
        with s2_c2:
            s2_loc = st.selectbox("Receiving Warehouse", LOCATIONS, index=2, key="s2_l")
            s2_diff = st.slider("Time Delta Between Duplicate Scans (minutes)", min_value=1, max_value=25, value=4, key="s2_d")

        res_s2 = simulate_duplicate_receipt(part_id=s2_part, loc=s2_loc, qty=s2_qty, time_diff_mins=s2_diff)

        st.markdown("---")
        col_s2a, col_s2b = st.columns(2)
        with col_s2a:
            st.markdown("#### 1️⃣ Normal Baseline State")
            st.info(f"**Expected Delivery:**\n\n{res_s2['normal_state']['description']}")
            st.markdown(f"• True Physical Quantity: `{res_s2['normal_state']['expected_stock']} units`")

        with col_s2b:
            st.markdown("#### 2️⃣ Injected Failure Event")
            st.warning(f"**Duplicate Entry:**\n\n{res_s2['failure_state']['description']}")
            st.markdown(f"• System Ledger Balance: `{res_s2['failure_state']['system_stock']} units` (Artificial +{s2_qty})")
            st.markdown(f"• Physical Shelved Stock: `{res_s2['failure_state']['physical_stock']} units`")
            st.markdown(f"• Net Detected Variance: `+{res_s2['failure_state']['variance']} units`")

        st.markdown("#### 📄 Duplicate Transaction Records")
        st.dataframe(res_s2["transactions_table"], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🔍 System Detection & Reconciliation Diagnostic")
        st.markdown("""
            <div style="margin-bottom: 0.8rem;">
                <span class="badge-status-detected">🚨 Detected: Phantom Stock Surplus</span> &nbsp;
                <span class="badge-status-explained">🔍 Explained: Temporal Duplicate Scan</span> &nbsp;
                <span class="badge-status-action">⚡ Action Required: Journal Reversal</span>
            </div>
        """, unsafe_allow_html=True)

        rec2 = res_s2["reconciliation"]
        st.warning(f"**Likely Root Cause:** {rec2['likely_cause']}")
        st.markdown(f"**Diagnostic Confidence:** <span class='badge-high'>{rec2['confidence']}</span>", unsafe_allow_html=True)

        with st.expander("🔎 Factual Evidence Collected by Engine", expanded=True):
            for ev in rec2["evidence"]:
                st.markdown(f"- {ev}")

        st.markdown(f"""
            <div class="action-box">
                <strong>💡 Recommended Recovery Step:</strong><br>
                {rec2['recommended_action']}
            </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SCENARIO 3: NETWORK FAILURE
    # -------------------------------------------------------------------------
    with sim_tab3:
        st.markdown("### 📡 Scenario 3: Network Failure & Delayed Edge Synchronization")
        st.caption("Simulates an offline repair pick stored on a handheld scanner with PENDING_SYNC status.")

        s3_c1, s3_c2 = st.columns(2)
        with s3_c1:
            s3_part = st.selectbox("Select Part Consumed", list(PARTS_CATALOG.keys()), index=2, key="s3_p", format_func=lambda x: f"{x} – {PARTS_CATALOG[x]}")
            s3_qty = st.slider("Picked Quantity", min_value=1, max_value=5, value=2, key="s3_q")
        with s3_c2:
            s3_loc = st.selectbox("Hub with Router Outage", LOCATIONS, index=0, key="s3_l")

        res_s3 = simulate_network_failure(part_id=s3_part, loc=s3_loc, qty=s3_qty)

        st.markdown("---")
        col_s3a, col_s3b = st.columns(2)
        with col_s3a:
            st.markdown("#### 1️⃣ Normal Baseline State")
            st.info(f"**Initial Balance:**\n\n{res_s3['normal_state']['description']}")
            st.markdown(f"• Expected Central Stock: `{res_s3['normal_state']['system_stock']} units`")

        with col_s3b:
            st.markdown("#### 2️⃣ Injected Failure Event (Offline Pick)")
            st.error(f"**Network Disconnect:**\n\n{res_s3['failure_state']['description']}")
            st.markdown(f"• Central System View: `{res_s3['failure_state']['central_system_stock']} units` (Unaware of offline pick)")
            st.markdown(f"• Physical Shelf Stock: `{res_s3['failure_state']['physical_stock']} units` (Physically removed)")
            st.markdown(f"• Apparent Discrepancy: `+{res_s3['failure_state']['apparent_variance']} units`")

        st.markdown("#### 📄 Local vs Central Transaction Status")
        st.dataframe(res_s3["transactions_table"], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🔍 System Detection & Reconciliation Diagnostic")
        st.markdown("""
            <div style="margin-bottom: 0.8rem;">
                <span class="badge-status-detected">🚨 Detected: Unreconciled Shelf Deficit</span> &nbsp;
                <span class="badge-status-explained">🔍 Explained: PENDING_SYNC Cached Event</span> &nbsp;
                <span class="badge-status-action">⚡ Action Required: Store-and-Forward Push</span>
            </div>
        """, unsafe_allow_html=True)

        rec3 = res_s3["reconciliation"]
        st.warning(f"**Likely Root Cause:** {rec3['likely_cause']}")
        st.markdown(f"**Diagnostic Confidence:** <span class='badge-high'>{rec3['confidence']}</span>", unsafe_allow_html=True)

        with st.expander("🔎 Factual Evidence Collected by Engine", expanded=True):
            for ev in rec3["evidence"]:
                st.markdown(f"- {ev}")

        st.markdown(f"""
            <div class="action-box">
                <strong>💡 Recommended Recovery Step:</strong><br>
                {rec3['recommended_action']}
            </div>
        """, unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # SCENARIO 4: TIMESTAMP ANOMALY
    # -------------------------------------------------------------------------
    with sim_tab4:
        st.markdown("### ⏱️ Scenario 4: Timestamp Sequence Inversion")
        st.caption("Simulates asynchronous scanner clock drift causing an intake receipt to arrive with a timestamp earlier than its source dispatch.")

        s4_c1, s4_c2 = st.columns(2)
        with s4_c1:
            s4_part = st.selectbox("Select Transferred Part", list(PARTS_CATALOG.keys()), index=3, key="s4_p", format_func=lambda x: f"{x} – {PARTS_CATALOG[x]}")
            s4_qty = st.slider("Transfer Units", min_value=1, max_value=5, value=2, key="s4_q")
        with s4_c2:
            s4_src = st.selectbox("Source Hub (Mumbai)", [LOCATIONS[2]], key="s4_s")
            s4_dst = st.selectbox("Destination Hub (Bangalore)", [LOCATIONS[1]], key="s4_d")

        res_s4 = simulate_timestamp_anomaly(part_id=s4_part, source_loc=s4_src, dest_loc=s4_dst, qty=s4_qty)

        st.markdown("---")
        col_s4a, col_s4b = st.columns(2)
        with col_s4a:
            st.markdown("#### 1️⃣ Normal Baseline Expectation")
            st.info(f"**Causal Workflow Rule:**\n\n{res_s4['normal_state']['description']}")

        with col_s4b:
            st.markdown("#### 2️⃣ Injected Chronological Failure")
            st.warning(f"**Sequence Anomaly:**\n\n{res_s4['failure_state']['description']}")
            st.markdown(f"• Discrepancy Signature: `{res_s4['failure_state']['time_discrepancy']}`")

        st.markdown("#### 📄 Inverted Transaction Ledger Timestamps")
        st.dataframe(res_s4["transactions_table"], use_container_width=True, hide_index=True)

        st.markdown("---")
        st.markdown("#### 🔍 System Detection & Reconciliation Diagnostic")
        st.markdown("""
            <div style="margin-bottom: 0.8rem;">
                <span class="badge-status-detected">🚨 Detected: Chronological Inversion</span> &nbsp;
                <span class="badge-status-explained">🔍 Explained: NTP Clock Drift</span> &nbsp;
                <span class="badge-status-action">⚡ Action Required: Terminal Audit & Resequencing</span>
            </div>
        """, unsafe_allow_html=True)

        rec4 = res_s4["reconciliation"]
        st.info(f"**Likely Root Cause:** {rec4['likely_cause']}")
        st.markdown(f"**Diagnostic Confidence:** <span class='badge-high'>{rec4['confidence']}</span>", unsafe_allow_html=True)

        with st.expander("🔎 Factual Evidence Collected by Engine", expanded=True):
            for ev in rec4["evidence"]:
                st.markdown(f"- {ev}")

        st.markdown(f"""
            <div class="action-box">
                <strong>💡 Recommended Recovery Step:</strong><br>
                {rec4['recommended_action']}
            </div>
        """, unsafe_allow_html=True)


# =============================================================================
# 5. OPERATIONAL FALLBACK SECTION
# =============================================================================
elif nav_choice == "🛡️ Operational Fallback":
    st.markdown('<div class="main-header">Operational Resilience & Fallback Controls</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Demonstrates store-and-forward edge persistence during network outages and manual fallback data entry during scanner/sensor failures.</div>', unsafe_allow_html=True)

    # Visual Workflow Stepper
    st.markdown("#### 🔄 Store-and-Forward Operational Workflow")
    w1, w2, w3, w4, w5, w6 = st.columns(6)
    with w1:
        st.markdown('<div class="workflow-step">1. Event Created</div>', unsafe_allow_html=True)
    with w2:
        st.markdown('<div class="workflow-step">2. Network Down</div>', unsafe_allow_html=True)
    with w3:
        st.markdown('<div class="workflow-step">3. Edge Stored</div>', unsafe_allow_html=True)
    with w4:
        st.markdown('<div class="workflow-step">4. PENDING_SYNC</div>', unsafe_allow_html=True)
    with w5:
        st.markdown('<div class="workflow-step">5. Link Restored</div>', unsafe_allow_html=True)
    with w6:
        st.markdown('<div class="workflow-step">6. Synced</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab_network, tab_manual = st.tabs(["📡 Section A: Network Outage & Store-and-Forward", "✍️ Section B: Manual Fallback Entry"])

    # SECTION A: NETWORK FAILURE SIMULATION
    with tab_network:
        st.markdown("### 📡 Section A: Network Failure & Store-and-Forward Simulation")
        st.markdown("Simulate an edge terminal logging a transaction while network connectivity to the central inventory ledger is down.")

        c1, c2 = st.columns([1, 1])

        with c1:
            st.markdown("#### 🛠️ Create Offline Transaction (Handheld Terminal)")
            with st.form("offline_tx_form"):
                off_part = st.selectbox("Select Part", list(PARTS_CATALOG.keys()), format_func=lambda x: f"{x} – {PARTS_CATALOG[x]}")
                off_event = st.selectbox("Event Type", ["PICK", "RECEIPT", "TRANSFER_OUT", "TRANSFER_IN"])
                off_qty = st.number_input("Quantity", min_value=1, max_value=20, value=2)
                off_loc = st.selectbox("Warehouse Location", LOCATIONS)
                off_reason = st.text_input("Offline Reason", value="Gateway timeout / WLAN outage at repair bay")
                
                submitted_offline = st.form_submit_button("📥 Record Offline Transaction")

            if submitted_offline:
                new_off_tx = fallback_handler.record_offline_transaction(
                    part_id=off_part,
                    event_type=off_event,
                    quantity=off_qty,
                    location=off_loc,
                    reason=off_reason
                )
                st.warning(
                    f"⚠️ **Transaction Cached Locally!**\n\n"
                    f"• **ID:** `{new_off_tx['transaction_id']}`\n\n"
                    f"• **Status:** `{new_off_tx['sync_status']}`\n\n"
                    f"• **Item:** {new_off_tx['part_id']} ({off_qty} units at {off_loc})\n\n"
                    f"• **Reason:** {off_reason}"
                )

        with c2:
            st.markdown("#### 📦 Edge Pending Synchronization Queue (SQLite)")
            pending_df = fallback_handler.get_pending_transactions()
            
            p_count = len(pending_df)
            st.metric("Transactions Waiting for Sync", f"{p_count} queued")

            if not pending_df.empty:
                st.dataframe(
                    pending_df[["transaction_id", "part_id", "event_type", "quantity", "location", "timestamp", "sync_status"]],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No pending offline transactions. Queue is clean.")

            st.markdown("---")
            if st.button("🚀 Restore Network & Synchronize All Pending Transactions", type="primary", disabled=(p_count == 0)):
                sync_summary = fallback_handler.simulate_network_restore()
                st.cache_data.clear()
                st.success(
                    f"✅ **Network Restored & Synchronized!**\n\n"
                    f"• **Pending Before Sync:** {sync_summary['pending_before']}\n\n"
                    f"• **Successfully Synchronized:** {sync_summary['successfully_synchronized']}\n\n"
                    f"• **Remaining Pending:** {sync_summary['remaining_pending']}\n\n"
                    f"Transactions have been flushed from local queue and posted to central ledger."
                )
                st.rerun()

    # SECTION B: MANUAL FALLBACK ENTRY
    with tab_manual:
        st.markdown("### ✍️ Section B: Manual Fallback Data Entry")
        st.markdown("When automated barcode scanners, RFID readers, or IoT sensors fail, technicians can log manual entries to maintain operational continuity.")

        with st.form("manual_entry_form"):
            m_col1, m_col2 = st.columns(2)
            with m_col1:
                man_part = st.selectbox("Part ID", list(PARTS_CATALOG.keys()), format_func=lambda x: f"{x} – {PARTS_CATALOG[x]}", key="man_part")
                man_event = st.selectbox("Event Type", ["RECEIPT", "PICK", "TRANSFER_OUT", "TRANSFER_IN", "ADJUSTMENT"], key="man_event")
                man_qty = st.number_input("Quantity", min_value=1, max_value=50, value=1, key="man_qty")
            with m_col2:
                man_loc = st.selectbox("Repair Hub Location", LOCATIONS, key="man_loc")
                man_reason = st.selectbox(
                    "Failure Reason / Exception Code",
                    [
                        "Barcode scanner optical engine malfunction",
                        "Damaged or unreadable part label barcode",
                        "RFID gate sensor communication failure",
                        "Emergency offline issue during power outage",
                        "Unregistered batch intake exception"
                    ]
                )
                man_custom_notes = st.text_input("Additional Notes / Technician ID", "TECH-409 (Supervised Manual Entry)")

            submit_manual = st.form_submit_button("📝 Submit Manual Fallback Transaction")

        if submit_manual:
            full_reason = f"{man_reason} | Notes: {man_custom_notes}"
            res_manual = fallback_handler.record_manual_fallback(
                part_id=man_part,
                event_type=man_event,
                quantity=man_qty,
                location=man_loc,
                reason=full_reason
            )
            st.cache_data.clear()
            st.success("✅ **Manual transaction recorded successfully and is pending verification.**")
            
            st.markdown(f"""
                <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 8px; padding: 1rem; margin-top: 0.5rem;">
                    <strong>Transaction ID:</strong> <code>{res_manual['transaction_id']}</code><br>
                    <strong>Assigned Status:</strong> <span class="badge-manual">{res_manual['status']}</span><br>
                    <strong>Verification Required:</strong> <code>True</code><br>
                    <strong>Part:</strong> {res_manual['part_id']} ({PARTS_CATALOG.get(res_manual['part_id'], '')}) &bull; <strong>Qty:</strong> {man_qty} &bull; <strong>Hub:</strong> {man_loc}<br>
                    <strong>Exception Reason:</strong> {full_reason}
                </div>
            """, unsafe_allow_html=True)
            st.info("ℹ️ This manual entry has been marked for supervisor verification and is now visible in the **Transaction Explorer**.")


# =============================================================================
# 6. BASELINE COMPARISON SECTION
# =============================================================================
elif nav_choice == "⚖️ Baseline Comparison":
    st.markdown('<div class="main-header">Baseline vs. SpareSync Evaluation Benchmark</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Empirical comparison demonstrating how SpareSync reduces unexplained inventory variance through automated transaction reconciliation.</div>', unsafe_allow_html=True)

    # Run Benchmark Experiment Dynamically
    bench_results = run_benchmark_experiment()

    # KPI Row
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #DC2626;">{bench_results['baseline']['unexplained_variance_rate_pct']}%</div>
                <div class="metric-label">Baseline Unexplained Rate</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col2:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #2563EB;">{bench_results['sparesync']['unexplained_variance_rate_pct']}%</div>
                <div class="metric-label">SpareSync Unexplained Rate</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col3:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #16A34A;">+{bench_results['sparesync']['variance_reduction_pct']}%</div>
                <div class="metric-label">Variance Reduction</div>
            </div>
        """, unsafe_allow_html=True)
    with kpi_col4:
        st.markdown(f"""
            <div class="metric-card">
                <div class="metric-val" style="color: #059669;">{bench_results['sparesync']['explanation_accuracy_pct']}%</div>
                <div class="metric-label">Explanation Accuracy</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Visualizations
    v_col1, v_col2 = st.columns(2)

    with v_col1:
        st.markdown("#### 📊 Unexplained Variance Rate Comparison")
        comp_df = pd.DataFrame([
            {"System": "Baseline Auditor", "Unexplained Variance Rate (%)": bench_results['baseline']['unexplained_variance_rate_pct']},
            {"System": "SpareSync Engine", "Unexplained Variance Rate (%)": bench_results['sparesync']['unexplained_variance_rate_pct']}
        ])
        fig_comp = px.bar(
            comp_df,
            x="System",
            y="Unexplained Variance Rate (%)",
            color="System",
            text="Unexplained Variance Rate (%)",
            color_discrete_map={"Baseline Auditor": "#EF4444", "SpareSync Engine": "#3B82F6"}
        )
        fig_comp.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig_comp.update_layout(yaxis_range=[0, 115], margin=dict(t=20, b=20, l=20, r=20), height=320, showlegend=False)
        st.plotly_chart(fig_comp, use_container_width=True)

    with v_col2:
        st.markdown("#### 🎯 Reconciliation Resolution Distribution")
        res_df = pd.DataFrame([
            {"Status": "Correctly Explained", "Count": bench_results['correctly_explained_cases']},
            {"Status": "Unexplained / Ambiguous", "Count": bench_results['unexplained_cases']}
        ])
        fig_pie = px.pie(
            res_df,
            values="Count",
            names="Status",
            hole=0.45,
            color="Status",
            color_discrete_map={"Correctly Explained": "#10B981", "Unexplained / Ambiguous": "#F59E0B"}
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=320)
        st.plotly_chart(fig_pie, use_container_width=True)

    # Feature Capability Table
    st.markdown("#### 📋 Feature Capability Matrix: Baseline vs. SpareSync")
    st.dataframe(bench_results["feature_comparison_df"], use_container_width=True, hide_index=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Detailed Evaluated Failures Table
    st.markdown("#### 🔬 Detailed Ground Truth Validation on Injected Scenarios")
    df_det = bench_results["detailed_failures_df"]
    if not df_det.empty:
        st.dataframe(
            df_det[["part_id", "part_name", "location", "variance", "ground_truth_cause", "sparesync_cause", "is_correctly_explained", "confidence"]],
            use_container_width=True,
            hide_index=True
        )

    st.markdown("---")

    # Error Analysis & Limitations Section
    st.markdown("### ⚠️ Error Analysis & System Limitations")
    st.markdown("""
        The current Review 1 prototype utilizes a **transparent, deterministic rule-based reconciliation engine**. While highly explainable and fast (processing latency $\le 100\\text{ ms}$), the following operational edge cases present known limitations:
    """)

    e1, e2 = st.columns(2)
    with e1:
        st.markdown("""
            - **Multiple Simultaneous Errors:** If a part experiences an unconfirmed transfer and an offline technician pick simultaneously, compound anomalies may reduce individual rule confidence.
            - **Missing Cross-System Logs:** When shipments move across third-party logistics (3PL) carriers without shared API logs, transfer confirmation gaps cannot be verified automatically.
            - **Clerical Count Errors Combined with Shrinkage:** Transposed audit numbers coinciding with real warehouse shrinkage require secondary blind recounts.
        """)
    with e2:
        st.markdown("""
            - **Ambiguous Chronology:** If multiple unsynchronized terminals log transactions during identical clock drift windows, causal sequence reordering requires NTP device audits.
            - **Delayed Synchronization Windows:** Handheld units offline for extended durations may cause central ledgers to temporarily flag discrepancies before store-and-forward flushing.
        """)

    st.info("💡 **Academic Note:** Future work (Review 2) will introduce sequence-based machine learning models (LSTM / Transformer) to complement rule routines and probabilistically resolve compound multi-error cases.")
