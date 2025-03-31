import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.report_generator import generate_invoice_summary_df, get_excel_download_link, generate_charts
import datetime

st.set_page_config(
    page_title="Financial Reports - Invoice Management System",
    page_icon="📊",
    layout="wide"
)

# Custom styling
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
st.markdown('<div class="main-header">Financial Reports</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Generate and view financial reports based on invoice data</div>', unsafe_allow_html=True)

# Check if invoices are generated
if 'invoices' not in st.session_state or not st.session_state.invoices:
    st.warning("No invoices generated. Please generate invoices first.")
    if st.button("Go to Generate Invoices"):
        st.switch_page("pages/02_Generate_Invoices.py")
else:
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    total_invoiced = sum(inv['total_amount'] for inv in st.session_state.invoices)
    total_paid = sum(inv.get('payment_amount', 0) for inv in st.session_state.invoices)
    total_invoices = len(st.session_state.invoices)
    paid_invoices = sum(1 for inv in st.session_state.invoices if inv.get('paid', False))
    
    with col1:
        st.metric("Total Invoiced", f"${total_invoiced:,.2f}")
    
    with col2:
        st.metric("Total Paid", f"${total_paid:,.2f}")
    
    with col3:
        st.metric("Total Invoices", total_invoices)
    
    with col4:
        payment_ratio = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
        st.metric("Payment Ratio", f"{payment_ratio:.1f}%")
    
    # Filter options
    st.markdown('<div class="sub-header">Filter Options</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get unique partners
        partners = sorted(list({inv['partner'] for inv in st.session_state.invoices}))
        selected_partners = st.multiselect("Partners", options=partners, default=partners)
    
    with col2:
        # Get unique countries
        countries = sorted(list({inv['country'] for inv in st.session_state.invoices}))
        selected_countries = st.multiselect("Countries", options=countries, default=countries)
    
    with col3:
        # Get unique periods
        periods = sorted(list({f"{inv['month_name']} {inv['year']}" for inv in st.session_state.invoices}))
        selected_periods = st.multiselect("Periods", options=periods, default=periods)
    
    # Filter invoices based on selection
    filtered_invoices = [
        inv for inv in st.session_state.invoices
        if inv['partner'] in selected_partners
        and inv['country'] in selected_countries
        and f"{inv['month_name']} {inv['year']}" in selected_periods
    ]
    
    # Generate summary dataframe
    summary_df = generate_invoice_summary_df(filtered_invoices)
    
    # Display summary table
    st.markdown('<div class="sub-header">Invoice Summary</div>', unsafe_allow_html=True)
    
    if not summary_df.empty:
        st.dataframe(summary_df, use_container_width=True)
        
        # Download button for Excel report
        st.markdown("#### Download Full Report")
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        st.markdown(get_excel_download_link(filtered_invoices, f"invoice_report_{now}.xlsx"), unsafe_allow_html=True)
        
        # Generate and display charts
        st.markdown('<div class="sub-header">Data Visualization</div>', unsafe_allow_html=True)
        
        payment_status_fig, country_fig, monthly_trend_fig = generate_charts(filtered_invoices)
        
        if payment_status_fig and country_fig and monthly_trend_fig:
            # Create tabs for different charts
            tab1, tab2, tab3 = st.tabs(["Payment Status", "Country Distribution", "Monthly Trends"])
            
            with tab1:
                st.pyplot(payment_status_fig)
            
            with tab2:
                st.pyplot(country_fig)
            
            with tab3:
                st.pyplot(monthly_trend_fig)
        
        # Detailed analysis
        st.markdown('<div class="sub-header">Detailed Analysis</div>', unsafe_allow_html=True)
        
        # Partner analysis
        st.markdown("#### Analysis by Partner")
        partner_analysis = summary_df.groupby('Partner').agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        partner_analysis.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        partner_analysis['Paid Ratio'] = (partner_analysis['Payment Amount'] / partner_analysis['Total Amount'] * 100).round(1).astype(str) + '%'
        st.dataframe(partner_analysis, use_container_width=True)
        
        # Country analysis
        st.markdown("#### Analysis by Country")
        country_analysis = summary_df.groupby('Country').agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        country_analysis.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        country_analysis['Paid Ratio'] = (country_analysis['Payment Amount'] / country_analysis['Total Amount'] * 100).round(1).astype(str) + '%'
        st.dataframe(country_analysis, use_container_width=True)
        
        # Period analysis
        st.markdown("#### Analysis by Period")
        summary_df['Year'] = summary_df['Period'].apply(lambda x: x.split()[-1])
        summary_df['Month'] = summary_df['Period'].apply(lambda x: x.split()[0])
        period_analysis = summary_df.groupby(['Year', 'Month']).agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        period_analysis.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        period_analysis['Paid Ratio'] = (period_analysis['Payment Amount'] / period_analysis['Total Amount'] * 100).round(1).astype(str) + '%'
        st.dataframe(period_analysis, use_container_width=True)
        
        # Status analysis
        st.markdown("#### Analysis by Status")
        status_analysis = summary_df.groupby('Status').agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        status_analysis.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        status_analysis['Paid Ratio'] = (status_analysis['Payment Amount'] / status_analysis['Total Amount'] * 100).round(1).astype(str) + '%'
        st.dataframe(status_analysis, use_container_width=True)
    else:
        st.info("No invoices match the selected filters.")
    
    # Next steps
    st.markdown("#### Next Steps")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Go to Import Data"):
            st.switch_page("pages/01_Import_Data.py")
    
    with col2:
        if st.button("Go to Reconcile Payments"):
            st.switch_page("pages/04_Reconcile_Payments.py")
