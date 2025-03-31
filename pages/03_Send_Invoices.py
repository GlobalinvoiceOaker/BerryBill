import streamlit as st
import pandas as pd
from utils.email_sender import send_invoice_email, get_default_email_template, send_bulk_invoices
import json
import os

st.set_page_config(
    page_title="Send Invoices - Invoice Management System",
    page_icon="📧",
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
st.markdown('<div class="main-header">Send Invoices</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Send generated invoices via email to partners</div>', unsafe_allow_html=True)

# Check if invoices are generated
if 'invoices' not in st.session_state or not st.session_state.invoices:
    st.warning("No invoices generated. Please generate invoices first.")
    if st.button("Go to Generate Invoices"):
        st.switch_page("pages/02_Generate_Invoices.py")
else:
    # Initialize partner emails in session state if not exists
    if 'partner_emails' not in st.session_state:
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Try to load from file
        try:
            with open('data/partner_emails.json', 'r') as f:
                st.session_state.partner_emails = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create empty dictionary if file doesn't exist or is invalid
            st.session_state.partner_emails = {}
    
    # Email configuration
    with st.expander("Email Configuration", expanded=False):
        # Load from session state or environment variables
        smtp_server = st.text_input(
            "SMTP Server",
            value=st.session_state.get('smtp_server', os.getenv('SMTP_SERVER', ''))
        )
        smtp_port = st.text_input(
            "SMTP Port",
            value=st.session_state.get('smtp_port', os.getenv('SMTP_PORT', '587'))
        )
        smtp_username = st.text_input(
            "SMTP Username",
            value=st.session_state.get('smtp_username', os.getenv('SMTP_USERNAME', ''))
        )
        smtp_password = st.text_input(
            "SMTP Password",
            value=st.session_state.get('smtp_password', os.getenv('SMTP_PASSWORD', '')),
            type="password"
        )
        sender_email = st.text_input(
            "Sender Email",
            value=st.session_state.get('sender_email', os.getenv('SENDER_EMAIL', ''))
        )
        
        # Save to session state
        if st.button("Save Email Configuration"):
            st.session_state.smtp_server = smtp_server
            st.session_state.smtp_port = smtp_port
            st.session_state.smtp_username = smtp_username
            st.session_state.smtp_password = smtp_password
            st.session_state.sender_email = sender_email
            st.success("Email configuration saved!")
    
    # Partner email management
    with st.expander("Partner Email Management", expanded=False):
        # Get unique partners from invoices
        partners = sorted(list({inv['partner'] for inv in st.session_state.invoices}))
        
        # Display current partner emails
        st.markdown("#### Current Partner Emails")
        
        partner_emails_df = pd.DataFrame([
            {"Partner": partner, "Email": st.session_state.partner_emails.get(partner, "")}
            for partner in partners
        ])
        
        # Use Streamlit's editable dataframe
        edited_df = st.data_editor(
            partner_emails_df,
            use_container_width=True,
            column_config={
                "Partner": st.column_config.TextColumn("Partner", disabled=True),
                "Email": st.column_config.TextColumn("Email Address")
            },
            hide_index=True
        )
        
        # Save button
        if st.button("Save Partner Emails"):
            # Update session state with edited values
            for _, row in edited_df.iterrows():
                st.session_state.partner_emails[row['Partner']] = row['Email']
            
            # Save to file
            os.makedirs('data', exist_ok=True)
            with open('data/partner_emails.json', 'w') as f:
                json.dump(st.session_state.partner_emails, f, indent=4)
            
            st.success("Partner emails saved successfully!")
    
    # Display invoices to send
    st.markdown('<div class="sub-header">Invoices to Send</div>', unsafe_allow_html=True)
    
    # Filter invoices that haven't been sent yet
    unsent_invoices = [inv for inv in st.session_state.invoices if not inv.get('sent', False)]
    
    if not unsent_invoices:
        st.info("All invoices have been sent.")
    else:
        # Convert to DataFrame for easier display
        invoices_df = pd.DataFrame([
            {
                "Select": False,
                "Invoice #": inv['invoice_number'],
                "Partner": inv['partner'],
                "Country": inv['country'],
                "Period": f"{inv['month_name']} {inv['year']}",
                "Total Amount": f"{inv['currency']} {inv['total_amount']:,.2f}",
                "Generated Date": inv['created_at'].strftime("%Y-%m-%d") if hasattr(inv['created_at'], 'strftime') else inv['created_at'],
                "Recipient Email": st.session_state.partner_emails.get(inv['partner'], "")
            } for inv in unsent_invoices
        ])
        
        # Use Streamlit's editable dataframe for selection
        selected_df = st.data_editor(
            invoices_df,
            use_container_width=True,
            column_config={
                "Select": st.column_config.CheckboxColumn("Select", default=False),
                "Invoice #": st.column_config.TextColumn("Invoice #", disabled=True),
                "Partner": st.column_config.TextColumn("Partner", disabled=True),
                "Country": st.column_config.TextColumn("Country", disabled=True),
                "Period": st.column_config.TextColumn("Period", disabled=True),
                "Total Amount": st.column_config.TextColumn("Total Amount", disabled=True),
                "Generated Date": st.column_config.TextColumn("Generated Date", disabled=True),
                "Recipient Email": st.column_config.TextColumn("Recipient Email")
            },
            hide_index=True
        )
        
        # Filtering selected invoices
        selected_invoices_df = selected_df[selected_df['Select']]
        
        # Email template
        if not selected_invoices_df.empty:
            st.markdown('<div class="sub-header">Email Template</div>', unsafe_allow_html=True)
            
            # Get the first selected invoice for template preview
            first_selected_idx = selected_df[selected_df['Select']].index[0]
            first_selected_invoice_number = selected_df.loc[first_selected_idx, 'Invoice #']
            selected_invoice = next((inv for inv in unsent_invoices if inv['invoice_number'] == first_selected_invoice_number), None)
            
            if selected_invoice:
                # Get default template
                template = get_default_email_template(selected_invoice)
                
                # Allow customization
                email_subject = st.text_input("Email Subject", value=template['subject'])
                email_body = st.text_area("Email Body", value=template['body'], height=300)
                
                # Send emails
                if st.button("Send Selected Invoices"):
                    # Check if all selected invoices have recipient emails
                    missing_emails = selected_df[(selected_df['Select']) & (selected_df['Recipient Email'] == "")]
                    
                    if not missing_emails.empty:
                        st.error(f"Missing recipient emails for {len(missing_emails)} partners. Please add all recipient emails before sending.")
                    else:
                        with st.spinner("Sending invoices..."):
                            # Create email mapping
                            email_mapping = {}
                            for _, row in selected_df[selected_df['Select']].iterrows():
                                email_mapping[row['Partner']] = row['Recipient Email']
                                # Also update the partner_emails session state
                                st.session_state.partner_emails[row['Partner']] = row['Recipient Email']
                            
                            # Save updated partner emails to file
                            with open('data/partner_emails.json', 'w') as f:
                                json.dump(st.session_state.partner_emails, f, indent=4)
                            
                            # Get selected invoices
                            selected_invoice_numbers = selected_df[selected_df['Select']]['Invoice #'].tolist()
                            selected_invoices = [inv for inv in unsent_invoices if inv['invoice_number'] in selected_invoice_numbers]
                            
                            # Send emails
                            success_count, fail_count, failed_invoices = send_bulk_invoices(selected_invoices, email_mapping)
                            
                            if fail_count == 0:
                                st.success(f"Successfully sent {success_count} invoices!")
                            else:
                                st.warning(f"Sent {success_count} invoices, but {fail_count} failed.")
                                
                                # Show failed invoices
                                st.error("Failed Invoices:")
                                for failed in failed_invoices:
                                    st.markdown(f"- **{failed['invoice_number']}** ({failed['partner']}): {failed['error']}")
        
        # View sent invoices
        st.markdown('<div class="sub-header">Sent Invoices</div>', unsafe_allow_html=True)
        
        # Filter invoices that have been sent
        sent_invoices = [inv for inv in st.session_state.invoices if inv.get('sent', False)]
        
        if not sent_invoices:
            st.info("No invoices have been sent yet.")
        else:
            # Convert to DataFrame for easier display
            sent_invoices_df = pd.DataFrame([
                {
                    "Invoice #": inv['invoice_number'],
                    "Partner": inv['partner'],
                    "Country": inv['country'],
                    "Period": f"{inv['month_name']} {inv['year']}",
                    "Total Amount": f"{inv['currency']} {inv['total_amount']:,.2f}",
                    "Generated Date": inv['created_at'].strftime("%Y-%m-%d") if hasattr(inv['created_at'], 'strftime') else inv['created_at'],
                    "Status": "Paid" if inv.get('paid', False) else "Sent"
                } for inv in sent_invoices
            ])
            
            st.dataframe(sent_invoices_df, use_container_width=True)
        
        # Next steps
        st.markdown("#### Next Steps")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Go to Reconcile Payments"):
                st.switch_page("pages/04_Reconcile_Payments.py")
        
        with col2:
            if st.button("Go to Financial Reports"):
                st.switch_page("pages/05_Financial_Reports.py")
