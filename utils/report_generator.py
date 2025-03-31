import pandas as pd
import io
from datetime import datetime
import base64
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np

def generate_invoice_summary_df(invoices):
    """
    Generate a DataFrame summarizing all invoices
    
    Parameters:
    - invoices: List of invoice dictionaries
    
    Returns:
    - DataFrame: Summary of invoices
    """
    if not invoices:
        return pd.DataFrame()
    
    # Extract relevant fields from invoices
    data = []
    for invoice in invoices:
        data.append({
            'Invoice Number': invoice['invoice_number'],
            'Partner': invoice['partner'],
            'Country': invoice['country'],
            'Period': f"{invoice['month_name']} {invoice['year']}",
            'Sell Out Amount': invoice['total_sell_out'],
            'Royalty Amount': invoice['royalty_amount'],
            'Ad Fund Amount': invoice['ad_fund_amount'],
            'Tax Amount': invoice['tax_amount'],
            'Total Amount': invoice['total_amount'],
            'Currency': invoice['currency'],
            'Created Date': invoice['created_at'].strftime('%Y-%m-%d') if hasattr(invoice['created_at'], 'strftime') else invoice['created_at'],
            'Status': 'Paid' if invoice.get('paid', False) else 'Sent' if invoice.get('sent', False) else 'Generated',
            'Payment Date': invoice.get('payment_date', '').strftime('%Y-%m-%d') if hasattr(invoice.get('payment_date', ''), 'strftime') else invoice.get('payment_date', ''),
            'Payment Amount': invoice.get('payment_amount', 0),
            'Balance': invoice['total_amount'] - invoice.get('payment_amount', 0)
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df

def generate_excel_report(invoices):
    """
    Generate an Excel report with invoice data
    
    Parameters:
    - invoices: List of invoice dictionaries
    
    Returns:
    - bytes: Excel file as bytes
    """
    # Create a BytesIO object to save the Excel file
    output = io.BytesIO()
    
    # Create a Pandas Excel writer using the BytesIO object
    writer = pd.ExcelWriter(output, engine='openpyxl')
    
    # Generate the summary DataFrame
    summary_df = generate_invoice_summary_df(invoices)
    
    if summary_df.empty:
        # If no invoices, create a simple message sheet
        pd.DataFrame(['No invoices available']).to_excel(writer, sheet_name='No Data', index=False, header=False)
    else:
        # Write summary sheet
        summary_df.to_excel(writer, sheet_name='Invoice Summary', index=False)
        
        # Generate by country analysis
        country_df = summary_df.groupby('Country').agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        country_df.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        country_df.to_excel(writer, sheet_name='By Country', index=False)
        
        # Generate by partner analysis
        partner_df = summary_df.groupby('Partner').agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        partner_df.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        partner_df.to_excel(writer, sheet_name='By Partner', index=False)
        
        # Generate by period (month/year) analysis
        summary_df['Year'] = summary_df['Period'].apply(lambda x: x.split()[-1])
        summary_df['Month'] = summary_df['Period'].apply(lambda x: x.split()[0])
        period_df = summary_df.groupby(['Year', 'Month']).agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        period_df.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        period_df.to_excel(writer, sheet_name='By Period', index=False)
        
        # Generate payment status analysis
        status_df = summary_df.groupby('Status').agg({
            'Total Amount': 'sum',
            'Payment Amount': 'sum',
            'Balance': 'sum',
            'Invoice Number': 'count'
        }).reset_index()
        status_df.rename(columns={'Invoice Number': 'Invoice Count'}, inplace=True)
        status_df.to_excel(writer, sheet_name='By Status', index=False)
    
    # Save the Excel file
    writer.close()
    
    # Return the Excel file as bytes
    output.seek(0)
    return output.getvalue()

def get_excel_download_link(invoices, filename="invoice_report.xlsx", link_text="Download Excel Report"):
    """
    Generate a download link for the Excel report
    
    Parameters:
    - invoices: List of invoice dictionaries
    - filename: Filename for the Excel file
    - link_text: Text to display for the download link
    
    Returns:
    - str: HTML link for downloading the Excel file
    """
    # Generate the Excel file
    excel_data = generate_excel_report(invoices)
    
    # Encode to base64
    b64 = base64.b64encode(excel_data).decode()
    
    # Create the download link
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" style="text-decoration:none;padding:10px 15px;background-color:#3A174E;color:white;border-radius:5px;">{link_text}</a>'
    
    return href

def generate_charts(invoices):
    """
    Generate charts for invoice visualization
    
    Parameters:
    - invoices: List of invoice dictionaries
    
    Returns:
    - tuple: (payment_status_fig, country_fig, monthly_trend_fig)
    """
    if not invoices:
        return None, None, None
    
    # Get invoice summary data
    summary_df = generate_invoice_summary_df(invoices)
    
    # Create a figure for payment status breakdown
    payment_status_fig, ax1 = plt.subplots(figsize=(8, 5))
    status_counts = summary_df['Status'].value_counts()
    status_colors = {'Paid': '#4CAF50', 'Sent': '#FFC107', 'Generated': '#2196F3'}
    colors = [status_colors.get(status, '#9E9E9E') for status in status_counts.index]
    wedges, texts, autotexts = ax1.pie(
        status_counts, 
        autopct='%1.1f%%',
        startangle=90,
        colors=colors
    )
    ax1.axis('equal')
    ax1.set_title('Invoice Status Breakdown')
    ax1.legend(wedges, status_counts.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Create a figure for country distribution
    country_fig, ax2 = plt.subplots(figsize=(10, 6))
    country_totals = summary_df.groupby('Country')['Total Amount'].sum().sort_values(ascending=False)
    bars = ax2.bar(country_totals.index, country_totals.values, color='#4A1F60')
    ax2.set_xlabel('Country')
    ax2.set_ylabel('Total Amount')
    ax2.set_title('Invoice Amounts by Country')
    ax2.tick_params(axis='x', rotation=45)
    for bar in bars:
        height = bar.get_height()
        ax2.annotate(f'{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom')
    
    # Create a figure for monthly trends
    monthly_trend_fig, ax3 = plt.subplots(figsize=(12, 6))
    summary_df['YearMonth'] = summary_df['Period'].apply(lambda x: x.split()[1] + '-' + x.split()[0])
    monthly_data = summary_df.groupby('YearMonth').agg({
        'Total Amount': 'sum',
        'Payment Amount': 'sum'
    }).reset_index()
    monthly_data = monthly_data.sort_values('YearMonth')
    
    x = np.arange(len(monthly_data['YearMonth']))
    width = 0.35
    
    ax3.bar(x - width/2, monthly_data['Total Amount'], width, label='Invoiced', color='#4A1F60')
    ax3.bar(x + width/2, monthly_data['Payment Amount'], width, label='Paid', color='#3A174E')
    
    ax3.set_xlabel('Period')
    ax3.set_ylabel('Amount')
    ax3.set_title('Monthly Invoice and Payment Trends')
    ax3.set_xticks(x)
    ax3.set_xticklabels(monthly_data['YearMonth'], rotation=45)
    ax3.legend()
    
    plt.tight_layout()
    
    return payment_status_fig, country_fig, monthly_trend_fig
