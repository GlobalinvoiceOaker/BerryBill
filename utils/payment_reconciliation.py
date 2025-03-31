import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

def extract_invoice_number(text):
    """
    Extract invoice number from a text string
    
    Parameters:
    - text: Text string that might contain an invoice number
    
    Returns:
    - str or None: Extracted invoice number or None if not found
    """
    # Pattern for invoice numbers (assuming format like AAA-YYYYMM-CC)
    pattern = r'[A-Z]{3}-\d{6}-[A-Z]{2}'
    
    if isinstance(text, str):
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None

def find_potential_matches(payment, invoices, fuzzy_date_range=10):
    """
    Find potential invoice matches for a payment
    
    Parameters:
    - payment: Dictionary containing payment information
    - invoices: List of invoice dictionaries
    - fuzzy_date_range: Number of days before/after invoice date to consider
    
    Returns:
    - list: List of dictionaries with potential matches and scores
    """
    matches = []
    
    # Extract invoice number from payment description or reference
    invoice_number = extract_invoice_number(payment['Description']) or extract_invoice_number(payment['Reference'])
    
    for invoice in invoices:
        # Skip already fully paid invoices
        if invoice.get('paid', False) and invoice.get('payment_amount', 0) >= invoice['total_amount']:
            continue
        
        score = 0
        reasons = []
        
        # Exact invoice number match (strongest indicator)
        if invoice_number and invoice_number == invoice['invoice_number']:
            score += 100
            reasons.append("Invoice number match")
        
        # Amount match (strong indicator)
        remaining_amount = invoice['total_amount'] - invoice.get('payment_amount', 0)
        if abs(payment['Amount'] - remaining_amount) < 0.01:
            score += 50
            reasons.append("Amount match")
        elif abs(payment['Amount'] - invoice['total_amount']) < 0.01:
            score += 45
            reasons.append("Total amount match")
        
        # Close amount (weaker indicator)
        elif abs(payment['Amount'] - remaining_amount) / remaining_amount < 0.1:
            score += 20
            reasons.append("Close amount (within 10%)")
        
        # Date range match (moderate indicator)
        invoice_date = invoice['created_at']
        payment_date = payment['Date']
        
        if isinstance(invoice_date, str):
            invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
        
        date_diff = abs((payment_date - invoice_date).days)
        if date_diff <= fuzzy_date_range:
            score += 15
            reasons.append(f"Recent invoice (within {date_diff} days)")
        elif date_diff <= 30:
            score += 10
            reasons.append(f"Invoice within 30 days")
        elif date_diff <= 60:
            score += 5
            reasons.append(f"Invoice within 60 days")
        
        # Partner name in description (weak indicator)
        if isinstance(payment['Description'], str) and invoice['partner'].lower() in payment['Description'].lower():
            score += 10
            reasons.append("Partner name in description")
        
        # Add to matches if score is positive
        if score > 0:
            matches.append({
                'invoice': invoice,
                'score': score,
                'reasons': reasons,
                'remaining_amount': remaining_amount
            })
    
    # Sort by score (descending)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return matches

def reconcile_payments(payments_df, invoices):
    """
    Reconcile payments with invoices
    
    Parameters:
    - payments_df: DataFrame containing payment data
    - invoices: List of invoice dictionaries
    
    Returns:
    - tuple: (reconciled_payments, updated_invoices)
    """
    reconciled_payments = []
    
    # Create a copy of invoices to update
    updated_invoices = invoices.copy()
    
    # Process each payment
    for _, payment in payments_df.iterrows():
        payment_dict = payment.to_dict()
        
        # Find potential matches
        matches = find_potential_matches(payment_dict, updated_invoices)
        
        if matches:
            # Get the best match
            best_match = matches[0]
            invoice = best_match['invoice']
            
            # Update the payment with match info
            payment_dict['matched_invoice'] = invoice['invoice_number']
            payment_dict['match_score'] = best_match['score']
            payment_dict['match_reasons'] = best_match['reasons']
            payment_dict['reconciled'] = True
            
            # Update the invoice payment status
            invoice_idx = next((i for i, inv in enumerate(updated_invoices) if inv['invoice_number'] == invoice['invoice_number']), None)
            if invoice_idx is not None:
                # Initialize payment_amount if it doesn't exist
                if 'payment_amount' not in updated_invoices[invoice_idx]:
                    updated_invoices[invoice_idx]['payment_amount'] = 0
                
                # Add this payment amount
                updated_invoices[invoice_idx]['payment_amount'] += payment_dict['Amount']
                
                # Update payment date
                updated_invoices[invoice_idx]['payment_date'] = payment_dict['Date']
                
                # Mark as paid if payment is complete or exceeds invoice amount
                if updated_invoices[invoice_idx]['payment_amount'] >= updated_invoices[invoice_idx]['total_amount']:
                    updated_invoices[invoice_idx]['paid'] = True
                else:
                    updated_invoices[invoice_idx]['paid'] = False
        else:
            # No match found
            payment_dict['matched_invoice'] = None
            payment_dict['match_score'] = 0
            payment_dict['match_reasons'] = []
            payment_dict['reconciled'] = False
        
        reconciled_payments.append(payment_dict)
    
    return reconciled_payments, updated_invoices

def manually_reconcile_payment(payment, invoice, amount, invoices):
    """
    Manually reconcile a payment with an invoice
    
    Parameters:
    - payment: Dictionary containing payment information
    - invoice: Dictionary containing invoice information
    - amount: Amount to apply to the invoice
    - invoices: List of all invoices
    
    Returns:
    - tuple: (updated_payment, updated_invoices)
    """
    # Create a copy of invoices to update
    updated_invoices = invoices.copy()
    
    # Update the payment with match info
    updated_payment = payment.copy()
    updated_payment['matched_invoice'] = invoice['invoice_number']
    updated_payment['match_score'] = 100  # Manual match is 100% confident
    updated_payment['match_reasons'] = ["Manually matched"]
    updated_payment['reconciled'] = True
    
    # Update the invoice payment status
    invoice_idx = next((i for i, inv in enumerate(updated_invoices) if inv['invoice_number'] == invoice['invoice_number']), None)
    if invoice_idx is not None:
        # Initialize payment_amount if it doesn't exist
        if 'payment_amount' not in updated_invoices[invoice_idx]:
            updated_invoices[invoice_idx]['payment_amount'] = 0
        
        # Add this payment amount
        updated_invoices[invoice_idx]['payment_amount'] += amount
        
        # Update payment date
        updated_invoices[invoice_idx]['payment_date'] = payment['Date']
        
        # Mark as paid if payment is complete or exceeds invoice amount
        if updated_invoices[invoice_idx]['payment_amount'] >= updated_invoices[invoice_idx]['total_amount']:
            updated_invoices[invoice_idx]['paid'] = True
        else:
            updated_invoices[invoice_idx]['paid'] = False
    
    return updated_payment, updated_invoices
