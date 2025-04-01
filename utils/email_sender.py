import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import streamlit as st
import pandas as pd
import re
import os

def validate_email(email):
    """
    Validate email format
    
    Parameters:
    - email: Email address to validate
    
    Returns:
    - bool: True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return bool(re.match(pattern, email))

def send_invoice_email(recipient_email, subject, body, invoice_pdf, invoice_filename):
    """
    Send invoice via email
    
    Parameters:
    - recipient_email: Email address of recipient
    - subject: Email subject
    - body: Email body content
    - invoice_pdf: PDF file content (bytes)
    - invoice_filename: Filename for the attachment
    
    Returns:
    - tuple: (success, message)
    """
    # Get email configuration from session state or environment variables
    smtp_server = st.session_state.get('smtp_server', os.getenv('SMTP_SERVER', ''))
    smtp_port = st.session_state.get('smtp_port', os.getenv('SMTP_PORT', '587'))
    smtp_username = st.session_state.get('smtp_username', os.getenv('SMTP_USERNAME', ''))
    smtp_password = st.session_state.get('smtp_password', os.getenv('SMTP_PASSWORD', ''))
    sender_email = st.session_state.get('sender_email', os.getenv('SENDER_EMAIL', ''))
    
    # Validate email configuration
    if not all([smtp_server, smtp_port, smtp_username, smtp_password, sender_email]):
        return False, "Email configuration is incomplete. Please check settings."
    
    # Validate recipient email
    if not validate_email(recipient_email):
        return False, f"Invalid recipient email: {recipient_email}"
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        
        # Attach body
        msg.attach(MIMEText(body, 'html'))
        
        # Attach PDF
        attachment = MIMEApplication(invoice_pdf, _subtype='pdf')
        attachment.add_header('Content-Disposition', 'attachment', filename=invoice_filename)
        msg.attach(attachment)
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_username, smtp_password)
        
        # Send email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        
        return True, "Email sent successfully!"
    
    except Exception as e:
        return False, f"Failed to send email: {str(e)}"

def get_default_email_template(invoice_data):
    """
    Get default email template for invoice
    
    Parameters:
    - invoice_data: Dictionary containing invoice information
    
    Returns:
    - dict: Contains subject and body for email
    """
    subject = f"Invoice {invoice_data['invoice_number']} - {invoice_data['month_name']} {invoice_data['year']}"
    
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #4A1F60; color: white; padding: 15px; text-align: center;">
                <h2>Invoice {invoice_data['invoice_number']}</h2>
            </div>
            
            <div style="padding: 20px; border: 1px solid #ddd; border-top: none;">
                <p>Dear {invoice_data['partner']},</p>
                
                <p>Please find attached your invoice for {invoice_data['month_name']} {invoice_data['year']}.</p>
                
                <div style="background-color: #f9f9f9; padding: 15px; margin: 20px 0; border-left: 4px solid #4A1F60;">
                    <p><strong>Invoice Number:</strong> {invoice_data['invoice_number']}</p>
                    <p><strong>Period:</strong> {invoice_data['month_name']} {invoice_data['year']}</p>
                    <p><strong>Total Amount:</strong> {invoice_data['currency']} {invoice_data['total_amount']:,.2f}</p>
                    <p><strong>Due Date:</strong> {(invoice_data['created_at'] + pd.Timedelta(days=30)).strftime('%Y-%m-%d')}</p>
                </div>
                
                <p>For any questions regarding this invoice, please reply to this email or contact our accounting department.</p>
                
                <p>Thank you for your business.</p>
                
                <p>Best regards,<br>
                Your Company Name<br>
                Accounting Department</p>
            </div>
            
            <div style="text-align: center; padding: 10px; font-size: 12px; color: #777;">
                <p>© 2023 Your Company Name. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return {"subject": subject, "body": body}

def send_bulk_invoices(invoices, email_mapping):
    """
    Send multiple invoices via email
    
    Parameters:
    - invoices: List of invoice dictionaries
    - email_mapping: Dictionary mapping partner names to email addresses
    
    Returns:
    - tuple: (success_count, fail_count, failed_invoices)
    """
    success_count = 0
    fail_count = 0
    failed_invoices = []
    
    for invoice in invoices:
        # Skip already sent invoices
        if invoice.get('sent', False):
            continue
        
        # Get recipient email from mapping
        recipient_email = email_mapping.get(invoice['partner'])
        if not recipient_email:
            fail_count += 1
            failed_invoices.append({
                'invoice_number': invoice['invoice_number'],
                'partner': invoice['partner'],
                'error': "No email address found for this partner"
            })
            continue
        
        # Get email template
        template = get_default_email_template(invoice)
        
        # Generate filename
        filename = f"Invoice_{invoice['invoice_number']}_{invoice['partner']}.pdf".replace(" ", "_")
        
        # Send email
        success, message = send_invoice_email(
            recipient_email,
            template['subject'],
            template['body'],
            invoice['pdf'],
            filename
        )
        
        if success:
            success_count += 1
            invoice['sent'] = True
        else:
            fail_count += 1
            failed_invoices.append({
                'invoice_number': invoice['invoice_number'],
                'partner': invoice['partner'],
                'error': message
            })
    
    return success_count, fail_count, failed_invoices
