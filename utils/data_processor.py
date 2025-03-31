import pandas as pd
import json
import os
import streamlit as st
from datetime import datetime

# Arquivo para armazenar configurações do país
COUNTRY_SETTINGS_FILE = "data/country_settings.json"

def ensure_data_dir():
    """
    Garante que o diretório de dados existe
    """
    if not os.path.exists("data"):
        os.makedirs("data")

def load_country_settings():
    """
    Carrega as configurações dos países do arquivo JSON
    """
    ensure_data_dir()
    
    if not os.path.exists(COUNTRY_SETTINGS_FILE):
        # Configurações padrão
        default_settings = {
            "Brazil": {
                "royalty_rate": 8.0,
                "ad_fund_rate": 2.0,
                "tax_rate": 15.0,
                "currency": "BRL",
                "exchange_rate": 5.0,
                "stores": {
                    "default": {
                        "royalty_rate": 8.0,
                        "ad_fund_rate": 2.0
                    }
                }
            },
            "USA": {
                "royalty_rate": 6.0,
                "ad_fund_rate": 1.5,
                "tax_rate": 0.0,
                "currency": "USD",
                "exchange_rate": 1.0,
                "stores": {
                    "default": {
                        "royalty_rate": 6.0,
                        "ad_fund_rate": 1.5
                    }
                }
            },
            "Mexico": {
                "royalty_rate": 7.0,
                "ad_fund_rate": 2.0,
                "tax_rate": 16.0,
                "currency": "MXN",
                "exchange_rate": 17.5,
                "stores": {
                    "default": {
                        "royalty_rate": 7.0,
                        "ad_fund_rate": 2.0
                    }
                }
            }
        }
        
        with open(COUNTRY_SETTINGS_FILE, 'w') as f:
            json.dump(default_settings, f, indent=4)
        
        return default_settings
    
    try:
        with open(COUNTRY_SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        # Em caso de erro no arquivo, retornar configurações padrão
        return {}

def save_country_settings(settings):
    """
    Salva as configurações dos países no arquivo JSON
    """
    ensure_data_dir()
    
    with open(COUNTRY_SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def validate_data(df):
    """
    Valida os dados importados
    
    Retorna:
    - (bool, str): (é_válido, mensagem_de_erro)
    """
    # Verificar colunas obrigatórias
    required_columns = ['Date', 'Country', 'Partner', 'Store', 'Sales']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}"
    
    # Verificar tipos de dados
    try:
        # Converter coluna de data
        df['Date'] = pd.to_datetime(df['Date'])
    except:
        return False, "Formato de data inválido. Utilize o formato YYYY-MM-DD."
    
    # Verificar valores numéricos para vendas
    if not pd.to_numeric(df['Sales'], errors='coerce').notnull().all():
        return False, "Valores de vendas inválidos. Utilize apenas valores numéricos."
    
    # Validar países
    country_settings = load_country_settings()
    unknown_countries = set(df['Country']) - set(country_settings.keys())
    
    if unknown_countries:
        return False, f"Países desconhecidos no arquivo: {', '.join(unknown_countries)}. Configure-os primeiro na seção Configurações."
    
    return True, "Dados válidos."

def process_data(df):
    """
    Processa os dados importados e calcula royalties, fundo de publicidade e impostos
    
    Retorna:
    - DataFrame com colunas calculadas adicionais
    """
    # Carregar configurações dos países
    country_settings = load_country_settings()
    
    # Criar cópia do DataFrame para evitar modificar o original
    processed_df = df.copy()
    
    # Converter colunas
    processed_df['Date'] = pd.to_datetime(processed_df['Date'])
    processed_df['Sales'] = pd.to_numeric(processed_df['Sales'])
    
    # Adicionar colunas de mês e ano
    processed_df['Month'] = processed_df['Date'].dt.month
    processed_df['Year'] = processed_df['Date'].dt.year
    processed_df['Month_Name'] = processed_df['Date'].dt.strftime('%B')
    
    # Inicializar colunas de cálculos
    processed_df['Royalty_Rate'] = 0.0
    processed_df['Ad_Fund_Rate'] = 0.0
    processed_df['Tax_Rate'] = 0.0
    processed_df['Currency'] = ''
    processed_df['Exchange_Rate'] = 0.0
    processed_df['Royalty_Amount'] = 0.0
    processed_df['Ad_Fund_Amount'] = 0.0
    processed_df['Tax_Amount'] = 0.0
    processed_df['Total_Amount'] = 0.0
    processed_df['Amount_USD'] = 0.0
    
    # Processar cada linha com base no país e, se disponível, na loja específica
    for idx, row in processed_df.iterrows():
        country = row['Country']
        store = row['Store']
        
        if country in country_settings:
            country_config = country_settings[country]
            
            # Verificar se a loja específica tem configurações personalizadas
            if 'stores' in country_config and store in country_config['stores']:
                store_config = country_config['stores'][store]
                royalty_rate = store_config.get('royalty_rate', country_config['royalty_rate'])
                ad_fund_rate = store_config.get('ad_fund_rate', country_config['ad_fund_rate'])
            else:
                # Usar configuração padrão da loja se disponível, caso contrário usa a do país
                if 'stores' in country_config and 'default' in country_config['stores']:
                    default_store = country_config['stores']['default']
                    royalty_rate = default_store.get('royalty_rate', country_config['royalty_rate'])
                    ad_fund_rate = default_store.get('ad_fund_rate', country_config['ad_fund_rate'])
                else:
                    royalty_rate = country_config['royalty_rate']
                    ad_fund_rate = country_config['ad_fund_rate']
            
            # Preencher dados do país
            processed_df.at[idx, 'Royalty_Rate'] = royalty_rate
            processed_df.at[idx, 'Ad_Fund_Rate'] = ad_fund_rate
            processed_df.at[idx, 'Tax_Rate'] = country_config['tax_rate']
            processed_df.at[idx, 'Currency'] = country_config['currency']
            processed_df.at[idx, 'Exchange_Rate'] = country_config['exchange_rate']
            
            # Calcular valores
            sales = row['Sales']
            royalty_amount = sales * (royalty_rate / 100)
            ad_fund_amount = sales * (ad_fund_rate / 100)
            subtotal = royalty_amount + ad_fund_amount
            tax_amount = subtotal * (country_config['tax_rate'] / 100)
            total_amount = subtotal + tax_amount
            amount_usd = total_amount / country_config['exchange_rate']
            
            # Preencher resultados dos cálculos
            processed_df.at[idx, 'Royalty_Amount'] = royalty_amount
            processed_df.at[idx, 'Ad_Fund_Amount'] = ad_fund_amount
            processed_df.at[idx, 'Tax_Amount'] = tax_amount
            processed_df.at[idx, 'Total_Amount'] = total_amount
            processed_df.at[idx, 'Amount_USD'] = amount_usd
    
    return processed_df

def group_data_by_partner(df):
    """
    Agrupa dados por parceiro e mês para geração de faturas
    
    Retorna:
    - Lista de dicionários com dados agrupados
    """
    # Garantir que as colunas necessárias existam
    if not all(col in df.columns for col in ['Partner', 'Country', 'Month', 'Year', 'Month_Name', 'Total_Amount', 'Amount_USD', 'Currency']):
        return []
    
    # Agrupar por parceiro, país, mês e ano
    grouped = df.groupby(['Partner', 'Country', 'Month', 'Year', 'Month_Name'])
    
    invoices_data = []
    
    for (partner, country, month, year, month_name), group in grouped:
        # Somar valores
        total_sales = group['Sales'].sum()
        total_royalty = group['Royalty_Amount'].sum()
        total_ad_fund = group['Ad_Fund_Amount'].sum()
        total_tax = group['Tax_Amount'].sum()
        total_amount = group['Total_Amount'].sum()
        amount_usd = group['Amount_USD'].sum()
        currency = group['Currency'].iloc[0]  # Assume que a moeda é a mesma para o grupo
        
        # Média das taxas (para mostrar na fatura)
        avg_royalty_rate = group['Royalty_Rate'].mean()
        avg_ad_fund_rate = group['Ad_Fund_Rate'].mean()
        tax_rate = group['Tax_Rate'].iloc[0]  # Assume que a taxa de imposto é a mesma
        
        # Criar dados para fatura
        invoice_data = {
            'partner': partner,
            'country': country,
            'month': month,
            'year': year,
            'month_name': month_name,
            'total_sales': total_sales,
            'royalty_rate': avg_royalty_rate,
            'royalty_amount': total_royalty,
            'ad_fund_rate': avg_ad_fund_rate,
            'ad_fund_amount': total_ad_fund,
            'tax_rate': tax_rate,
            'tax_amount': total_tax,
            'total_amount': total_amount,
            'amount_usd': amount_usd,
            'currency': currency,
            'invoice_number': f"INV-{country[:3]}-{partner[:3]}-{year}{month:02d}",
            'created_at': datetime.now(),
            'sent': False,
            'paid': False,
            'payment_amount': 0,
            'due_status': 'A Vencer'  # Status inicial
        }
        
        invoices_data.append(invoice_data)
    
    return invoices_data

def import_payment_data(file):
    """
    Importa e valida dados de pagamento de arquivos CSV ou Excel
    
    Retorna:
    - (DataFrame, bool, str): (dados, é_válido, mensagem_de_erro)
    """
    try:
        # Detectar tipo de arquivo
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension == '.csv':
            df = pd.read_csv(file)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file)
        else:
            return None, False, "Formato de arquivo não suportado. Utilize CSV ou Excel."
        
        # Verificar colunas mínimas necessárias
        required_columns = ['Date', 'Amount', 'Description']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return df, False, f"Colunas obrigatórias ausentes: {', '.join(missing_columns)}"
        
        # Tentar converter data
        try:
            df['Date'] = pd.to_datetime(df['Date'])
        except:
            return df, False, "Formato de data inválido. Utilize o formato YYYY-MM-DD."
        
        # Validar valores numéricos para montante
        if not pd.to_numeric(df['Amount'], errors='coerce').notnull().all():
            return df, False, "Valores de pagamento inválidos. Utilize apenas valores numéricos."
        
        # Converter Amount para numérico
        df['Amount'] = pd.to_numeric(df['Amount'])
        
        return df, True, "Dados de pagamento válidos."
        
    except Exception as e:
        return None, False, f"Erro ao importar arquivo: {str(e)}"