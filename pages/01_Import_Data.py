import streamlit as st
import pandas as pd
import os
from utils.data_processor import validate_data, process_data

st.set_page_config(
    page_title="Importar Dados - Sistema de Gerenciamento de Faturas",
    page_icon="📊",
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
st.markdown('<div class="main-header">Importar Dados</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Faça upload e processe dados de venda dos parceiros (Masters)</div>', unsafe_allow_html=True)

# Upload de arquivo
uploaded_file = st.file_uploader("Faça upload do arquivo Excel com dados de venda", type=["xlsx", "xls"])

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
                        st.switch_page("pages/02_Generate_Invoices.py")
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
