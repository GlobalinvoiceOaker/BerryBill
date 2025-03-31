import streamlit as st
import pandas as pd
from datetime import datetime
from utils.invoice_generator import generate_invoices_from_data, get_invoice_download_link

st.set_page_config(
    page_title="Gerar Faturas - Sistema de Gerenciamento de Faturas",
    page_icon="📄",
    layout="wide"
)

# Estilo personalizado
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
st.markdown('<div class="main-header">Gerar Faturas</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Crie faturas com base em dados processados e cálculos</div>', unsafe_allow_html=True)

# Verifica se os dados foram importados
if 'imported_data' not in st.session_state or st.session_state.imported_data is None:
    st.warning("Nenhum dado importado. Por favor, importe dados primeiro.")
    if st.button("Ir para Importar Dados"):
        st.switch_page("pages/01_Importar_Dados.py")
else:
    # Exibe resumo dos dados
    processed_data = st.session_state.imported_data
    
    # Métricas de resumo
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total de Parceiros", processed_data['Partner'].nunique())
    
    with col2:
        st.metric("Total de Países", processed_data['Country'].nunique())
    
    with col3:
        st.metric("Total de Vendas", f"R$ {processed_data['Amount'].sum():,.2f}")
    
    with col4:
        st.metric("Valor Total das Faturas", f"R$ {processed_data['Total Amount'].sum():,.2f}")
    
    # Seção de geração de faturas
    st.markdown('<div class="sub-header">Gerar Faturas</div>', unsafe_allow_html=True)
    
    # Opções de filtro
    col1, col2 = st.columns(2)
    
    with col1:
        selected_partners = st.multiselect(
            "Selecionar Parceiros",
            options=processed_data['Partner'].unique(),
            default=list(processed_data['Partner'].unique())
        )
    
    with col2:
        selected_countries = st.multiselect(
            "Selecionar Países",
            options=processed_data['Country'].unique(),
            default=list(processed_data['Country'].unique())
        )
    
    # Filtrar dados
    filtered_data = processed_data[
        processed_data['Partner'].isin(selected_partners) &
        processed_data['Country'].isin(selected_countries)
    ]
    
    # Exibir dados filtrados
    st.markdown("#### Visualização dos Dados Filtrados")
    st.dataframe(filtered_data.head(10), use_container_width=True)
    
    # Botão de geração de faturas
    if st.button("Gerar Faturas"):
        with st.spinner("Gerando faturas..."):
            # Gerar faturas
            invoices = generate_invoices_from_data(filtered_data)
            
            # Armazenar no estado da sessão (adicionar às faturas existentes, se houver)
            if 'invoices' not in st.session_state:
                st.session_state.invoices = []
            
            # Verificar duplicatas e adicionar apenas novas faturas
            existing_invoice_numbers = [inv['invoice_number'] for inv in st.session_state.invoices]
            new_invoices = [inv for inv in invoices if inv['invoice_number'] not in existing_invoice_numbers]
            
            st.session_state.invoices.extend(new_invoices)
            
            st.success(f"{len(new_invoices)} faturas geradas com sucesso!")
    
    # Exibir faturas geradas
    if 'invoices' in st.session_state and st.session_state.invoices:
        st.markdown('<div class="sub-header">Faturas Geradas</div>', unsafe_allow_html=True)
        
        # Converter para DataFrame para exibição mais fácil
        invoices_df = pd.DataFrame([
            {
                "Fatura #": inv['invoice_number'],
                "Parceiro": inv['partner'],
                "País": inv['country'],
                "Período": f"{inv['month_name']} {inv['year']}",
                "Valor Total": f"{inv['currency']} {inv['total_amount']:,.2f}",
                "Data de Geração": inv['created_at'].strftime("%d/%m/%Y") if hasattr(inv['created_at'], 'strftime') else inv['created_at'],
                "Status": "Enviada" if inv.get('sent', False) else "Gerada"
            } for inv in st.session_state.invoices
        ])
        
        st.dataframe(invoices_df, use_container_width=True)
        
        # Detalhes da fatura e download
        selected_invoice_idx = st.selectbox(
            "Selecione uma fatura para ver detalhes",
            options=range(len(st.session_state.invoices)),
            format_func=lambda i: f"{st.session_state.invoices[i]['invoice_number']} - {st.session_state.invoices[i]['partner']} ({st.session_state.invoices[i]['month_name']} {st.session_state.invoices[i]['year']})"
        )
        
        if selected_invoice_idx is not None:
            selected_invoice = st.session_state.invoices[selected_invoice_idx]
            
            # Exibir detalhes da fatura
            with st.expander("Detalhes da Fatura", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**Número da Fatura:** {selected_invoice['invoice_number']}")
                    st.markdown(f"**Parceiro:** {selected_invoice['partner']}")
                    st.markdown(f"**País:** {selected_invoice['country']}")
                    st.markdown(f"**Período:** {selected_invoice['month_name']} {selected_invoice['year']}")
                
                with col2:
                    st.markdown(f"**Total de Vendas:** {selected_invoice['currency']} {selected_invoice['total_sell_out']:,.2f}")
                    st.markdown(f"**Valor de Royalties:** {selected_invoice['currency']} {selected_invoice['royalty_amount']:,.2f}")
                    st.markdown(f"**Valor do Fundo de Publicidade:** {selected_invoice['currency']} {selected_invoice['ad_fund_amount']:,.2f}")
                    st.markdown(f"**Valor de Impostos:** {selected_invoice['currency']} {selected_invoice['tax_amount']:,.2f}")
                    st.markdown(f"**Valor Total:** {selected_invoice['currency']} {selected_invoice['total_amount']:,.2f}")
                
                # Link de download
                st.markdown(get_invoice_download_link(selected_invoice, "Baixar PDF"), unsafe_allow_html=True)
        
        # Próximos passos
        st.markdown("#### Próximos Passos")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Enviar Faturas"):
                st.switch_page("pages/03_Enviar_Faturas.py")
        
        with col2:
            if st.button("Reconciliar Pagamentos"):
                st.switch_page("pages/04_Reconciliar_Pagamentos.py")
