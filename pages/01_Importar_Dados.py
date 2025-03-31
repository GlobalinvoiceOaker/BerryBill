import streamlit as st
import pandas as pd
import os
from datetime import datetime
from utils.data_processor import validate_data, process_data
from utils.auth import login_required
from assets.logo_header import render_logo, render_icon

st.set_page_config(
    page_title="Importar Dados - Sistema de Gerenciamento de Faturas",
    page_icon="📊",
    layout="wide"
)

# Verifica login
username = login_required()

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

# Cabeçalho com logo
col1, col2 = st.columns([1, 3])

with col1:
    render_logo(width=200)
    
with col2:
    st.markdown('<div class="main-header">Importar Dados</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">Faça upload ou insira manualmente dados de venda dos parceiros (Masters)</div>', unsafe_allow_html=True)

# Tabs para os diferentes métodos de importação
tab1, tab2 = st.tabs(["Upload de Arquivo", "Inserção Manual"])

with tab1:
    # Upload de arquivo
    uploaded_file = st.file_uploader("Faça upload do arquivo Excel com dados de venda", type=["xlsx", "xls"])

with tab2:
    # Formulário para entrada manual de dados
    st.write("Insira manualmente os dados de venda:")
    
    with st.form(key="manual_data_form"):
        # Data da transação
        transaction_date = st.date_input("Data da Transação", value=datetime.now())
        
        # Nome do parceiro
        partner_name = st.text_input("Nome do Parceiro/Master")
        
        # País
        from utils.data_processor import load_country_settings
        country_settings = load_country_settings()
        countries = list(country_settings.keys())
        country_code = st.selectbox("País", options=countries)
        
        # Valor
        amount = st.number_input("Valor de Venda", min_value=0.01, format="%f")
        
        # Moeda
        currency = st.selectbox("Moeda", options=["BRL", "USD", "EUR", "GBP"])
        
        # Botão de submissão
        submit_button = st.form_submit_button(label="Adicionar Registro")
    
    # Processamento do formulário
    if submit_button:
        # Criar um DataFrame com o registro único
        manual_data = pd.DataFrame({
            "Date": [transaction_date],
            "Partner": [partner_name],
            "Country": [country_code],
            "Amount": [amount],
            "Currency": [currency]
        })
        
        # Inicializa lista de registros manuais se não existir
        if 'manual_records' not in st.session_state:
            st.session_state.manual_records = pd.DataFrame(columns=["Date", "Partner", "Country", "Amount", "Currency"])
        
        # Adiciona o novo registro
        st.session_state.manual_records = pd.concat([st.session_state.manual_records, manual_data], ignore_index=True)
        
        st.success(f"Registro adicionado: {partner_name} - {amount} {currency}")
    
    # Exibe registros atuais
    if 'manual_records' in st.session_state and not st.session_state.manual_records.empty:
        st.write("Registros inseridos manualmente:")
        st.dataframe(st.session_state.manual_records, use_container_width=True)
        
        # Botão para processar os dados manuais
        if st.button("Processar Dados Manuais"):
            with st.spinner("Processando dados..."):
                df = st.session_state.manual_records
                processed_data = process_data(df)
                
                # Armazena no estado da sessão
                st.session_state.imported_data = processed_data
                
                # Exibe os dados processados
                st.markdown('<div class="sub-header">Dados Processados</div>', unsafe_allow_html=True)
                st.dataframe(processed_data, use_container_width=True)
                
                # Mostra o resumo
                st.markdown('<div class="sub-header">Resumo dos Dados</div>', unsafe_allow_html=True)
                
                # Cria métricas de resumo
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Registros", len(processed_data))
                
                with col2:
                    st.metric("Valor Total", f"R$ {processed_data['Amount'].sum():,.2f}")
                
                with col3:
                    st.metric("Total de Parceiros", processed_data['Partner'].nunique())
                
                with col4:
                    st.metric("Total de Países", processed_data['Country'].nunique())
                
                # Próximos passos
                st.success("Processamento de dados concluído! Agora você pode prosseguir para gerar faturas.")
                if st.button("Ir para Gerar Faturas"):
                    st.switch_page("pages/02_Gerar_Faturas.py")

