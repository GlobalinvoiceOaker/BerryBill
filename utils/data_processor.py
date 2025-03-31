import pandas as pd
import json
import os
import streamlit as st
from datetime import datetime

def load_country_settings():
    """
    Carrega as configurações dos países do arquivo JSON
    """
    try:
        with open('data/country_settings.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Retorna configurações padrão se o arquivo não existir
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
    Salva as configurações dos países no arquivo JSON
    """
    # Cria o diretório de dados se não existir
    os.makedirs('data', exist_ok=True)
    
    with open('data/country_settings.json', 'w') as f:
        json.dump(settings, f, indent=4)

def validate_data(df):
    """
    Valida os dados importados
    
    Retorna:
    - (bool, str): (é_válido, mensagem_de_erro)
    """
    required_columns = ['Date', 'Partner', 'Country', 'Amount', 'Currency']
    
    # Verifica se as colunas obrigatórias existem
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        return False, f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}"
    
    # Verifica valores ausentes em campos obrigatórios
    for col in required_columns:
        if df[col].isnull().any():
            return False, f"Valores ausentes na coluna '{col}'"
    
    # Verifica se as datas são válidas
    try:
        pd.to_datetime(df['Date'])
    except:
        return False, "Formato de data inválido na coluna 'Date'"
    
    # Verifica se os valores são numéricos
    try:
        pd.to_numeric(df['Amount'])
    except:
        return False, "Valores numéricos inválidos na coluna 'Amount'"
    
    # Verifica se os países são suportados
    country_settings = load_country_settings()
    unsupported_countries = df[~df['Country'].isin(country_settings.keys())]['Country'].unique()
    if len(unsupported_countries) > 0:
        return False, f"Países não suportados encontrados: {', '.join(unsupported_countries)}"
    
    return True, ""

def process_data(df):
    """
    Processa os dados importados e calcula royalties, fundo de publicidade e impostos
    
    Retorna:
    - DataFrame com colunas calculadas adicionais
    """
    # Carrega configurações dos países
    country_settings = load_country_settings()
    
    # Converte coluna de data para datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Garante que Amount é numérico
    df['Amount'] = pd.to_numeric(df['Amount'])
    
    # Cria novas colunas para cálculos
    df['Royalty Rate'] = df['Country'].map({country: data['royalty_rate'] for country, data in country_settings.items()})
    df['Ad Fund Rate'] = df['Country'].map({country: data['ad_fund_rate'] for country, data in country_settings.items()})
    df['Tax Rate'] = df['Country'].map({country: data['tax_rate'] for country, data in country_settings.items()})
    
    # Calcula valores
    df['Royalty Amount'] = df['Amount'] * df['Royalty Rate']
    df['Ad Fund Amount'] = df['Amount'] * df['Ad Fund Rate']
    df['Subtotal'] = df['Royalty Amount'] + df['Ad Fund Amount']
    df['Tax Amount'] = df['Subtotal'] * df['Tax Rate']
    df['Total Amount'] = df['Subtotal'] + df['Tax Amount']
    
    # Formata valores para 2 casas decimais
    for col in ['Royalty Amount', 'Ad Fund Amount', 'Subtotal', 'Tax Amount', 'Total Amount']:
        df[col] = df[col].round(2)
    
    # Adiciona colunas de ano e mês para agrupamento mais fácil
    df['Year'] = df['Date'].dt.year
    df['Month'] = df['Date'].dt.month
    df['Month Name'] = df['Date'].dt.strftime('%B')
    
    # Adiciona coluna de status de geração de fatura
    df['Invoice Generated'] = False
    
    return df

def group_data_by_partner(df):
    """
    Agrupa dados por parceiro e mês para geração de faturas
    
    Retorna:
    - Lista de dicionários com dados agrupados
    """
    grouped_data = []
    
    # Agrupa por parceiro, país, ano e mês
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
    Importa e valida dados de pagamento de arquivos CSV ou Excel
    
    Retorna:
    - (DataFrame, bool, str): (dados, é_válido, mensagem_de_erro)
    """
    try:
        # Determina o tipo de arquivo com base na extensão
        if file.name.endswith('.csv'):
            df = pd.read_csv(file)
        elif file.name.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(file)
        else:
            return None, False, "Formato de arquivo não suportado. Por favor, faça upload de um arquivo CSV ou Excel."
        
        # Valida colunas obrigatórias
        required_columns = ['Date', 'Amount', 'Description', 'Reference']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return None, False, f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}"
        
        # Converte coluna de data para datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Garante que Amount é numérico
        df['Amount'] = pd.to_numeric(df['Amount'])
        
        return df, True, ""
    
    except Exception as e:
        return None, False, f"Erro ao importar dados de pagamento: {str(e)}"
