import streamlit as st
import os
import base64
from datetime import datetime
import pandas as pd

# Initialize session state if not already done
if 'imported_data' not in st.session_state:
    st.session_state.imported_data = None
if 'invoices' not in st.session_state:
    st.session_state.invoices = []
if 'payments' not in st.session_state:
    st.session_state.payments = None
if 'reconciled_invoices' not in st.session_state:
    st.session_state.reconciled_invoices = []

# App title and description
st.set_page_config(
    page_title="Invoice Management System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling to match requirements
# Purple (#4A1F60) as primary color
# White (#FFFFFF) for backgrounds and text
# Dark purple (#3A174E) for buttons
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #4A1F60;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3A174E;
        margin-top: 1rem;
    }
    .description {
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.markdown('<div class="main-header">Invoice Management System</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Streamline your invoice workflow with automated calculations, PDF generation, and payment reconciliation.</div>', unsafe_allow_html=True)

# Dashboard overview
st.markdown('<div class="sub-header">Dashboard Overview</div>', unsafe_allow_html=True)

# Create a 3-column layout for the dashboard metrics
col1, col2, col3 = st.columns(3)

with col1:
    num_invoices = len(st.session_state.invoices) if hasattr(st.session_state, 'invoices') else 0
    st.metric(label="Total Invoices", value=num_invoices)

with col2:
    num_sent = sum(1 for inv in st.session_state.invoices if inv.get('sent', False)) if hasattr(st.session_state, 'invoices') else 0
    st.metric(label="Invoices Sent", value=num_sent)

with col3:
    num_paid = sum(1 for inv in st.session_state.invoices if inv.get('paid', False)) if hasattr(st.session_state, 'invoices') else 0
    st.metric(label="Invoices Paid", value=num_paid)

# Recent activity
st.markdown('<div class="sub-header">Recent Activity</div>', unsafe_allow_html=True)

if not st.session_state.invoices:
    st.info("No recent activity. Start by importing data in the Import Data section.")
else:
    # Show 5 most recent invoices
    recent_invoices = sorted(st.session_state.invoices, key=lambda x: x.get('created_at', datetime.now()), reverse=True)[:5]
    
    activity_df = pd.DataFrame([
        {
            "Invoice #": inv.get('invoice_number', 'N/A'),
            "Customer": inv.get('customer', 'N/A'),
            "Amount": f"${inv.get('total_amount', 0):,.2f}",
            "Status": "Paid" if inv.get('paid', False) else "Sent" if inv.get('sent', False) else "Generated",
            "Date": inv.get('created_at', datetime.now()).strftime('%Y-%m-%d')
        } for inv in recent_invoices
    ])
    
    st.dataframe(activity_df, use_container_width=True)

# Quick actions section
st.markdown('<div class="sub-header">Quick Actions</div>', unsafe_allow_html=True)

# Create a 3-column layout for quick action buttons
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Import Data", use_container_width=True):
        st.switch_page("pages/01_Import_Data.py")

with col2:
    if st.button("Generate Invoices", use_container_width=True):
        st.switch_page("pages/02_Generate_Invoices.py")

with col3:
    if st.button("View Reports", use_container_width=True):
        st.switch_page("pages/05_Financial_Reports.py")

# Instructions section
with st.expander("How to use this application"):
    st.markdown("""
    ### Getting Started
    1. **Import Data**: Upload your Excel file with sell-out data from partners.
    2. **Generate Invoices**: System will calculate royalties, ad fund, and taxes automatically.
    3. **Send Invoices**: Send generated invoices to registered contacts.
    4. **Reconcile Payments**: Upload bank statements to match payments with invoices.
    5. **Generate Reports**: Create consolidated financial reports for analysis.
    
    ### Tips
    - Ensure your Excel data follows the required format
    - Check country settings to ensure correct tax and royalty calculations
    - Review generated invoices before sending
    - Regularly reconcile payments to keep financial records up-to-date
    """)

# Footer
st.markdown("---")
st.markdown("© 2023 Invoice Management System | Powered by Streamlit")
