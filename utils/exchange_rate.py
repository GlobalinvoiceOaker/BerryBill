import pandas as pd
import requests
from datetime import datetime, timedelta
import streamlit as st

def get_bc_exchange_rate(date=None):
    """
    Obtém a taxa de câmbio (BRL/USD) do Banco Central para uma data específica
    
    Parâmetros:
    - date: Data para consulta (datetime ou string no formato 'YYYY-MM-DD'). Se None, usa a data atual.
    
    Retorna:
    - float: Taxa de câmbio do dia ou None se não disponível
    """
    try:
        # Se a data não for fornecida, usa a data atual
        if date is None:
            date = datetime.now()
        elif isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')
        
        # Formatar data para o formato esperado pela API
        date_str = date.strftime('%m-%d-%Y')
        
        # URL da API do Banco Central
        url = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{date_str}'&$format=json"
        
        # Fazer a requisição
        response = requests.get(url)
        data = response.json()
        
        # Verificar se há valores
        if 'value' in data and len(data['value']) > 0:
            # Retorna a cotação de fechamento (venda)
            return float(data['value'][0]['cotacaoVenda'])
        else:
            # Se não há cotação para a data fornecida, tenta o dia anterior (até 5 dias)
            for i in range(1, 6):
                prev_date = date - timedelta(days=i)
                prev_date_str = prev_date.strftime('%m-%d-%Y')
                url = f"https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/CotacaoDolarDia(dataCotacao=@dataCotacao)?@dataCotacao='{prev_date_str}'&$format=json"
                response = requests.get(url)
                data = response.json()
                
                if 'value' in data and len(data['value']) > 0:
                    return float(data['value'][0]['cotacaoVenda'])
            
            # Se não encontrar em nenhum dos dias anteriores
            return None
    
    except Exception as e:
        st.error(f"Erro ao obter taxa de câmbio: {str(e)}")
        return None

def get_exchange_rates_for_countries(date=None):
    """
    Obtém taxas de câmbio para diferentes moedas em relação ao dólar
    
    Parâmetros:
    - date: Data para consulta (opcional)
    
    Retorna:
    - dict: Mapeamento de códigos de moeda para taxas de câmbio
    """
    # Obter taxa BRL/USD
    usd_brl = get_bc_exchange_rate(date)
    
    # Para simplificar, usamos valores fixos para outras moedas ou APIs adicionais se necessário
    # Estes valores seriam idealmente obtidos de uma API como a do Banco Central
    rates = {
        'BRL': usd_brl or 5.20,  # Valor padrão caso falhe a API
        'EUR': 0.93,             # Exemplo: 1 USD = 0.93 EUR
        'USD': 1.0,              # Base
        'GBP': 0.79,             # Exemplo: 1 USD = 0.79 GBP
        'MXN': 16.5,             # Exemplo: 1 USD = 16.5 MXN
        'COP': 3900.0,           # Exemplo: 1 USD = 3900 COP
        'ARS': 350.0,            # Exemplo: 1 USD = 350 ARS
        'CLP': 870.0             # Exemplo: 1 USD = 870 CLP
    }
    
    return rates