import streamlit as st
import requests
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import os

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
st.set_page_config(
    page_title="AI Expense Analyzer",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# Styles
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4B5563;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #F3F4F6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #E5E7EB;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .stButton>button {
        width: 100%;
        background-color: #2563EB;
        color: white;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Session State
# -----------------------------------------------------------------------------
if 'data' not in st.session_state:
    st.session_state.data = None
if 'analysis' not in st.session_state:
    st.session_state.analysis = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# -----------------------------------------------------------------------------
# API Client
# -----------------------------------------------------------------------------
def upload_file(file):
    try:
        files = {"file": (file.name, file, file.type)}
        response = requests.post(f"{API_URL}/api/upload", files=files)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Upload failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def get_transactions():
    try:
        response = requests.get(f"{API_URL}/api/transactions")
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None

def run_analysis():
    try:
        response = requests.get(f"{API_URL}/api/analysis")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Analysis failed: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

def chat_with_agent(message):
    try:
        response = requests.post(f"{API_URL}/api/chat", json={"message": message})
        if response.status_code == 200:
            return response.json().get("response")
        else:
            return f"Error: {response.text}"
    except Exception as e:
        return f"Connection error: {e}"

# -----------------------------------------------------------------------------
# UI Components
# -----------------------------------------------------------------------------
def sidebar():
    st.sidebar.title("💸 AI Expense Analyzer")
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### Actions")
    if st.sidebar.button("Refresh Data"):
        data = get_transactions()
        if data:
            st.session_state.data = data
            st.success("Data refreshed!")
            st.rerun()
            
    if st.sidebar.button("Run AI Analysis"):
        with st.spinner("Analyzing financial data..."):
            analysis = run_analysis()
            if analysis:
                st.session_state.analysis = analysis
                st.rerun()

def dashboard():
    st.markdown('<div class="main-header">Dashboard</div>', unsafe_allow_html=True)
    
    # -------------------------------------------------------------------------
    # File Uploader Section (Prominent Drag & Drop)
    # -------------------------------------------------------------------------
    with st.expander("📤 Upload Bank Statement or Invoice", expanded=True):
        uploaded_file = st.file_uploader(
            "Drag and drop your PDF or Excel file here", 
            type=['pdf', 'xls', 'xlsx'],
            help="Supported formats: .pdf, .xls, .xlsx"
        )
        
        if uploaded_file:
            if st.button("Process Document", type="primary"):
                with st.spinner("Uploading and extracting..."):
                    result = upload_file(uploaded_file)
                    if result:
                        st.success(f"Processed as {result.get('doc_type', 'unknown')}")
                        st.session_state.data = result.get('data')
                        st.rerun()

    st.markdown("---")
    
    data = st.session_state.data
    if not data or not data.get('transactions'):
        st.info("👋 Upload a document above to see your financial data here.")
        return

    # Account Info
    account_info = data.get('account_info', data) # Handle both structures
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Account Holder", account_info.get('account_holder', 'N/A'))
    with col2:
        st.metric("Bank", account_info.get('bank_name', 'N/A'))
    with col3:
        bal = account_info.get('closing_balance')
        st.metric("Closing Balance", f"₹{bal:,.2f}" if bal is not None else "N/A")

    # Transactions
    st.subheader("Recent Transactions")
    transactions = data.get('transactions', [])
    df = pd.DataFrame(transactions)
    
    if not df.empty:
        # Format for display
        display_df = df.copy()
        if 'date' in display_df.columns:
            display_df['date'] = pd.to_datetime(display_df['date'], format='%d/%m/%Y', errors='coerce').dt.date
        
        st.dataframe(
            display_df[['date', 'description', 'withdrawal', 'deposit', 'balance']], 
            use_container_width=True,
            column_config={
                "withdrawal": st.column_config.NumberColumn("Withdrawal", format="₹%.2f"),
                "deposit": st.column_config.NumberColumn("Deposit", format="₹%.2f"),
                "balance": st.column_config.NumberColumn("Balance", format="₹%.2f"),
            }
        )

def analysis_view():
    st.markdown('<div class="main-header">AI Analysis</div>', unsafe_allow_html=True)
    
    analysis = st.session_state.analysis
    if not analysis:
        st.warning("No analysis report found. Click 'Run AI Analysis' in the sidebar.")
        return

    report = analysis.get('report', {})
    insights = analysis.get('insights', "")
    
    # Tabs
    tab1, tab2 = st.tabs(["📊 Reports & Charts", "🧠 AI Insights"])
    
    with tab1:
        # Summary Metrics
        summary = report.get('summary', {})
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Income", f"₹{summary.get('total_income', 0):,.2f}", delta=None)
        c2.metric("Total Expenses", f"₹{summary.get('total_expenses', 0):,.2f}", delta="-")
        c3.metric("Net Change", f"₹{summary.get('net_change', 0):,.2f}", delta_color="normal")
        c4.metric("Savings Rate", f"{summary.get('savings_rate', 0)}%")
        
        # Charts
        st.subheader("Spending by Category")
        spending = report.get('spending_by_category', {})
        if spending:
            fig = px.pie(values=list(spending.values()), names=list(spending.keys()), title="Expenses Breakdown")
            st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Spending Trend")
        trend = report.get('spending_trend', {})
        if trend:
            trend_df = pd.DataFrame(list(trend.items()), columns=['Date', 'Amount'])
            fig = px.bar(trend_df, x='Date', y='Amount', title="Daily Spending")
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown(insights)

def chat_interface():
    st.markdown('<div class="main-header">Financial Assistant</div>', unsafe_allow_html=True)
    
    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about your finances..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.spinner("Thinking..."):
            response = chat_with_agent(prompt)
        
        # Add assistant message
        st.session_state.chat_history.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# -----------------------------------------------------------------------------
# Main App Structure
# -----------------------------------------------------------------------------
sidebar()

# Page Routing
page = st.sidebar.radio("Navigate", ["Dashboard", "Analysis", "Chat"])

if page == "Dashboard":
    dashboard()
elif page == "Analysis":
    analysis_view()
elif page == "Chat":
    chat_interface()

# On load logic
if st.session_state.data is None:
    # Try to load existing data
    data = get_transactions()
    if data and data.get('transactions'):
        st.session_state.data = data
