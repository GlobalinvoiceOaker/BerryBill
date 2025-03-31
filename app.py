import streamlit as st
import os
import base64
from datetime import datetime
import pandas as pd

# Inicializa o estado da sessão se ainda não estiver feito
if 'imported_data' not in st.session_state:
    st.session_state.imported_data = None
if 'invoices' not in st.session_state:
    st.session_state.invoices = []
if 'payments' not in st.session_state:
    st.session_state.payments = None
if 'reconciled_invoices' not in st.session_state:
    st.session_state.reconciled_invoices = []

# Título e descrição do aplicativo
st.set_page_config(
    page_title="Sistema de Gerenciamento de Faturas",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo personalizado para corresponder aos requisitos
# Roxo (#4A1F60) como cor primária
# Branco (#FFFFFF) para fundos e texto
# Roxo escuro (#3A174E) para botões
st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        font-weight: bold;
        color: #4A1F60;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3A174E;
        margin-top: 1rem;
    }
    .description {
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Cabeçalho
st.markdown('<div class="main-header">Sistema de Gerenciamento de Faturas</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Simplifique seu fluxo de trabalho de faturas com cálculos automatizados, geração de PDF e reconciliação de pagamentos.</div>', unsafe_allow_html=True)

# Visão geral do painel
st.markdown('<div class="sub-header">Visão Geral do Painel</div>', unsafe_allow_html=True)

# Cria um layout de 3 colunas para as métricas do painel
col1, col2, col3 = st.columns(3)

with col1:
    num_invoices = len(st.session_state.invoices) if hasattr(st.session_state, 'invoices') else 0
    st.metric(label="Total de Faturas", value=num_invoices)

with col2:
    num_sent = sum(1 for inv in st.session_state.invoices if inv.get('sent', False)) if hasattr(st.session_state, 'invoices') else 0
    st.metric(label="Faturas Enviadas", value=num_sent)

with col3:
    num_paid = sum(1 for inv in st.session_state.invoices if inv.get('paid', False)) if hasattr(st.session_state, 'invoices') else 0
    st.metric(label="Faturas Pagas", value=num_paid)

# Atividade recente
st.markdown('<div class="sub-header">Atividade Recente</div>', unsafe_allow_html=True)

if not st.session_state.invoices:
    st.info("Nenhuma atividade recente. Comece importando dados na seção Importar Dados.")
else:
    # Mostra as 5 faturas mais recentes
    recent_invoices = sorted(st.session_state.invoices, key=lambda x: x.get('created_at', datetime.now()), reverse=True)[:5]
    
    activity_df = pd.DataFrame([
        {
            "Fatura #": inv.get('invoice_number', 'N/A'),
            "Cliente": inv.get('partner', 'N/A'),
            "Valor": f"R$ {inv.get('total_amount', 0):,.2f}",
            "Status": "Paga" if inv.get('paid', False) else "Enviada" if inv.get('sent', False) else "Gerada",
            "Data": inv.get('created_at', datetime.now()).strftime('%d/%m/%Y')
        } for inv in recent_invoices
    ])
    
    st.dataframe(activity_df, use_container_width=True)

# Seção de ações rápidas
st.markdown('<div class="sub-header">Ações Rápidas</div>', unsafe_allow_html=True)

# Cria um layout de 3 colunas para botões de ação rápida
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Importar Dados", use_container_width=True):
        st.switch_page("pages/01_Import_Data.py")

with col2:
    if st.button("Gerar Faturas", use_container_width=True):
        st.switch_page("pages/02_Generate_Invoices.py")

with col3:
    if st.button("Ver Relatórios", use_container_width=True):
        st.switch_page("pages/05_Financial_Reports.py")

# Seção de instruções
with st.expander("Como usar este aplicativo"):
    st.markdown("""
    ### Primeiros Passos
    1. **Importar Dados**: Faça upload do seu arquivo Excel com dados de venda dos parceiros.
    2. **Gerar Faturas**: O sistema calculará royalties, fundo de publicidade e impostos automaticamente.
    3. **Enviar Faturas**: Envie as faturas geradas para os contatos registrados.
    4. **Reconciliar Pagamentos**: Faça upload de extratos bancários para combinar pagamentos com faturas.
    5. **Gerar Relatórios**: Crie relatórios financeiros consolidados para análise.
    
    ### Dicas
    - Certifique-se de que seus dados Excel seguem o formato requerido
    - Verifique as configurações do país para garantir cálculos corretos de impostos e royalties
    - Revise as faturas geradas antes de enviar
    - Reconcilie pagamentos regularmente para manter os registros financeiros atualizados
    """)

# Rodapé
st.markdown("---")
st.markdown("© 2023 Sistema de Gerenciamento de Faturas | Desenvolvido com Streamlit")
