import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import streamlit as st
import base64
import io
import pandas as pd

def create_invoice_pdf(invoice_data):
    """
    Create a PDF invoice from the given data
    
    Parameters:
    - invoice_data: Dictionary containing invoice information
    
    Returns:
    - bytes: PDF file as bytes
    """
    buffer = io.BytesIO()
    
    # Create the PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch/2,
        leftMargin=inch/2,
        topMargin=inch/2,
        bottomMargin=inch/2
    )
    
    # Get styles
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#4A1F60'),
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3A174E'),
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    # Create content elements
    elements = []
    
    # Title
    elements.append(Paragraph("INVOICE", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Invoice info table
    invoice_data_items = [
        ["Invoice Number:", invoice_data['invoice_number']],
        ["Date:", datetime.now().strftime("%Y-%m-%d")],
        ["Due Date:", (datetime.now() + pd.Timedelta(days=30)).strftime("%Y-%m-%d")],
        ["Period:", f"{invoice_data['month_name']} {invoice_data['year']}"]
    ]
    
    invoice_table = Table(invoice_data_items, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#3A174E')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # From-To table (billing info)
    from_to_data = [
        ["From:", "To:"],
        ["Your Company Name", invoice_data['partner']],
        ["Your Address Line 1", "Partner Address Line 1"],
        ["Your City, State, ZIP", "Partner City, State, ZIP"],
        ["Your Country", invoice_data['country']]
    ]
    
    from_to_table = Table(from_to_data, colWidths=[2.5*inch, 2.5*inch])
    from_to_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#3A174E')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(from_to_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Summary header
    elements.append(Paragraph("Summary", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Summary table
    summary_data = [
        ["Description", "Rate", "Amount", f"Amount ({invoice_data['currency']})"],
        ["Total Sell Out", "", "", f"{invoice_data['total_sell_out']:,.2f}"],
        ["Royalties", f"{invoice_data['royalty_rate']*100:.1f}%", "", f"{invoice_data['royalty_amount']:,.2f}"],
        ["Ad Fund", f"{invoice_data['ad_fund_rate']*100:.1f}%", "", f"{invoice_data['ad_fund_amount']:,.2f}"],
        ["Subtotal", "", "", f"{invoice_data['subtotal']:,.2f}"],
        ["Taxes", f"{invoice_data['tax_rate']*100:.1f}%", "", f"{invoice_data['tax_amount']:,.2f}"],
        ["Total Due", "", "", f"{invoice_data['total_amount']:,.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A1F60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F0F0')),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Payment information
    elements.append(Paragraph("Payment Information", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    payment_info = [
        ["Bank Name:", "Your Bank Name"],
        ["Account Name:", "Your Company Name"],
        ["Account Number:", "XXXX-XXXX-XXXX-XXXX"],
        ["Routing Number:", "XXXXXXXXX"],
        ["SWIFT/BIC:", "XXXXXXXXXXX"]
    ]
    
    payment_table = Table(payment_info, colWidths=[2*inch, 3*inch])
    payment_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#3A174E')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(payment_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Terms and notes
    elements.append(Paragraph("Terms and Conditions", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    terms_text = """
    1. Payment is due within 30 days of invoice date.
    2. Please include the invoice number in your payment reference.
    3. For questions regarding this invoice, please contact accounting@yourcompany.com.
    """
    
    elements.append(Paragraph(terms_text, normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the PDF from the buffer
    buffer.seek(0)
    return buffer.getvalue()

def get_invoice_download_link(invoice_data, link_text="Download PDF"):
    """
    Generate a download link for the invoice PDF
    
    Parameters:
    - invoice_data: Dictionary containing invoice information
    - link_text: Text to display for the download link
    
    Returns:
    - str: HTML link for downloading the PDF
    """
    # Generate the PDF
    pdf = create_invoice_pdf(invoice_data)
    
    # Encode to base64
    b64 = base64.b64encode(pdf).decode()
    
    # Generate a safe filename
    filename = f"Invoice_{invoice_data['invoice_number']}_{invoice_data['partner']}.pdf"
    filename = filename.replace(" ", "_")
    
    # Create the download link
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;padding:10px 15px;background-color:#3A174E;color:white;border-radius:5px;">{link_text}</a>'
    
    return href

def generate_invoices_from_data(data):
    """
    Generate invoices from processed data
    
    Parameters:
    - data: DataFrame containing processed sell-out data
    
    Returns:
    - List of generated invoice dictionaries
    """
    from utils.data_processor import group_data_by_partner
    
    # Group data by partner and month
    grouped_data = group_data_by_partner(data)
    
    # Generate invoices
    generated_invoices = []
    for group in grouped_data:
        invoice = {
            **group,
            'sent': False,
            'paid': False,
            'payment_date': None,
            'payment_amount': 0,
            'pdf': create_invoice_pdf(group)
        }
        generated_invoices.append(invoice)
    
    return generated_invoices
