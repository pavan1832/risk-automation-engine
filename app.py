"""Risk Automation Engine - Streamlit Dashboard"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os

from risk_engine import RiskScoringEngine
from database import RiskDatabase
from llm_explainer import GeminiRiskExplainer
from utils import (generate_sample_data, load_risk_data, format_currency, 
                   format_timestamp, get_risk_color, calculate_percentiles)

# Page config
st.set_page_config(
    page_title="Risk Automation Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'risk_engine' not in st.session_state:
    st.session_state.risk_engine = RiskScoringEngine()
if 'db' not in st.session_state:
    st.session_state.db = RiskDatabase("risk_cases.db")
if 'explainer' not in st.session_state:
    st.session_state.explainer = GeminiRiskExplainer()
if 'selected_cases' not in st.session_state:
    st.session_state.selected_cases = []

# Sidebar
st.sidebar.title("🛡️ Risk Automation Engine")
st.sidebar.title("Developed By Lokpavan")
st.sidebar.markdown("---")

page = st.sidebar.radio("Navigation", [
    "📊 Risk Dashboard",
    "⚙️ Bulk Actions",
    "🔍 Case Details",
    "📋 Audit Logs",
    "⚙️ Settings"
])

st.sidebar.markdown("---")
st.sidebar.markdown("### Stats")
stats = st.session_state.db.get_statistics()
col1, col2 = st.sidebar.columns(2)
col1.metric("Total Cases", stats.get('total_cases', 0))
col2.metric("Audit Logs", stats.get('audit_log_entries', 0))

# Main content
if page == "📊 Risk Dashboard":
    st.title("📊 Risk Case Dashboard")
    st.markdown("Real-time risk case tracking and management")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        risk_filter = st.selectbox("Risk Level", 
                                   ["All", "LOW", "MEDIUM", "HIGH"],
                                   help="Filter by risk level")
    with col2:
        status_filter = st.selectbox("Status",
                                     ["All", "NEW", "APPROVED", "ESCALATED", "BLOCKED"],
                                     help="Filter by action status")
    with col3:
        refresh = st.button("🔄 Refresh", use_container_width=True)
    
    # Get data
    risk_level_param = None if risk_filter == "All" else risk_filter
    status_param = None if status_filter == "All" else status_filter
    cases_df = st.session_state.db.get_risk_cases(
        risk_level=risk_level_param,
        status=status_param,
        limit=500
    )
    
    if not cases_df.empty:
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Cases", len(cases_df))
        with col2:
            high_count = len(cases_df[cases_df['risk_level'] == 'HIGH'])
            st.metric("HIGH Risk", high_count, 
                     delta=f"{high_count/len(cases_df)*100:.1f}%" if len(cases_df) > 0 else "")
        with col3:
            medium_count = len(cases_df[cases_df['risk_level'] == 'MEDIUM'])
            st.metric("MEDIUM Risk", medium_count)
        with col4:
            avg_score = cases_df['final_score'].mean()
            st.metric("Avg Risk Score", f"{avg_score:.1f}")
        
        st.markdown("---")
        
        # Charts
        col1, col2 = st.columns(2)
        
        with col1:
            risk_dist = cases_df['risk_level'].value_counts()
            fig = go.Figure(data=[
                go.Bar(x=risk_dist.index, y=risk_dist.values,
                       marker_color=['#e74c3c', '#f39c12', '#2ecc71'])
            ])
            fig.update_layout(title="Risk Level Distribution", 
                            xaxis_title="Risk Level", yaxis_title="Count",
                            height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[
                go.Histogram(x=cases_df['final_score'], nbinsx=20,
                           marker_color='#3498db')
            ])
            fig.update_layout(title="Risk Score Distribution",
                            xaxis_title="Risk Score", yaxis_title="Count",
                            height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        # Risk cases table
        st.subheader("📋 Risk Cases")
        
        display_cols = ['case_id', 'merchant_id', 'amount', 'final_score', 
                       'risk_level', 'status', 'created_at']
        
        display_df = cases_df[display_cols].copy()
        display_df['amount'] = display_df['amount'].apply(format_currency)
        display_df['final_score'] = display_df['final_score'].apply(lambda x: f"{x:.1f}")
        display_df['created_at'] = display_df['created_at'].apply(format_timestamp)
        
        # Highlight risk levels
        def highlight_risk(row):
            base_style = "background-color: #0f172a; color: #f8fafc;"
            if row['risk_level'] == 'HIGH':
                return [base_style + "border-left: 5px solid #ef4444;"] * len(row)
            elif row['risk_level'] == 'MEDIUM':
                 return [base_style + "border-left: 5px solid #f59e0b;"] * len(row)
            else:
                return [base_style + "border-left: 5px solid #22c55e;"] * len(row)
        
        styled_df = display_df.style.apply(highlight_risk, axis=1)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Bulk action selection
        st.subheader("🎯 Bulk Actions")
        selected_ids = st.multiselect(
            "Select cases for bulk action",
            options=cases_df['case_id'].tolist(),
            key="bulk_select"
        )
        
        if selected_ids:
            col1, col2, col3 = st.columns(3)
            with col1:
                action = st.selectbox("Action", 
                                     ["APPROVE", "ESCALATE", "BLOCKED"],
                                     key="bulk_action")
            with col2:
                notes = st.text_input("Notes", key="bulk_notes")
            with col3:
                st.write("")
                st.write("")
                if st.button("Apply Action", use_container_width=True):
                    count = st.session_state.db.bulk_action(
                        selected_ids, action, notes)
                    st.success(f"✅ Applied to {count} cases")
                    st.rerun()
    
    else:
        st.info("No risk cases found matching filters")


elif page == "⚙️ Bulk Actions":
    st.title("⚙️ Bulk Risk Actions")
    st.markdown("Apply actions to multiple risk cases efficiently")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Bulk Upload")
        uploaded_file = st.file_uploader("Upload CSV with case IDs", 
                                        type=['csv'],
                                        help="CSV must have 'case_id' column")
        
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            st.write(f"Loaded {len(df)} cases")
            st.dataframe(df.head(10), use_container_width=True)
            
            case_ids = df['case_id'].tolist()
            
            action = st.selectbox("Bulk Action",
                                 ["APPROVE", "ESCALATE", "BLOCKED"],
                                 key="bulk_upload_action")
            notes = st.text_area("Action Notes", key="bulk_upload_notes")
            
            if st.button("Execute Bulk Action", use_container_width=True):
                count = st.session_state.db.bulk_action(case_ids, action, notes)
                st.success(f"✅ Applied {action} to {count} cases")
    
    with col2:
        st.subheader("🎯 Manual Selection")
        cases_df = st.session_state.db.get_risk_cases(limit=1000)
        
        if not cases_df.empty:
            # Filter options
            risk_filter = st.multiselect("Filter by Risk Level",
                                        ["LOW", "MEDIUM", "HIGH"],
                                        default=["HIGH"],
                                        key="manual_risk_filter")
            
            filtered = cases_df[cases_df['risk_level'].isin(risk_filter)]
            
            st.write(f"Found {len(filtered)} matching cases")
            
            selected = st.multiselect(
                "Select cases",
                options=filtered['case_id'].tolist(),
                key="manual_select"
            )
            
            if selected:
                action = st.selectbox("Action",
                                     ["APPROVE", "ESCALATE", "BLOCKED"],
                                     key="manual_action")
                notes = st.text_area("Notes", key="manual_notes")
                
                if st.button("Apply Action", use_container_width=True):
                    count = st.session_state.db.bulk_action(
                        selected, action, notes)
                    st.success(f"✅ Applied to {count} cases")


elif page == "🔍 Case Details":
    st.title("🔍 Case Details & History")
    
    # Get all case IDs
    all_cases = st.session_state.db.get_risk_cases(limit=5000)
    
    if not all_cases.empty:
        case_id = st.selectbox("Select Case ID", 
                              options=all_cases['case_id'].tolist())
        
        details = st.session_state.db.get_case_details(case_id)
        
        if details:
            # Basic info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Risk Score", f"{details['final_score']:.1f}")
            with col2:
                st.metric("Risk Level", details['risk_level'])
            with col3:
                st.metric("Status", details['status'])
            with col4:
                st.metric("Merchant", details.get('merchant_id', 'N/A'))
            
            st.markdown("---")
            
            # Case data
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Case Data")
                st.write(f"**Amount:** {format_currency(details.get('amount', 0))}")
                st.write(f"**Transactions:** {details.get('transaction_count', 0)}")
                st.write(f"**Velocity Score:** {details.get('velocity_score', 0):.1f}")
                st.write(f"**Location Mismatch:** {'Yes' if details.get('location_mismatch') else 'No'}")
                st.write(f"**Failed Attempts:** {details.get('failed_attempts', 0)}")
            
            with col2:
                st.subheader("Scoring")
                st.write(f"**Rule Score:** {details.get('rule_score', 0):.1f}")
                if details.get('ml_score'):
                    st.write(f"**ML Score:** {details['ml_score']:.1f}")
                st.write(f"**Final Score:** {details['final_score']:.1f}/100")
            
            st.markdown("---")
            
            # Triggered rules
            st.subheader("🚨 Triggered Risk Factors")
            rules = details.get('triggered_rules', [])
            if rules:
                for rule in rules:
                    st.write(f"• {rule}")
            else:
                st.write("No specific risk factors triggered")
            
            st.markdown("---")
            
            # LLM explanation
            st.subheader("🤖 AI Risk Explanation")
            explanation = details.get('explanation', '')
            if explanation:
                st.info(explanation)
            else:
                if st.button("Generate Explanation", key="gen_explain"):
                    with st.spinner("Generating explanation..."):
                        explainer = st.session_state.explainer
                        explanation = explainer.generate_explanation(
                            {k: details.get(k) for k in ['amount', 'transaction_count',
                                                         'location_mismatch', 'velocity_score',
                                                         'failed_attempts', 'merchant_id']},
                            {'final_score': details['final_score'],
                             'risk_level': details['risk_level'],
                             'triggered_rules': rules}
                        )
                        st.info(explanation)
            
            st.markdown("---")
            
            # Action history
            st.subheader("📜 Action History")
            actions = details.get('actions', [])
            if actions:
                actions_df = pd.DataFrame(actions)
                actions_df['timestamp'] = actions_df['timestamp'].apply(format_timestamp)
                st.dataframe(actions_df[['action_type', 'risk_score_at_action', 
                                        'performed_by', 'timestamp']], 
                           use_container_width=True)
            else:
                st.write("No actions yet")
            
            # Manual action
            st.markdown("---")
            st.subheader("✏️ Manual Action")
            col1, col2, col3 = st.columns(3)
            with col1:
                manual_action = st.selectbox("Action", 
                                            ["APPROVE", "ESCALATE", "BLOCKED",
                                             "REVIEW", "RELEASE"],
                                            key="manual_case_action")
            with col2:
                st.write("")
                st.write("")
                st.write("")
            with col3:
                st.write("")
                st.write("")
                if st.button("Execute", use_container_width=True):
                    st.session_state.db.log_action(case_id, manual_action)
                    st.success(f"✅ {manual_action} applied")
                    st.rerun()


elif page == "📋 Audit Logs":
    st.title("📋 Compliance Audit Logs")
    st.markdown("Complete audit trail for all risk operations")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        event_filter = st.selectbox(
            "Event Type",
            ["All", "CASE_CREATED", "ACTION_APPROVE", "ACTION_ESCALATE", 
             "ACTION_BLOCKED", "BULK_ACTION"],
            key="audit_event_filter")
    with col2:
        case_filter = st.text_input("Case ID (optional)", key="audit_case_filter")
    with col3:
        limit = st.slider("Show last N entries", 100, 5000, 1000)
    
    # Get logs
    event_param = None if event_filter == "All" else event_filter
    case_param = case_filter if case_filter else None
    
    logs_df = st.session_state.db.get_audit_logs(
        case_id=case_param,
        event_type=event_param,
        limit=limit
    )
    
    if not logs_df.empty:
        st.metric("Total Audit Entries", len(logs_df))
        
        # Format for display
        display_df = logs_df.copy()
        display_df['timestamp'] = display_df['timestamp'].apply(format_timestamp)
        display_df['risk_score'] = display_df['risk_score'].apply(
            lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
        
        st.dataframe(display_df[['timestamp', 'event_type', 'case_id', 'action_taken',
                                'risk_score', 'classification_method', 'user_id']],
                    use_container_width=True, height=500)
        
        # Export option
        csv = logs_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Audit Logs (CSV)",
            data=csv,
            file_name=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No audit logs found")


elif page == "⚙️ Settings":
    st.title("⚙️ Configuration & Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Data Management")
        
        if st.button("Generate Sample Data (100 cases)"):
            with st.spinner("Generating sample data..."):
                sample_df = generate_sample_data(100)
                
                # Score all cases
                engine = st.session_state.risk_engine
                scored_cases = []
                for idx, row in sample_df.iterrows():
                    score_result = engine.score_case(row.to_dict())
                    score_result.update(row.to_dict())
                    scored_cases.append(score_result)
                
                scored_df = pd.DataFrame(scored_cases)
                
                # Insert to DB
                st.session_state.db.batch_insert_cases(scored_df)
                st.success(f"✅ Generated and scored {len(sample_df)} cases")
        
        if st.button("Load from CSV"):
            st.write("Upload a CSV file with risk data")
            uploaded = st.file_uploader("Choose CSV", type=['csv'])
            if uploaded:
                df = pd.read_csv(uploaded)
                st.write(f"Loaded {len(df)} rows")
        
        if st.button("Clear All Data"):
            if st.checkbox("Confirm clear"):
                os.remove("risk_cases.db")
                st.session_state.db = RiskDatabase("risk_cases.db")
                st.success("✅ Database cleared")
    
    with col2:
        st.subheader("🤖 LLM Configuration")
        
        api_key = st.text_input("Google Gemini API Key (leave empty to skip)",
                               type="password",
                               help="Get from https://makersuite.google.com/app/apikey")
        
        if api_key:
            st.success("✅ API Key configured")
            if st.button("Test Gemini Connection"):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=api_key)
                    st.success("✅ Connection successful")
                except Exception as e:
                    st.error(f"❌ Connection failed: {e}")
        else:
            st.warning("⚠️ LLM explanations disabled")
        
        st.markdown("---")
        st.subheader("📈 Risk Engine Config")
        
        st.write("**Current Rules:**")
        rules = st.session_state.risk_engine.RULES
        for rule, value in rules.items():
            st.write(f"• {rule}: {value}")

# Footer
st.markdown("---")
st.markdown(
    "🛡️ **Risk Automation Engine** | Fintech Risk Operations | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)
