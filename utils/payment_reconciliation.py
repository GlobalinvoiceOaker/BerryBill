import pandas as pd
import numpy as np
import re
from datetime import datetime, timedelta

def extract_invoice_number(text):
    """
    Extrai o número da fatura de uma string de texto
    
    Parâmetros:
    - text: String de texto que pode conter um número de fatura
    
    Retorna:
    - str ou None: Número da fatura extraído ou None se não encontrado
    """
    # Padrão para números de fatura (assumindo formato como AAA-YYYYMM-CC)
    pattern = r'[A-Z]{3}-\d{6}-[A-Z]{2}'
    
    if isinstance(text, str):
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    
    return None

def find_potential_matches(payment, invoices, fuzzy_date_range=10):
    """
    Encontra possíveis correspondências de faturas para um pagamento
    
    Parâmetros:
    - payment: Dicionário contendo informações de pagamento
    - invoices: Lista de dicionários de faturas
    - fuzzy_date_range: Número de dias antes/depois da data da fatura a considerar
    
    Retorna:
    - list: Lista de dicionários com correspondências potenciais e pontuações
    """
    matches = []
    
    # Extrai o número da fatura da descrição ou referência do pagamento
    invoice_number = extract_invoice_number(payment['Description']) or extract_invoice_number(payment['Reference'])
    
    for invoice in invoices:
        # Ignora faturas já totalmente pagas
        if invoice.get('paid', False) and invoice.get('payment_amount', 0) >= invoice['total_amount']:
            continue
        
        score = 0
        reasons = []
        
        # Correspondência exata do número da fatura (indicador mais forte)
        if invoice_number and invoice_number == invoice['invoice_number']:
            score += 100
            reasons.append("Correspondência do número da fatura")
        
        # Correspondência de valor (indicador forte)
        remaining_amount = invoice['total_amount'] - invoice.get('payment_amount', 0)
        if abs(payment['Amount'] - remaining_amount) < 0.01:
            score += 50
            reasons.append("Correspondência de valor")
        elif abs(payment['Amount'] - invoice['total_amount']) < 0.01:
            score += 45
            reasons.append("Correspondência de valor total")
        
        # Valor próximo (indicador mais fraco)
        elif abs(payment['Amount'] - remaining_amount) / remaining_amount < 0.1:
            score += 20
            reasons.append("Valor próximo (dentro de 10%)")
        
        # Correspondência de intervalo de data (indicador moderado)
        invoice_date = invoice['created_at']
        payment_date = payment['Date']
        
        if isinstance(invoice_date, str):
            invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d')
        
        date_diff = abs((payment_date - invoice_date).days)
        if date_diff <= fuzzy_date_range:
            score += 15
            reasons.append(f"Fatura recente (dentro de {date_diff} dias)")
        elif date_diff <= 30:
            score += 10
            reasons.append(f"Fatura dentro de 30 dias")
        elif date_diff <= 60:
            score += 5
            reasons.append(f"Fatura dentro de 60 dias")
        
        # Nome do parceiro na descrição (indicador fraco)
        if isinstance(payment['Description'], str) and invoice['partner'].lower() in payment['Description'].lower():
            score += 10
            reasons.append("Nome do parceiro na descrição")
        
        # Adiciona às correspondências se a pontuação for positiva
        if score > 0:
            matches.append({
                'invoice': invoice,
                'score': score,
                'reasons': reasons,
                'remaining_amount': remaining_amount
            })
    
    # Ordena por pontuação (decrescente)
    matches.sort(key=lambda x: x['score'], reverse=True)
    
    return matches

