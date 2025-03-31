import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from utils.auth import login_required
from utils.access_control import check_access
import os
import json

# Configuração da página
st.set_page_config(
    page_title="Dashboard - Sistema de Gerenciamento de Faturas",
    page_icon="📊",
    layout="wide"
)

# Verificar login
username = login_required()
full_name = st.session_state.full_name
user_role = st.session_state.user_role

# Estilo personalizado
try:
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass

# Função para calcular a inadimplência por mês
def calculate_monthly_delinquency(invoices):
    if not invoices:
        return pd.DataFrame({'Mês': [], 'Valor em Aberto': [], 'Percentual de Inadimplência': []})
    
    # Converter para DataFrame
    df = pd.DataFrame(invoices)
    
    # Garantir que o campo created_at seja datetime
    df['created_at'] = pd.to_datetime(df['created_at'])
    
    # Adicionar coluna de mês/ano
    df['month_year'] = df['created_at'].dt.strftime('%m/%Y')
    
    # Adicionar valor pendente
    df['valor_pendente'] = df['total_amount'] - df.get('payment_amount', 0)
    
    # Agrupar por mês/ano
    monthly = df.groupby('month_year').agg({
        'total_amount': 'sum',
        'payment_amount': 'sum',
        'valor_pendente': 'sum'
    }).reset_index()
    
    # Calcular percentual de inadimplência
    monthly['percentual_inadimplencia'] = (monthly['valor_pendente'] / monthly['total_amount'] * 100).round(2)
    
    # Ordenar por mês/ano
    monthly['month_year_sort'] = pd.to_datetime(monthly['month_year'], format='%m/%Y')
    monthly = monthly.sort_values('month_year_sort')
    
    return monthly[['month_year', 'valor_pendente', 'percentual_inadimplencia']]

# Função para calcular inadimplência por país
def calculate_country_delinquency(invoices, selected_country=None):
    if not invoices:
        return pd.DataFrame({'País': [], 'Valor Total': [], 'Valor Pago': [], 'Valor em Aberto': [], 'Percentual de Inadimplência': []})
    
    # Converter para DataFrame
    df = pd.DataFrame(invoices)
    
    # Filtrar por país se necessário
    if selected_country and selected_country != 'Todos':
        df = df[df['country'] == selected_country]
    
    # Agrupar por país
    country_stats = df.groupby('country').agg({
        'total_amount': 'sum',
        'payment_amount': 'sum'
    }).reset_index()
    
    # Calcular valor em aberto e percentual de inadimplência
    country_stats['valor_em_aberto'] = country_stats['total_amount'] - country_stats['payment_amount']
    country_stats['percentual_inadimplencia'] = (country_stats['valor_em_aberto'] / country_stats['total_amount'] * 100).round(2)
    
    # Renomear colunas
    country_stats.columns = ['País', 'Valor Total', 'Valor Pago', 'Valor em Aberto', 'Percentual de Inadimplência']
    
    return country_stats

# Título da página
st.markdown('<div class="main-header">Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<div class="description">Olá, {full_name}! Bem-vindo ao painel de controle do sistema de gerenciamento de faturas.</div>', unsafe_allow_html=True)

# Verificar se existe alguma fatura
if 'invoices' not in st.session_state or not st.session_state.invoices:
    st.warning("Não há faturas registradas no sistema. Por favor, importe dados e gere faturas.")
    
    if check_access(["admin", "configuracao"]):
        if st.button("Ir para Importar Dados"):
            st.switch_page("pages/01_Importar_Dados.py")
    
    st.stop()

# Se temos faturas, mostrar o dashboard
invoices = st.session_state.invoices

