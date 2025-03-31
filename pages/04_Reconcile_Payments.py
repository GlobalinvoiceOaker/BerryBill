import streamlit as st
import pandas as pd
from datetime import datetime
from utils.payment_reconciliation import import_payment_data, reconcile_payments, find_potential_matches, manually_reconcile_payment

st.set_page_config(
    page_title="Reconcile Payments - Invoice Management System",
    page_icon="💰",
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
st.markdown('<div class="main-header">Reconcile Payments</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Match bank statement payments with invoices</div>', unsafe_allow_html=True)

# Initialize session states if needed
if 'payments' not in st.session_state:
    st.session_state.payments = None
if 'reconciled_invoices' not in st.session_state:
    st.session_state.reconciled_invoices = []

# Check if invoices are generated
if 'invoices' not in st.session_state or not st.session_state.invoices:
    st.warning("No invoices generated. Please generate invoices first.")
    if st.button("Go to Generate Invoices"):
        st.switch_page("pages/02_Generate_Invoices.py")
else:
    # Payment import section
    st.markdown('<div class="sub-header">Import Bank Statement</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload bank statement (CSV or Excel)", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        # Import payment data
        payments_df, is_valid, error_message = import_payment_data(uploaded_file)
        
        if is_valid:
            st.success("Bank statement imported successfully!")
            
            # Store in session state
            st.session_state.payments = payments_df
            
            # Display payment data
            st.dataframe(payments_df.head(10), use_container_width=True)
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Transactions", len(payments_df))
            
            with col2:
                positive_amounts = payments_df[payments_df['Amount'] > 0]['Amount'].sum()
                st.metric("Total Inflows", f"${positive_amounts:,.2f}")
            
            with col3:
                negative_amounts = payments_df[payments_df['Amount'] < 0]['Amount'].sum()
                st.metric("Total Outflows", f"${abs(negative_amounts):,.2f}")
            
            # Reconciliation section
            st.markdown('<div class="sub-header">Reconcile Payments</div>', unsafe_allow_html=True)
            
            if st.button("Match Payments with Invoices"):
                with st.spinner("Reconciling payments..."):
                    # Filter only incoming payments (positive amounts)
                    incoming_payments = payments_df[payments_df['Amount'] > 0]
                    
                    # Reconcile payments
                    reconciled_payments, updated_invoices = reconcile_payments(incoming_payments, st.session_state.invoices)
                    
                    # Store reconciled data
                    st.session_state.reconciled_payments = reconciled_payments
                    st.session_state.invoices = updated_invoices
                    
                    st.success("Payments reconciled successfully!")
            
            # Display reconciliation results
            if 'reconciled_payments' in st.session_state and st.session_state.reconciled_payments:
                # Show matched payments
                st.markdown("#### Matched Payments")
                
                matched_payments = [p for p in st.session_state.reconciled_payments if p['reconciled']]
                if matched_payments:
                    matched_df = pd.DataFrame([
                        {
                            "Date": p['Date'].strftime("%Y-%m-%d") if hasattr(p['Date'], 'strftime') else p['Date'],
                            "Amount": f"${p['Amount']:,.2f}",
                            "Description": p['Description'],
                            "Reference": p['Reference'],
                            "Matched Invoice": p['matched_invoice'],
                            "Confidence": f"{p['match_score']}%"
                        } for p in matched_payments
                    ])
                    
                    st.dataframe(matched_df, use_container_width=True)
                else:
                    st.info("No payments were automatically matched with invoices.")
                
                # Show unmatched payments
                st.markdown("#### Unmatched Payments")
                
                unmatched_payments = [p for p in st.session_state.reconciled_payments if not p['reconciled']]
                if unmatched_payments:
                    unmatched_df = pd.DataFrame([
                        {
                            "Date": p['Date'].strftime("%Y-%m-%d") if hasattr(p['Date'], 'strftime') else p['Date'],
                            "Amount": f"${p['Amount']:,.2f}",
                            "Description": p['Description'],
                            "Reference": p['Reference']
                        } for p in unmatched_payments
                    ])
                    
                    st.dataframe(unmatched_df, use_container_width=True)
                    
                    # Manual reconciliation
                    st.markdown("#### Manual Reconciliation")
                    
                    # Select unmatched payment
                    selected_payment_idx = st.selectbox(
                        "Select an unmatched payment",
                        options=range(len(unmatched_payments)),
                        format_func=lambda i: f"{unmatched_payments[i]['Date'].strftime('%Y-%m-%d') if hasattr(unmatched_payments[i]['Date'], 'strftime') else unmatched_payments[i]['Date']} - ${unmatched_payments[i]['Amount']:,.2f} - {unmatched_payments[i]['Description'][:30]}..."
                    )
                    
                    if selected_payment_idx is not None:
                        selected_payment = unmatched_payments[selected_payment_idx]
                        
                        # Show payment details
                        st.markdown(f"**Payment Date:** {selected_payment['Date'].strftime('%Y-%m-%d') if hasattr(selected_payment['Date'], 'strftime') else selected_payment['Date']}")
                        st.markdown(f"**Amount:** ${selected_payment['Amount']:,.2f}")
                        st.markdown(f"**Description:** {selected_payment['Description']}")
                        st.markdown(f"**Reference:** {selected_payment['Reference']}")
                        
                        # Find potential matches for the selected payment
                        potential_matches = find_potential_matches(selected_payment, st.session_state.invoices)
                        
                        if potential_matches:
                            st.markdown("**Potential Matching Invoices:**")
                            
                            # Convert potential matches to DataFrame
                            potential_matches_df = pd.DataFrame([
                                {
                                    "Invoice #": match['invoice']['invoice_number'],
                                    "Partner": match['invoice']['partner'],
                                    "Total Amount": f"{match['invoice']['currency']} {match['invoice']['total_amount']:,.2f}",
                                    "Remaining": f"{match['invoice']['currency']} {match['remaining_amount']:,.2f}",
                                    "Match Score": f"{match['score']}%",
                                    "Reasons": ", ".join(match['reasons'])
                                } for match in potential_matches
                            ])
                            
                            # Display potential matches
                            st.dataframe(potential_matches_df, use_container_width=True)
                            
                            # Select an invoice to match
                            selected_invoice_idx = st.selectbox(
                                "Select an invoice to match with this payment",
                                options=range(len(potential_matches)),
                                format_func=lambda i: f"{potential_matches[i]['invoice']['invoice_number']} - {potential_matches[i]['invoice']['partner']} (${potential_matches[i]['remaining_amount']:,.2f})"
                            )
                            
                            if selected_invoice_idx is not None:
                                selected_match = potential_matches[selected_invoice_idx]
                                selected_invoice = selected_match['invoice']
                                
                                # Payment amount options
                                payment_amount = st.number_input(
                                    "Payment amount to apply",
                                    min_value=0.01,
                                    max_value=float(selected_payment['Amount']),
                                    value=min(float(selected_payment['Amount']), selected_match['remaining_amount']),
                                    step=0.01
                                )
                                
                                # Apply payment
                                if st.button("Apply Payment"):
                                    with st.spinner("Applying payment..."):
                                        # Update the payment and invoices
                                        updated_payment, updated_invoices = manually_reconcile_payment(
                                            selected_payment,
                                            selected_invoice,
                                            payment_amount,
                                            st.session_state.invoices
                                        )
                                        
                                        # Update session state
                                        # Find the payment index in the original list
                                        payment_idx = next((i for i, p in enumerate(st.session_state.reconciled_payments) 
                                                          if p['Date'] == updated_payment['Date'] and 
                                                          p['Amount'] == updated_payment['Amount'] and
                                                          p['Description'] == updated_payment['Description']),
                                                         None)
                                        
                                        if payment_idx is not None:
                                            st.session_state.reconciled_payments[payment_idx] = updated_payment
                                        
                                        st.session_state.invoices = updated_invoices
                                        
                                        st.success(f"Payment of ${payment_amount:,.2f} applied to invoice {selected_invoice['invoice_number']}!")
                                        st.rerun()
                        else:
                            st.info("No potential matching invoices found for this payment.")
                else:
                    st.info("All payments have been matched with invoices.")
            
            # Invoice status section
            st.markdown('<div class="sub-header">Invoice Payment Status</div>', unsafe_allow_html=True)
            
            # Convert to DataFrame for easier display
            invoice_status_df = pd.DataFrame([
                {
                    "Invoice #": inv['invoice_number'],
                    "Partner": inv['partner'],
                    "Country": inv['country'],
                    "Period": f"{inv['month_name']} {inv['year']}",
                    "Total Amount": f"{inv['currency']} {inv['total_amount']:,.2f}",
                    "Paid Amount": f"{inv['currency']} {inv.get('payment_amount', 0):,.2f}",
                    "Remaining": f"{inv['currency']} {inv['total_amount'] - inv.get('payment_amount', 0):,.2f}",
                    "Status": "Paid" if inv.get('paid', False) else "Partially Paid" if inv.get('payment_amount', 0) > 0 else "Unpaid",
                    "Payment Date": inv.get('payment_date', '').strftime("%Y-%m-%d") if hasattr(inv.get('payment_date', ''), 'strftime') else inv.get('payment_date', '')
                } for inv in st.session_state.invoices
            ])
            
            st.dataframe(invoice_status_df, use_container_width=True)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_invoiced = sum(inv['total_amount'] for inv in st.session_state.invoices)
                st.metric("Total Invoiced", f"${total_invoiced:,.2f}")
            
            with col2:
                total_paid = sum(inv.get('payment_amount', 0) for inv in st.session_state.invoices)
                st.metric("Total Paid", f"${total_paid:,.2f}")
            
            with col3:
                st.metric("Remaining", f"${total_invoiced - total_paid:,.2f}")
            
            with col4:
                paid_ratio = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
                st.metric("Payment Ratio", f"{paid_ratio:.1f}%")
            
            # Next steps
            st.markdown("#### Next Steps")
            if st.button("Go to Financial Reports"):
                st.switch_page("pages/05_Financial_Reports.py")
        else:
            st.error(f"Error importing bank statement: {error_message}")
            
            # Show required format
            with st.expander("View Required Data Format"):
                st.markdown("""
                The uploaded bank statement must contain the following columns:
                
                - **Date**: Date of the transaction (required format: YYYY-MM-DD)
                - **Amount**: Numeric value (positive for incoming payments, negative for outgoing)
                - **Description**: Description or memo of the transaction
                - **Reference**: Reference number or additional information
                
                Example:
                
                | Date       | Amount   | Description                | Reference    |
                |------------|----------|----------------------------|--------------|
                | 2023-10-15 | 5000.0   | Payment from Partner A     | INV-123      |
                | 2023-10-16 | -2500.0  | Office rent payment        | RENT-OCT     |
                
                Make sure all required columns are present and data is in the correct format.
                """)
    else:
        # Display sample data format
        st.info("Please upload a bank statement file (CSV or Excel) to proceed.")
        
        with st.expander("View Required Data Format"):
            st.markdown("""
            The uploaded bank statement must contain the following columns:
            
            - **Date**: Date of the transaction (required format: YYYY-MM-DD)
            - **Amount**: Numeric value (positive for incoming payments, negative for outgoing)
            - **Description**: Description or memo of the transaction
            - **Reference**: Reference number or additional information
            
            Example:
            
            | Date       | Amount   | Description                | Reference    |
            |------------|----------|----------------------------|--------------|
            | 2023-10-15 | 5000.0   | Payment from Partner A     | INV-123      |
            | 2023-10-16 | -2500.0  | Office rent payment        | RENT-OCT     |
            
            Make sure all required columns are present and data is in the correct format.
            """)
        
        # Show current invoice status
        if st.session_state.invoices:
            st.markdown('<div class="sub-header">Current Invoice Status</div>', unsafe_allow_html=True)
            
            # Convert to DataFrame for easier display
            invoice_status_df = pd.DataFrame([
                {
                    "Invoice #": inv['invoice_number'],
                    "Partner": inv['partner'],
                    "Country": inv['country'],
                    "Period": f"{inv['month_name']} {inv['year']}",
                    "Total Amount": f"{inv['currency']} {inv['total_amount']:,.2f}",
                    "Paid Amount": f"{inv['currency']} {inv.get('payment_amount', 0):,.2f}",
                    "Remaining": f"{inv['currency']} {inv['total_amount'] - inv.get('payment_amount', 0):,.2f}",
                    "Status": "Paid" if inv.get('paid', False) else "Partially Paid" if inv.get('payment_amount', 0) > 0 else "Unpaid",
                    "Payment Date": inv.get('payment_date', '').strftime("%Y-%m-%d") if hasattr(inv.get('payment_date', ''), 'strftime') else inv.get('payment_date', '')
                } for inv in st.session_state.invoices
            ])
            
            st.dataframe(invoice_status_df, use_container_width=True)
