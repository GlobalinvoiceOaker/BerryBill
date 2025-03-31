import streamlit as st
import pandas as pd
from datetime import datetime
from utils.invoice_generator import generate_invoices_from_data, get_invoice_download_link

st.set_page_config(
    page_title="Generate Invoices - Invoice Management System",
    page_icon="📄",
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
st.markdown('<div class="main-header">Generate Invoices</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Create invoices based on processed data and calculations</div>', unsafe_allow_html=True)

# Check if data is imported
if st.session_state.imported_data is None:
    st.warning("No data imported. Please import data first.")
    if st.button("Go to Import Data"):
        st.switch_page("pages/01_Import_Data.py")
else:
    # Display data summary
    processed_data = st.session_state.imported_data
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Partners", processed_data['Partner'].nunique())
    
    with col2:
        st.metric("Total Countries", processed_data['Country'].nunique())
    
    with col3:
        st.metric("Total Sell-Out", f"${processed_data['Amount'].sum():,.2f}")
    
    with col4:
        st.metric("Total Invoice Amount", f"${processed_data['Total Amount'].sum():,.2f}")
    
    # Generate invoices section
    st.markdown('<div class="sub-header">Generate Invoices</div>', unsafe_allow_html=True)
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        selected_partners = st.multiselect(
            "Select Partners",
            options=processed_data['Partner'].unique(),
            default=list(processed_data['Partner'].unique())
        )
    
    with col2:
        selected_countries = st.multiselect(
            "Select Countries",
            options=processed_data['Country'].unique(),
            default=list(processed_data['Country'].unique())
        )
    
    # Filter data
    filtered_data = processed_data[
        processed_data['Partner'].isin(selected_partners) &
        processed_data['Country'].isin(selected_countries)
    ]
    
    # Display filtered data
    st.markdown("#### Filtered Data Preview")
    st.dataframe(filtered_data.head(10), use_container_width=True)
    
    # Generate invoices button
    if st.button("Generate Invoices"):
        with st.spinner("Generating invoices..."):
            # Generate invoices
            invoices = generate_invoices_from_data(filtered_data)
            
            # Store in session state (add to existing invoices if any)
            if 'invoices' not in st.session_state:
                st.session_state.invoices = []
            
            # Check for duplicates and add only new invoices
            existing_invoice_numbers = [inv['invoice_number'] for inv in st.session_state.invoices]
            new_invoices = [inv for inv in invoices if inv['invoice_number'] not in existing_invoice_numbers]
            
            st.session_state.invoices.extend(new_invoices)
            
            st.success(f"{len(new_invoices)} invoices generated successfully!")
    
    # Display generated invoices
    if 'invoices' in st.session_state and st.session_state.invoices:
        st.markdown('<div class="sub-header">Generated Invoices</div>', unsafe_allow_html=True)
        
        # Convert to DataFrame for easier display
        invoices_df = pd.DataFrame([
            {
                "Invoice #": inv['invoice_number'],
                "Partner": inv['partner'],
                "Country": inv['country'],
                "Period": f"{inv['month_name']} {inv['year']}",
                "Total Amount": f"{inv['currency']} {inv['total_amount']:,.2f}",
                "Generated Date": inv['created_at'].strftime("%Y-%m-%d") if hasattr(inv['created_at'], 'strftime') else inv['created_at'],
                "Status": "Sent" if inv.get('sent', False) else "Generated"
            } for inv in st.session_state.invoices
        ])
        
        st.dataframe(invoices_df, use_container_width=True)
        
        # Invoice details and download
        selected_invoice_idx = st.selectbox(
            "Select an invoice to view details",
            options=range(len(st.session_state.invoices)),
            format_func=lambda i: f"{st.session_state.invoices[i]['invoice_number']} - {st.session_state.invoices[i]['partner']} ({st.session_state.invoices[i]['month_name']} {st.session_state.invoices[i]['year']})"
        )
        
        if selected_invoice_idx is not None:
            selected_invoice = st.session_state.invoices[selected_invoice_idx]
            
            # Display invoice details
            with st.expander("Invoice Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Invoice Number:** {selected_invoice['invoice_number']}")
                    st.markdown(f"**Partner:** {selected_invoice['partner']}")
                    st.markdown(f"**Country:** {selected_invoice['country']}")
                    st.markdown(f"**Period:** {selected_invoice['month_name']} {selected_invoice['year']}")
                
                with col2:
                    st.markdown(f"**Total Sell-Out:** {selected_invoice['currency']} {selected_invoice['total_sell_out']:,.2f}")
                    st.markdown(f"**Royalty Amount:** {selected_invoice['currency']} {selected_invoice['royalty_amount']:,.2f}")
                    st.markdown(f"**Ad Fund Amount:** {selected_invoice['currency']} {selected_invoice['ad_fund_amount']:,.2f}")
                    st.markdown(f"**Tax Amount:** {selected_invoice['currency']} {selected_invoice['tax_amount']:,.2f}")
                    st.markdown(f"**Total Amount:** {selected_invoice['currency']} {selected_invoice['total_amount']:,.2f}")
                
                # Download link
                st.markdown(get_invoice_download_link(selected_invoice), unsafe_allow_html=True)
        
        # Next steps
        st.markdown("#### Next Steps")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Send Invoices"):
                st.switch_page("pages/03_Send_Invoices.py")
        
        with col2:
            if st.button("Reconcile Payments"):
                st.switch_page("pages/04_Reconcile_Payments.py")