# Filtros
st.markdown('<div class="sub-header">Filtros</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    # Lista de países únicos
    countries = sorted(list(set([inv.get('country', 'N/A') for inv in invoices])))
    selected_country = st.selectbox("País", options=["Todos"] + countries)

with col2:
    # Lista de masters únicos
    masters = sorted(list(set([inv.get('partner', 'N/A') for inv in invoices])))
    selected_master = st.selectbox("Master", options=["Todos"] + masters)

with col3:
    # Filtro de período
    period_options = ["Todos", "Últimos 30 dias", "Últimos 3 meses", "Últimos 6 meses", "Este ano"]
    selected_period = st.selectbox("Período", options=period_options)

# Aplicar filtros
filtered_invoices = invoices

if selected_country != "Todos":
    filtered_invoices = [inv for inv in filtered_invoices if inv.get('country') == selected_country]

if selected_master != "Todos":
    filtered_invoices = [inv for inv in filtered_invoices if inv.get('partner') == selected_master]

if selected_period != "Todos":
    today = datetime.now()
    
    if selected_period == "Últimos 30 dias":
        date_limit = today - timedelta(days=30)
    elif selected_period == "Últimos 3 meses":
        date_limit = today - timedelta(days=90)
    elif selected_period == "Últimos 6 meses":
        date_limit = today - timedelta(days=180)
    elif selected_period == "Este ano":
        date_limit = datetime(today.year, 1, 1)
    
    filtered_invoices = [inv for inv in filtered_invoices if 
                         isinstance(inv.get('created_at'), datetime) and inv.get('created_at') >= date_limit]

# Métricas principais
st.markdown('<div class="sub-header">Métricas Principais</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

# Calcular métricas
total_invoices = len(filtered_invoices)
total_invoiced = sum(inv.get('total_amount', 0) for inv in filtered_invoices)
total_paid = sum(inv.get('payment_amount', 0) for inv in filtered_invoices)
open_amount = total_invoiced - total_paid

if total_invoiced > 0:
    delinquency_rate = (open_amount / total_invoiced) * 100
else:
    delinquency_rate = 0

with col1:
    st.metric("Total de Faturas", f"{total_invoices}")

with col2:
    st.metric("Valor Total", f"$ {total_invoiced:,.2f}")

with col3:
    st.metric("Valor Pago", f"$ {total_paid:,.2f}")

with col4:
    st.metric("Taxa de Inadimplência", f"{delinquency_rate:.2f}%")

# Gráficos e análises
st.markdown('<div class="sub-header">Análise de Inadimplência</div>', unsafe_allow_html=True)

# Duas colunas para os gráficos principais
col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Inadimplência por País")
    
    country_stats = calculate_country_delinquency(filtered_invoices)
    
    if not country_stats.empty:
        # Mostrar tabela
        st.dataframe(country_stats, use_container_width=True)
        
        # Gráfico de barras
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Ordenar por percentual de inadimplência (decrescente)
        sorted_data = country_stats.sort_values('Percentual de Inadimplência', ascending=False)
        
        bars = ax.bar(
            sorted_data['País'], 
            sorted_data['Percentual de Inadimplência'],
            color='#4A1F60'
        )
        
        # Adicionar rótulos nas barras
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2.,
                height + 0.5,
                f'{height:.1f}%',
                ha='center', 
                va='bottom',
                fontsize=10
            )
        
        ax.set_ylabel('Percentual de Inadimplência (%)')
        ax.set_title('Inadimplência por País')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        st.pyplot(fig)
    else:
        st.info("Não há dados suficientes para análise por país.")

with col2:
    st.markdown("#### Evolução Mensal da Inadimplência")
    
    monthly_data = calculate_monthly_delinquency(filtered_invoices)
    
    if not monthly_data.empty:
        # Mostrar tabela
        display_df = monthly_data.copy()
        display_df.columns = ['Mês', 'Valor em Aberto ($)', 'Inadimplência (%)']
        st.dataframe(display_df, use_container_width=True)
        
        # Gráfico de linha
        fig, ax1 = plt.subplots(figsize=(10, 6))
        
        color = '#4A1F60'
        ax1.set_xlabel('Mês')
        ax1.set_ylabel('Percentual de Inadimplência (%)', color=color)
        ax1.plot(monthly_data['month_year'], monthly_data['percentual_inadimplencia'], marker='o', color=color)
        ax1.tick_params(axis='y', labelcolor=color)
        
        # Segundo eixo y para valores absolutos
        ax2 = ax1.twinx()
        color = '#3A174E'
        ax2.set_ylabel('Valor em Aberto ($)', color=color)
        ax2.plot(monthly_data['month_year'], monthly_data['valor_pendente'], marker='s', color=color, linestyle='--')
        ax2.tick_params(axis='y', labelcolor=color)
        
        # Formatação
        plt.title('Evolução da Inadimplência ao Longo do Tempo')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Adicionar valores nos pontos
        for i, (p, v) in enumerate(zip(monthly_data['percentual_inadimplencia'], monthly_data['valor_pendente'])):
            ax1.annotate(f'{p:.1f}%', (i, p), textcoords="offset points", xytext=(0,10), ha='center')
            ax2.annotate(f'${v:,.0f}', (i, v), textcoords="offset points", xytext=(0,-15), ha='center')
        
        st.pyplot(fig)
    else:
        st.info("Não há dados suficientes para análise mensal.")

# Análise detalhada
st.markdown('<div class="sub-header">Análise Detalhada</div>', unsafe_allow_html=True)

# Selecionar visualização por país ou por master
view_option = st.radio("Visualizar por:", options=["País", "Master"])

if view_option == "País" and selected_country == "Todos":
    # Análise por país quando nenhum país específico foi selecionado
    country_analysis = pd.DataFrame([
        {
            "País": inv.get('country', 'N/A'),
            "Fatura #": inv.get('invoice_number', 'N/A'),
            "Master": inv.get('partner', 'N/A'),
            "Valor Total": inv.get('total_amount', 0),
            "Valor Pago": inv.get('payment_amount', 0) if 'payment_amount' in inv else 0,
            "Valor em Aberto": inv.get('total_amount', 0) - (inv.get('payment_amount', 0) if 'payment_amount' in inv else 0),
            "Status": "Paga" if inv.get('paid', False) else "Em aberto",
            "Data de Vencimento": inv.get('due_date').strftime('%d/%m/%Y') if 'due_date' in inv and hasattr(inv['due_date'], 'strftime') else 
                               (inv['installments'][0]['due_date'].strftime('%d/%m/%Y') if 'installments' in inv and inv['installments'] and hasattr(inv['installments'][0]['due_date'], 'strftime') else
                               (inv.get('created_at', datetime.now()) + timedelta(days=30)).strftime('%d/%m/%Y') if hasattr(inv.get('created_at', datetime.now()), 'strftime') else 'N/A')
        } for inv in filtered_invoices
    ])
    
    # Agrupar por país
    country_summary = country_analysis.groupby('País').agg({
        'Valor Total': 'sum',
        'Valor Pago': 'sum',
        'Valor em Aberto': 'sum',
        'Fatura #': 'count'
    }).reset_index()
    
    country_summary['Percentual Pago'] = (country_summary['Valor Pago'] / country_summary['Valor Total'] * 100).round(2)
    country_summary['Percentual em Aberto'] = (100 - country_summary['Percentual Pago']).round(2)
    country_summary = country_summary.rename(columns={'Fatura #': 'Quantidade de Faturas'})
    
    st.markdown("#### Resumo por País")
    st.dataframe(country_summary, use_container_width=True)
    
    # Gráfico de pizza para distribuição de valores em aberto por país
    if len(country_summary) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Ordenar por valor em aberto (decrescente)
        pie_data = country_summary.sort_values('Valor em Aberto', ascending=False)
        
        # Usar cores mais agradáveis
        colors = plt.cm.Purples(np.linspace(0.4, 0.8, len(pie_data)))
        
        wedges, texts, autotexts = ax.pie(
            pie_data['Valor em Aberto'], 
            labels=pie_data['País'],
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Personalizar textos
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
            
        ax.axis('equal')
        plt.title('Distribuição de Valores em Aberto por País')
        plt.tight_layout()
        
        st.pyplot(fig)
    
elif view_option == "Master" and selected_master == "Todos":
    # Análise por master quando nenhum master específico foi selecionado
    master_analysis = pd.DataFrame([
        {
            "Master": inv.get('partner', 'N/A'),
            "Fatura #": inv.get('invoice_number', 'N/A'),
            "País": inv.get('country', 'N/A'),
            "Valor Total": inv.get('total_amount', 0),
            "Valor Pago": inv.get('payment_amount', 0) if 'payment_amount' in inv else 0,
            "Valor em Aberto": inv.get('total_amount', 0) - (inv.get('payment_amount', 0) if 'payment_amount' in inv else 0),
            "Status": "Paga" if inv.get('paid', False) else "Em aberto",
            "Data de Vencimento": inv.get('due_date').strftime('%d/%m/%Y') if 'due_date' in inv and hasattr(inv['due_date'], 'strftime') else 
                               (inv['installments'][0]['due_date'].strftime('%d/%m/%Y') if 'installments' in inv and inv['installments'] and hasattr(inv['installments'][0]['due_date'], 'strftime') else
                               (inv.get('created_at', datetime.now()) + timedelta(days=30)).strftime('%d/%m/%Y') if hasattr(inv.get('created_at', datetime.now()), 'strftime') else 'N/A')
        } for inv in filtered_invoices
    ])
    
    # Agrupar por master
    master_summary = master_analysis.groupby('Master').agg({
        'Valor Total': 'sum',
        'Valor Pago': 'sum',
        'Valor em Aberto': 'sum',
        'Fatura #': 'count'
    }).reset_index()
    
    master_summary['Percentual Pago'] = (master_summary['Valor Pago'] / master_summary['Valor Total'] * 100).round(2)
    master_summary['Percentual em Aberto'] = (100 - master_summary['Percentual Pago']).round(2)
    master_summary = master_summary.rename(columns={'Fatura #': 'Quantidade de Faturas'})
    
    st.markdown("#### Resumo por Master")
    st.dataframe(master_summary, use_container_width=True)
    
    # Gráfico de barras para valores em aberto por master
    if len(master_summary) > 0:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Ordenar por valor em aberto (decrescente)
        bar_data = master_summary.sort_values('Valor em Aberto', ascending=False).head(10)  # Top 10 masters
        
        bars = ax.barh(
            bar_data['Master'], 
            bar_data['Valor em Aberto'],
            color='#4A1F60'
        )
        
        # Adicionar rótulos nas barras
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.5,
                bar.get_y() + bar.get_height()/2.,
                f'${width:,.2f}',
                ha='left', 
                va='center',
                fontsize=10
            )
        
        ax.set_xlabel('Valor em Aberto ($)')
        ax.set_title('Top 10 Masters por Valor em Aberto')
        plt.tight_layout()
        
        st.pyplot(fig)
        
else:
    # Análise detalhada quando um país ou master específico está selecionado
    detail_analysis = pd.DataFrame([
        {
            "Fatura #": inv.get('invoice_number', 'N/A'),
            "Master": inv.get('partner', 'N/A'),
            "País": inv.get('country', 'N/A'),
            "Período": f"{inv.get('month_name', 'N/A')} {inv.get('year', 'N/A')}",
            "Valor Total": inv.get('total_amount', 0),
            "Valor Pago": inv.get('payment_amount', 0) if 'payment_amount' in inv else 0,
            "Valor em Aberto": inv.get('total_amount', 0) - (inv.get('payment_amount', 0) if 'payment_amount' in inv else 0),
            "Status": "Paga" if inv.get('paid', False) else "Em aberto",
            "Data de Vencimento": inv.get('due_date').strftime('%d/%m/%Y') if 'due_date' in inv and hasattr(inv['due_date'], 'strftime') else 
                               (inv['installments'][0]['due_date'].strftime('%d/%m/%Y') if 'installments' in inv and inv['installments'] and hasattr(inv['installments'][0]['due_date'], 'strftime') else
                               (inv.get('created_at', datetime.now()) + timedelta(days=30)).strftime('%d/%m/%Y') if hasattr(inv.get('created_at', datetime.now()), 'strftime') else 'N/A')
        } for inv in filtered_invoices
    ])
    
    title = f"Detalhes para {selected_country}" if view_option == "País" and selected_country != "Todos" else f"Detalhes para {selected_master}"
    st.markdown(f"#### {title}")
    
    # Destacar status com cores
    def highlight_status(val):
        if val == "Paga":
            return 'background-color: #d4edda; color: #155724'
        elif val == "Em aberto":
            return 'background-color: #f8d7da; color: #721c24'
        return ''
    
    # Aplicar estilo
    styled_df = detail_analysis.style.applymap(highlight_status, subset=['Status'])
    
    st.dataframe(styled_df, use_container_width=True)

# Resumo de Faturas por Status
st.markdown('<div class="sub-header">Resumo de Faturas por Status</div>', unsafe_allow_html=True)

# Função para obter a data de vencimento de uma fatura
def get_due_date(inv):
    if 'due_date' in inv and inv['due_date']:
        return inv['due_date']
    elif 'installments' in inv and inv['installments'] and len(inv['installments']) > 0:
        return inv['installments'][0]['due_date']
    else:
        # Fallback para o cálculo padrão antigo
        return inv.get('created_at', datetime.now()) + timedelta(days=30)

# Contar faturas por status
status_counts = {
    "Paga": len([inv for inv in filtered_invoices if inv.get('paid', False)]),
    "Vencida": len([inv for inv in filtered_invoices if not inv.get('paid', False) and 
                   get_due_date(inv) < datetime.now()]),
    "A Vencer": len([inv for inv in filtered_invoices if not inv.get('paid', False) and 
                    get_due_date(inv) >= datetime.now()])
}

# Mostrar contagem e proporção
col1, col2 = st.columns(2)

with col1:
    # Tabela de contagem
    status_df = pd.DataFrame([
        {"Status": status, "Quantidade": count, "Percentual": f"{count/total_invoices*100:.1f}%" if total_invoices > 0 else "0%"}
        for status, count in status_counts.items()
    ])
    
    st.dataframe(status_df, use_container_width=True)

with col2:
    # Gráfico de pizza
    fig, ax = plt.subplots(figsize=(8, 6))
    
    statuses = list(status_counts.keys())
    counts = list(status_counts.values())
    
    # Verificar se há dados para plotar
    if sum(counts) > 0:
        # Definir cores para cada status
        colors = ['#4daf4a', '#e41a1c', '#377eb8']  # Verde para Paga, Vermelho para Vencida, Azul para A Vencer
        
        wedges, texts, autotexts = ax.pie(
            counts, 
            labels=statuses,
            autopct='%1.1f%%',
            startangle=90,
            colors=colors
        )
        
        # Personalizar textos
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_fontweight('bold')
            
        ax.axis('equal')
        plt.title('Distribuição de Faturas por Status')
        
        st.pyplot(fig)
    else:
        st.info("Não há dados para exibir no gráfico.")

# Navegação para outras páginas
st.markdown("---")
st.markdown("#### Ações")

col1, col2, col3 = st.columns(3)

with col1:
    if check_access(["admin", "gestor"]):
        if st.button("Ver Controle de Invoices", use_container_width=True):
            st.switch_page("pages/07_Controle_Invoices.py")

with col2:
    if check_access(["admin"]):
        if st.button("Gerar Novas Faturas", use_container_width=True):
            st.switch_page("pages/02_Gerar_Faturas.py")

with col3:
    if check_access(["admin", "configuracao"]):
        if st.button("Configurações", use_container_width=True):
            st.switch_page("pages/06_Configuracoes.py")