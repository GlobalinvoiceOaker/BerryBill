import streamlit as st
import pandas as pd
import os
from utils.data_processor import validate_data, process_data

st.set_page_config(
    page_title="Import Data - Invoice Management System",
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
st.markdown('<div class="main-header">Import Data</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Upload and process sell-out data from partners (Masters)</div>', unsafe_allow_html=True)

# File upload
uploaded_file = st.file_uploader("Upload Excel file with sell-out data", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file)
        
        # Show raw data
        st.markdown('<div class="sub-header">Raw Data Preview</div>', unsafe_allow_html=True)
        st.dataframe(df.head(10), use_container_width=True)
        
        # Validate data
        is_valid, error_message = validate_data(df)
        
        if is_valid:
            st.success("Data validation successful! The uploaded file has all required columns.")
            
            # Process data
            if st.button("Process Data"):
                with st.spinner("Processing data..."):
                    processed_data = process_data(df)
                    
                    # Store in session state
                    st.session_state.imported_data = processed_data
                    
                    # Display processed data
                    st.markdown('<div class="sub-header">Processed Data</div>', unsafe_allow_html=True)
                    st.dataframe(processed_data, use_container_width=True)
                    
                    # Show summary
                    st.markdown('<div class="sub-header">Data Summary</div>', unsafe_allow_html=True)
                    
                    # Create summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Records", len(processed_data))
                    
                    with col2:
                        st.metric("Total Amount", f"${processed_data['Amount'].sum():,.2f}")
                    
                    with col3:
                        st.metric("Total Partners", processed_data['Partner'].nunique())
                    
                    with col4:
                        st.metric("Total Countries", processed_data['Country'].nunique())
                    
                    # Show detailed summary
                    with st.expander("View Detailed Summary"):
                        # By partner
                        st.markdown("#### By Partner")
                        partner_summary = processed_data.groupby('Partner').agg({
                            'Amount': 'sum',
                            'Royalty Amount': 'sum',
                            'Ad Fund Amount': 'sum',
                            'Tax Amount': 'sum',
                            'Total Amount': 'sum'
                        }).reset_index()
                        st.dataframe(partner_summary, use_container_width=True)
                        
                        # By country
                        st.markdown("#### By Country")
                        country_summary = processed_data.groupby('Country').agg({
                            'Amount': 'sum',
                            'Royalty Amount': 'sum',
                            'Ad Fund Amount': 'sum',
                            'Tax Amount': 'sum',
                            'Total Amount': 'sum'
                        }).reset_index()
                        st.dataframe(country_summary, use_container_width=True)
                    
                    # Next steps
                    st.success("Data processing complete! You can now proceed to generate invoices.")
                    if st.button("Go to Generate Invoices"):
                        st.switch_page("pages/02_Generate_Invoices.py")
        else:
            st.error(f"Data validation failed: {error_message}")
            
            # Show required format
            with st.expander("View Required Data Format"):
                st.markdown("""
                The uploaded Excel file must contain the following columns:
                
                - **Date**: Date of the transaction (required format: YYYY-MM-DD)
                - **Partner**: Name of the partner/master
                - **Country**: Country code (must be one of the supported countries)
                - **Amount**: Numeric value representing the sell-out amount
                - **Currency**: Currency code (e.g., USD, EUR, GBP)
                
                Example:
                
                | Date       | Partner      | Country | Amount  | Currency |
                |------------|--------------|---------|---------|----------|
                | 2023-10-01 | Partner Name | US      | 10000.0 | USD      |
                | 2023-10-02 | Another Co   | UK      | 8500.5  | GBP      |
                
                Make sure all required columns are present and data is in the correct format.
                """)
    
    except Exception as e:
        st.error(f"Error reading the file: {str(e)}")
        st.info("Please ensure you're uploading a valid Excel file (.xlsx or .xls)")
else:
    # Display sample data format
    st.info("Please upload an Excel file with sell-out data to proceed.")
    
    with st.expander("View Required Data Format"):
        st.markdown("""
        The uploaded Excel file must contain the following columns:
        
        - **Date**: Date of the transaction (required format: YYYY-MM-DD)
        - **Partner**: Name of the partner/master
        - **Country**: Country code (must be one of the supported countries)
        - **Amount**: Numeric value representing the sell-out amount
        - **Currency**: Currency code (e.g., USD, EUR, GBP)
        
        Example:
        
        | Date       | Partner      | Country | Amount  | Currency |
        |------------|--------------|---------|---------|----------|
        | 2023-10-01 | Partner Name | US      | 10000.0 | USD      |
        | 2023-10-02 | Another Co   | UK      | 8500.5  | GBP      |
        
        Make sure all required columns are present and data is in the correct format.
        """)
