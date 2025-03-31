import pandas as pd
import json
import os
import streamlit as st
from datetime import datetime

def load_country_settings():
    """
    Load country settings from the JSON file
    """
    try:
        with open('data/country_settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default settings if file doesn't exist
        return {
            "US": {"royalty_rate": 0.05, "ad_fund_rate": 0.02, "tax_rate": 0.0},
            "UK": {"royalty_rate": 0.06, "ad_fund_rate": 0.02, "tax_rate": 0.20},
            "BR": {"royalty_rate": 0.06, "ad_fund_rate": 0.02, "tax_rate": 0.17},
            "CA": {"royalty_rate": 0.05, "ad_fund_rate": 0.02, "tax_rate": 0.05},
            "DE": {"royalty_rate": 0.05, "ad_fund_rate": 0.02, "tax_rate": 0.19},
            "FR": {"royalty_rate": 0.05, "ad_fund_rate": 0.02, "tax_rate": 0.20},
            "ES": {"royalty_rate": 0.05, "ad_fund_rate": 0.02, "tax_rate": 0.21}
        }

def save_country_settings(settings):
    """
    Save country settings to the JSON file
    """
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    with open('data/country_settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

def validate_data(df):
    """
    Validate the imported data
    
    Returns:
    - (bool, str): (is_valid, error_message)
    """
    required_columns = ['Date', 'Partner', 'Country', 'Amount', 'Currency']
    
    # Check if required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check for missing values in required fields
    for col in required_columns:
        if df[col].isnull().any():
            return False, f"Missing values in '{col}' column"
    
    # Check if dates are valid
    try:
        pd.to_datetime(df['Date'])
    except:
        return False, "Invalid date format in 'Date' column"
    
    # Check if amounts are numeric
    try:
        pd.to_numeric(df['Amount'])
    except:
        return False, "Invalid numeric values in 'Amount' column"
    
    # Check if countries are supported
    country_settings = load_country_settings()
    unsupported_countries = df[~df['Country'].isin(country_settings.keys())]['Country'].unique()
    if len(unsupported_countries) > 0:
        return False, f"Unsupported countries found: {', '.join(unsupported_countries)}"
    
    return True, ""

def process_data(df):
    """
    Process the imported data and calculate royalties, ad fund, and taxes
    
    Returns:
    - DataFrame with additional calculated columns
    """
    # Load country settings
    country_settings = load_country_settings()
    
    # Convert date column to datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Ensure Amount is numeric
    df['Amount'] = pd.to_numeric(df['Amount'])
    
    # Create new columns for calculations
    df['Royalty Rate'] = df['Country'].map({country: data['royalty_rate'] for country, data in country_settings.items()})
    df['Ad Fund Rate'] = df['Country'].map({country: data['ad_fund_rate'] for country, data in country_settings.items()})
    df['Tax Rate'] = df['Country'].map({country: data['tax_rate'] for country, data in country_settings.items()})
    
    # Calculate amounts
    df['Royalty Amount'] = df['Amount'] * df['Royalty Rate']
    df['Ad Fund Amount'] = df['Amount'] * df['Ad Fund Rate']
    df['Subtotal'] = df['Royalty Amount'] + df['Ad Fund Amount']
    df['Tax Amount'] = df['Subtotal'] * df['Tax Rate']
    df['Total Amount'] = df['Subtotal'] + df['Tax Amount']
    
    # Format amounts to 2 decimal places
    for col in ['Royalty Amount', 'Ad Fund Amount', 'Subtotal', 'Tax Amount', 'Total Amount']:
        df[col] = df[col].round(2)
    
    # Add year and month columns for easier grouping
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Month Name'] = df['Date'].dt.strftime('%B')
    
    # Add invoice generation status column
    df['Invoice Generated'] = False
    
    return df

def group_data_by_partner(df):
    """
    Group data by partner and month for invoice generation
    
    Returns:
    - List of dictionaries with grouped data
    """
    grouped_data = []
    
    # Group by partner, country, year, and month
    for (partner, country, year, month), group_df in df.groupby(['Partner', 'Country', 'Year', 'Month']):
        month_name = group_df['Month Name'].iloc[0]
        
        group_data = {
            'partner': partner,
            'country': country,
            'year': year,
            'month': month,
            'month_name': month_name,
            'currency': group_df['Currency'].iloc[0],
            'total_sell_out': group_df['Amount'].sum(),
            'royalty_amount': group_df['Royalty Amount'].sum(),
            'ad_fund_amount': group_df['Ad Fund Amount'].sum(),
            'subtotal': group_df['Subtotal'].sum(),
            'tax_amount': group_df['Tax Amount'].sum(),
            'total_amount': group_df['Total Amount'].sum(),
            'royalty_rate': group_df['Royalty Rate'].iloc[0],
            'ad_fund_rate': group_df['Ad Fund Rate'].iloc[0],
            'tax_rate': group_df['Tax Rate'].iloc[0],
            'details': group_df.to_dict('records'),
            'created_at': datetime.now(),
            'invoice_number': f"{partner[:3].upper()}-{year}{month:02d}-{country}"
        }
        
        grouped_data.append(group_data)
    
    return grouped_data

def import_payment_data(file):
    """
    Import and validate payment data from CSV or Excel file
    
    Returns:
    - (DataFrame, bool, str): (data, is_valid, error_message)
    """
    try:
        # Determine file type based on extension
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, False, "Unsupported file format. Please upload a CSV or Excel file."
        
        # Validate required columns
        required_columns = ['Date', 'Amount', 'Description', 'Reference']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return None, False, f"Missing required columns: {', '.join(missing_columns)}"
        
        # Convert date column to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Ensure Amount is numeric
        df['Amount'] = pd.to_numeric(df['Amount'])
        
        return df, True, ""
    
    except Exception as e:
        return None, False, f"Error importing payment data: {str(e)}"