def reconcile_payments(payments_df, invoices):
    """
    Reconcilia pagamentos com faturas
    
    Parâmetros:
    - payments_df: DataFrame contendo dados de pagamento
    - invoices: Lista de dicionários de faturas
    
    Retorna:
    - tuple: (pagamentos_reconciliados, faturas_atualizadas)
    """
    reconciled_payments = []
    
    # Cria uma cópia das faturas para atualizar
    updated_invoices = invoices.copy()
    
    # Processa cada pagamento
    for _, payment in payments_df.iterrows():
        payment_dict = payment.to_dict()
        
        # Encontra correspondências potenciais
        matches = find_potential_matches(payment_dict, updated_invoices)
        
        if matches:
            # Obtém a melhor correspondência
            best_match = matches[0]
            invoice = best_match['invoice']
            
            # Atualiza o pagamento com informações de correspondência
            payment_dict['matched_invoice'] = invoice['invoice_number']
            payment_dict['match_score'] = best_match['score']
            payment_dict['match_reasons'] = best_match['reasons']
            payment_dict['reconciled'] = True
            
            # Atualiza o status de pagamento da fatura
            invoice_idx = next((i for i, inv in enumerate(updated_invoices) if inv['invoice_number'] == invoice['invoice_number']), None)
            if invoice_idx is not None:
                # Inicializa payment_amount se não existir
                if 'payment_amount' not in updated_invoices[invoice_idx]:
                    updated_invoices[invoice_idx]['payment_amount'] = 0
                
                # Adiciona este valor de pagamento
                updated_invoices[invoice_idx]['payment_amount'] += payment_dict['Amount']
                
                # Atualiza a data de pagamento
                updated_invoices[invoice_idx]['payment_date'] = payment_dict['Date']
                
                # Marca como pago se o pagamento estiver completo ou exceder o valor da fatura
                if updated_invoices[invoice_idx]['payment_amount'] >= updated_invoices[invoice_idx]['total_amount']:
                    updated_invoices[invoice_idx]['paid'] = True
                else:
                    updated_invoices[invoice_idx]['paid'] = False
        else:
            # Nenhuma correspondência encontrada
            payment_dict['matched_invoice'] = None
            payment_dict['match_score'] = 0
            payment_dict['match_reasons'] = []
            payment_dict['reconciled'] = False
        
        reconciled_payments.append(payment_dict)
    
    return reconciled_payments, updated_invoices

def manually_reconcile_payment(payment, invoice, amount, invoices):
    """
    Reconcilia manualmente um pagamento com uma fatura
    
    Parâmetros:
    - payment: Dicionário contendo informações de pagamento
    - invoice: Dicionário contendo informações da fatura
    - amount: Valor a ser aplicado à fatura
    - invoices: Lista de todas as faturas
    
    Retorna:
    - tuple: (pagamento_atualizado, faturas_atualizadas)
    """
    # Cria uma cópia das faturas para atualizar
    updated_invoices = invoices.copy()
    
    # Atualiza o pagamento com informações de correspondência
    updated_payment = payment.copy()
    updated_payment['matched_invoice'] = invoice['invoice_number']
    updated_payment['match_score'] = 100  # Correspondência manual é 100% confiante
    updated_payment['match_reasons'] = ["Correspondência manual"]
    updated_payment['reconciled'] = True
    
    # Atualiza o status de pagamento da fatura
    invoice_idx = next((i for i, inv in enumerate(updated_invoices) if inv['invoice_number'] == invoice['invoice_number']), None)
    if invoice_idx is not None:
        # Inicializa payment_amount se não existir
        if 'payment_amount' not in updated_invoices[invoice_idx]:
            updated_invoices[invoice_idx]['payment_amount'] = 0
        
        # Adiciona este valor de pagamento
        updated_invoices[invoice_idx]['payment_amount'] += amount
        
        # Atualiza a data de pagamento
        updated_invoices[invoice_idx]['payment_date'] = payment['Date']
        
        # Marca como pago se o pagamento estiver completo ou exceder o valor da fatura
        if updated_invoices[invoice_idx]['payment_amount'] >= updated_invoices[invoice_idx]['total_amount']:
            updated_invoices[invoice_idx]['paid'] = True
        else:
            updated_invoices[invoice_idx]['paid'] = False
    
    return updated_payment, updated_invoices