# Verificação e processamento apenas para o caso do upload de arquivo
if uploaded_file is not None:
    try:
        # Lê o arquivo Excel
        df = pd.read_excel(uploaded_file)
        
        # Mostra os dados brutos
        st.markdown('<div class="sub-header">Visualização dos Dados Brutos</div>', unsafe_allow_html=True)
        st.dataframe(df.head(10), use_container_width=True)
        
        # Valida os dados
        is_valid, error_message = validate_data(df)
        
        if is_valid:
            st.success("Validação de dados bem-sucedida! O arquivo enviado possui todas as colunas necessárias.")
            
            # Processa os dados
            if st.button("Processar Dados"):
                with st.spinner("Processando dados..."):
                    processed_data = process_data(df)
                    
                    # Armazena no estado da sessão
                    st.session_state.imported_data = processed_data
                    
                    # Exibe os dados processados
                    st.markdown('<div class="sub-header">Dados Processados</div>', unsafe_allow_html=True)
                    st.dataframe(processed_data, use_container_width=True)
                    
                    # Mostra o resumo
                    st.markdown('<div class="sub-header">Resumo dos Dados</div>', unsafe_allow_html=True)
                    
                    # Cria métricas de resumo
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total de Registros", len(processed_data))
                    
                    with col2:
                        st.metric("Valor Total", f"R$ {processed_data['Amount'].sum():,.2f}")
                    
                    with col3:
                        st.metric("Total de Parceiros", processed_data['Partner'].nunique())
                    
                    with col4:
                        st.metric("Total de Países", processed_data['Country'].nunique())
                    
                    # Mostra resumo detalhado
                    with st.expander("Ver Resumo Detalhado"):
                        # Por parceiro
                        st.markdown("#### Por Parceiro")
                        partner_summary = processed_data.groupby('Partner').agg({
                            'Amount': 'sum',
                            'Royalty Amount': 'sum',
                            'Ad Fund Amount': 'sum',
                            'Tax Amount': 'sum',
                            'Total Amount': 'sum'
                        }).reset_index()
                        st.dataframe(partner_summary, use_container_width=True)
                        
                        # Por país
                        st.markdown("#### Por País")
                        country_summary = processed_data.groupby('Country').agg({
                            'Amount': 'sum',
                            'Royalty Amount': 'sum',
                            'Ad Fund Amount': 'sum',
                            'Tax Amount': 'sum',
                            'Total Amount': 'sum'
                        }).reset_index()
                        st.dataframe(country_summary, use_container_width=True)
                    
                    # Próximos passos
                    st.success("Processamento de dados concluído! Agora você pode prosseguir para gerar faturas.")
                    if st.button("Ir para Gerar Faturas"):
                        st.switch_page("pages/02_Gerar_Faturas.py")
        else:
            st.error(f"Falha na validação de dados: {error_message}")
            
            # Mostra o formato necessário
            with st.expander("Ver Formato de Dados Necessário"):
                st.markdown("""
                O arquivo Excel enviado deve conter as seguintes colunas:
                
                - **Date**: Data da transação (formato necessário: AAAA-MM-DD)
                - **Partner**: Nome do parceiro/master
                - **Country**: Código do país (deve ser um dos países suportados)
                - **Amount**: Valor numérico representando o valor de venda
                - **Currency**: Código da moeda (ex: USD, EUR, BRL)
                
                Exemplo:
                
                | Date       | Partner      | Country | Amount  | Currency |
                |------------|--------------|---------|---------|----------|
                | 2023-10-01 | Nome Parceiro| BR      | 10000.0 | BRL      |
                | 2023-10-02 | Outra Empresa| US      | 8500.5  | USD      |
                
                Certifique-se de que todas as colunas necessárias estejam presentes e os dados estejam no formato correto.
                """)
    
    except Exception as e:
        st.error(f"Erro ao ler o arquivo: {str(e)}")
        st.info("Por favor, certifique-se de que está enviando um arquivo Excel válido (.xlsx ou .xls)")
else:
    # Exibe o formato de amostra de dados
    st.info("Por favor, faça upload de um arquivo Excel com dados de venda para prosseguir.")
    
    with st.expander("Ver Formato de Dados Necessário"):
        st.markdown("""
        O arquivo Excel enviado deve conter as seguintes colunas:
        
        - **Date**: Data da transação (formato necessário: AAAA-MM-DD)
        - **Partner**: Nome do parceiro/master
        - **Country**: Código do país (deve ser um dos países suportados)
        - **Amount**: Valor numérico representando o valor de venda
        - **Currency**: Código da moeda (ex: USD, EUR, BRL)
        
        Exemplo:
        
        | Date       | Partner      | Country | Amount  | Currency |
        |------------|--------------|---------|---------|----------|
        | 2023-10-01 | Nome Parceiro| BR      | 10000.0 | BRL      |
        | 2023-10-02 | Outra Empresa| US      | 8500.5  | USD      |
        
        Certifique-se de que todas as colunas necessárias estejam presentes e os dados estejam no formato correto.
        """)
