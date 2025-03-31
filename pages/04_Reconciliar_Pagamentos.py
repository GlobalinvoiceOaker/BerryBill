import streamlit as st
import pandas as pd
from datetime import datetime
from utils.data_processor import import_payment_data
from utils.payment_reconciliation import reconcile_payments, find_potential_matches, manually_reconcile_payment
from utils.invoice_generator import create_invoice_pdf, get_invoice_download_link
from utils.auth import login_required
from assets.logo_header import render_logo, render_icon
import base64

st.set_page_config(
    page_title="Reconciliar Pagamentos - Sistema de Gerenciamento de Faturas",
    page_icon="💰",
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
    st.markdown('<div class="main-header">Reconciliar Pagamentos</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">Associe pagamentos do extrato bancário com faturas</div>', unsafe_allow_html=True)

# Inicializa estados da sessão se necessário
if 'payments' not in st.session_state:
    st.session_state.payments = None
if 'reconciled_invoices' not in st.session_state:
    st.session_state.reconciled_invoices = []

# Verifica se as faturas foram geradas
if 'invoices' not in st.session_state or not st.session_state.invoices:
    st.warning("Nenhuma fatura gerada. Por favor, gere faturas primeiro.")
    if st.button("Ir para Gerar Faturas"):
        st.switch_page("pages/02_Gerar_Faturas.py")
else:
    # Seção de importação de pagamentos
    st.markdown('<div class="sub-header">Importar Extrato Bancário</div>', unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Faça upload do extrato bancário (CSV ou Excel)", type=["csv", "xlsx", "xls"])
    
    if uploaded_file is not None:
        # Importa dados de pagamento
        payments_df, is_valid, error_message = import_payment_data(uploaded_file)
        
        if is_valid:
            st.success("Extrato bancário importado com sucesso!")
            
            # Armazena no estado da sessão
            st.session_state.payments = payments_df
            
            # Exibe dados de pagamento
            st.dataframe(payments_df.head(10), use_container_width=True)
            
            # Métricas de resumo
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Transações", len(payments_df))
            
            with col2:
                positive_amounts = payments_df[payments_df['Amount'] > 0]['Amount'].sum()
                st.metric("Total de Entradas", f"R$ {positive_amounts:,.2f}")
            
            with col3:
                negative_amounts = payments_df[payments_df['Amount'] < 0]['Amount'].sum()
                st.metric("Total de Saídas", f"R$ {abs(negative_amounts):,.2f}")
            
            # Seção de reconciliação
            st.markdown('<div class="sub-header">Reconciliar Pagamentos</div>', unsafe_allow_html=True)
            
            if st.button("Associar Pagamentos com Faturas"):
                with st.spinner("Reconciliando pagamentos..."):
                    # Filtra apenas pagamentos de entrada (valores positivos)
                    incoming_payments = payments_df[payments_df['Amount'] > 0]
                    
                    # Reconcilia pagamentos
                    reconciled_payments, updated_invoices = reconcile_payments(incoming_payments, st.session_state.invoices)
                    
                    # Armazena dados reconciliados
                    st.session_state.reconciled_payments = reconciled_payments
                    st.session_state.invoices = updated_invoices
                    
                    st.success("Pagamentos reconciliados com sucesso!")
            
            # Exibe resultados da reconciliação
            if 'reconciled_payments' in st.session_state and st.session_state.reconciled_payments:
                # Mostra pagamentos associados
                st.markdown("#### Pagamentos Associados")
                
                matched_payments = [p for p in st.session_state.reconciled_payments if p['reconciled']]
                if matched_payments:
                    matched_df = pd.DataFrame([
                        {
                            "Data": p['Date'].strftime("%d/%m/%Y") if hasattr(p['Date'], 'strftime') else p['Date'],
                            "Valor": f"R$ {p['Amount']:,.2f}",
                            "Descrição": p['Description'],
                            "Referência": p['Reference'],
                            "Fatura Associada": p['matched_invoice'],
                            "Confiança": f"{p['match_score']}%"
                        } for p in matched_payments
                    ])
                    
                    st.dataframe(matched_df, use_container_width=True)
                else:
                    st.info("Nenhum pagamento foi automaticamente associado às faturas.")
                
                # Mostra pagamentos não associados
                st.markdown("#### Pagamentos Não Associados")
                
                unmatched_payments = [p for p in st.session_state.reconciled_payments if not p['reconciled']]
                if unmatched_payments:
                    unmatched_df = pd.DataFrame([
                        {
                            "Data": p['Date'].strftime("%d/%m/%Y") if hasattr(p['Date'], 'strftime') else p['Date'],
                            "Valor": f"R$ {p['Amount']:,.2f}",
                            "Descrição": p['Description'],
                            "Referência": p['Reference']
                        } for p in unmatched_payments
                    ])
                    
                    st.dataframe(unmatched_df, use_container_width=True)
                    
                    # Reconciliação manual
                    st.markdown("#### Reconciliação Manual")
                    
                    # Seleciona pagamento não associado
                    selected_payment_idx = st.selectbox(
                        "Selecione um pagamento não associado",
                        options=range(len(unmatched_payments)),
                        format_func=lambda i: f"{unmatched_payments[i]['Date'].strftime('%d/%m/%Y') if hasattr(unmatched_payments[i]['Date'], 'strftime') else unmatched_payments[i]['Date']} - R$ {unmatched_payments[i]['Amount']:,.2f} - {unmatched_payments[i]['Description'][:30]}..."
                    )
                    
                    if selected_payment_idx is not None:
                        selected_payment = unmatched_payments[selected_payment_idx]
                        
                        # Mostra detalhes do pagamento
                        st.markdown(f"**Data do Pagamento:** {selected_payment['Date'].strftime('%d/%m/%Y') if hasattr(selected_payment['Date'], 'strftime') else selected_payment['Date']}")
                        st.markdown(f"**Valor:** R$ {selected_payment['Amount']:,.2f}")
                        st.markdown(f"**Descrição:** {selected_payment['Description']}")
                        st.markdown(f"**Referência:** {selected_payment['Reference']}")
                        
                        # Encontra possíveis correspondências para o pagamento selecionado
                        potential_matches = find_potential_matches(selected_payment, st.session_state.invoices)
                        
                        if potential_matches:
                            st.markdown("**Possíveis Faturas Correspondentes:**")
                            
                            # Converte possíveis correspondências para DataFrame
                            potential_matches_df = pd.DataFrame([
                                {
                                    "Fatura #": match['invoice']['invoice_number'],
                                    "Parceiro": match['invoice']['partner'],
                                    "Valor Total": f"{match['invoice']['currency']} {match['invoice']['total_amount']:,.2f}",
                                    "Restante": f"{match['invoice']['currency']} {match['remaining_amount']:,.2f}",
                                    "Pontuação": f"{match['score']}%",
                                    "Motivos": ", ".join(match['reasons'])
                                } for match in potential_matches
                            ])
                            
                            # Exibe possíveis correspondências
                            st.dataframe(potential_matches_df, use_container_width=True)
                            
                            # Seleciona uma fatura para associar
                            selected_invoice_idx = st.selectbox(
                                "Selecione uma fatura para associar a este pagamento",
                                options=range(len(potential_matches)),
                                format_func=lambda i: f"{potential_matches[i]['invoice']['invoice_number']} - {potential_matches[i]['invoice']['partner']} (R$ {potential_matches[i]['remaining_amount']:,.2f})"
                            )
                            
                            if selected_invoice_idx is not None:
                                selected_match = potential_matches[selected_invoice_idx]
                                selected_invoice = selected_match['invoice']
                                
                                # Opções de valor do pagamento
                                payment_amount = st.number_input(
                                    "Valor do pagamento a aplicar",
                                    min_value=0.01,
                                    max_value=float(selected_payment['Amount']),
                                    value=min(float(selected_payment['Amount']), selected_match['remaining_amount']),
                                    step=0.01
                                )
                                
                                # Aplica pagamento
                                if st.button("Aplicar Pagamento"):
                                    with st.spinner("Aplicando pagamento..."):
                                        # Atualiza o pagamento e as faturas
                                        updated_payment, updated_invoices = manually_reconcile_payment(
                                            selected_payment,
                                            selected_invoice,
                                            payment_amount,
                                            st.session_state.invoices
                                        )
                                        
                                        # Atualiza o estado da sessão
                                        # Encontra o índice do pagamento na lista original
                                        payment_idx = next((i for i, p in enumerate(st.session_state.reconciled_payments) 
                                                          if p['Date'] == updated_payment['Date'] and 
                                                          p['Amount'] == updated_payment['Amount'] and
                                                          p['Description'] == updated_payment['Description']),
                                                         None)
                                        
                                        if payment_idx is not None:
                                            st.session_state.reconciled_payments[payment_idx] = updated_payment
                                        
                                        st.session_state.invoices = updated_invoices
                                        
                                        st.success(f"Pagamento de R$ {payment_amount:,.2f} aplicado à fatura {selected_invoice['invoice_number']}!")
                                        st.rerun()
                        else:
                            st.info("Não foram encontradas faturas correspondentes para este pagamento.")
                else:
                    st.info("Todos os pagamentos foram associados às faturas.")
            
            # Seção de status de pagamento das faturas
            st.markdown('<div class="sub-header">Status de Pagamento das Faturas</div>', unsafe_allow_html=True)
            
            # Converte para DataFrame para exibição mais fácil
            invoice_status_df = pd.DataFrame([
                {
                    "Fatura #": inv['invoice_number'],
                    "Parceiro": inv['partner'],
                    "País": inv['country'],
                    "Período": f"{inv['month_name']} {inv['year']}",
                    "Valor Total": f"{inv['currency']} {inv['total_amount']:,.2f}",
                    "Valor Pago": f"{inv['currency']} {inv.get('payment_amount', 0):,.2f}",
                    "Valor Restante": f"{inv['currency']} {inv['total_amount'] - inv.get('payment_amount', 0):,.2f}",
                    "Status": "Paga" if inv.get('paid', False) else "Parcialmente Paga" if inv.get('payment_amount', 0) > 0 else "Não Paga",
                    "Data de Pagamento": inv.get('payment_date', '').strftime("%d/%m/%Y") if hasattr(inv.get('payment_date', ''), 'strftime') else inv.get('payment_date', '')
                } for inv in st.session_state.invoices
            ])
            
            st.dataframe(invoice_status_df, use_container_width=True)
            
            # Métricas de resumo
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_invoiced = sum(inv['total_amount'] for inv in st.session_state.invoices)
                st.metric("Total Faturado", f"R$ {total_invoiced:,.2f}")
            
            with col2:
                total_paid = sum(inv.get('payment_amount', 0) for inv in st.session_state.invoices)
                st.metric("Total Pago", f"R$ {total_paid:,.2f}")
            
            with col3:
                st.metric("Valor Restante", f"R$ {total_invoiced - total_paid:,.2f}")
            
            with col4:
                paid_ratio = (total_paid / total_invoiced * 100) if total_invoiced > 0 else 0
                st.metric("Taxa de Pagamento", f"{paid_ratio:.1f}%")
            
            # Visualização direta de faturas
            st.markdown('<div class="sub-header">Visualizar Faturas</div>', unsafe_allow_html=True)
            
            # Seleciona uma fatura para visualizar
            selected_invoice_view_idx = st.selectbox(
                "Selecione uma fatura para visualizar",
                options=range(len(st.session_state.invoices)),
                format_func=lambda i: f"{st.session_state.invoices[i]['invoice_number']} - {st.session_state.invoices[i]['partner']} ({st.session_state.invoices[i]['currency']} {st.session_state.invoices[i]['total_amount']:,.2f})"
            )
            
            if selected_invoice_view_idx is not None:
                selected_invoice_view = st.session_state.invoices[selected_invoice_view_idx]
                
                # Cria o PDF da fatura
                invoice_pdf = create_invoice_pdf(selected_invoice_view)
                
                # Converte o PDF para base64 para embutir
                encoded_pdf = base64.b64encode(invoice_pdf).decode('utf-8')
                
                # Adiciona botão de download
                st.download_button(
                    label="Baixar Fatura em PDF",
                    data=invoice_pdf,
                    file_name=f"{selected_invoice_view['invoice_number']}.pdf",
                    mime="application/pdf"
                )
                
                # Exibe o PDF embutido
                st.markdown(f"""
                <h4>Visualização da Fatura</h4>
                <iframe src="data:application/pdf;base64,{encoded_pdf}" width="100%" height="600" type="application/pdf"></iframe>
                """, unsafe_allow_html=True)
            
            # Próximos passos
            st.markdown("#### Próximos Passos")
            if st.button("Ir para Relatórios Financeiros"):
                st.switch_page("pages/05_Relatorios_Financeiros.py")
        else:
            st.error(f"Erro ao importar extrato bancário: {error_message}")
            
            # Mostra o formato necessário
            with st.expander("Ver Formato de Dados Necessário"):
                st.markdown("""
                O extrato bancário enviado deve conter as seguintes colunas:
                
                - **Date**: Data da transação (formato necessário: AAAA-MM-DD)
                - **Amount**: Valor numérico (positivo para entradas de pagamento, negativo para saídas)
                - **Description**: Descrição ou memorando da transação
                - **Reference**: Número de referência ou informações adicionais
                
                Exemplo:
                
                | Date       | Amount   | Description                | Reference    |
                |------------|----------|----------------------------|--------------|
                | 2023-10-15 | 5000.0   | Pagamento do Parceiro A    | INV-123      |
                | 2023-10-16 | -2500.0  | Pagamento de aluguel       | ALUG-OUT     |
                
                Certifique-se de que todas as colunas necessárias estejam presentes e os dados estejam no formato correto.
                """)
    else:
        # Exibe o formato de amostra de dados
        st.info("Por favor, faça upload de um arquivo de extrato bancário (CSV ou Excel) para prosseguir.")
        
        with st.expander("Ver Formato de Dados Necessário"):
            st.markdown("""
            O extrato bancário enviado deve conter as seguintes colunas:
            
            - **Date**: Data da transação (formato necessário: AAAA-MM-DD)
            - **Amount**: Valor numérico (positivo para entradas de pagamento, negativo para saídas)
            - **Description**: Descrição ou memorando da transação
            - **Reference**: Número de referência ou informações adicionais
            
            Exemplo:
            
            | Date       | Amount   | Description                | Reference    |
            |------------|----------|----------------------------|--------------|
            | 2023-10-15 | 5000.0   | Pagamento do Parceiro A    | INV-123      |
            | 2023-10-16 | -2500.0  | Pagamento de aluguel       | ALUG-OUT     |
            
            Certifique-se de que todas as colunas necessárias estejam presentes e os dados estejam no formato correto.
            """)
        
        # Mostra o status atual das faturas
        if st.session_state.invoices:
            st.markdown('<div class="sub-header">Status Atual das Faturas</div>', unsafe_allow_html=True)
            
            # Converte para DataFrame para exibição mais fácil
            invoice_status_df = pd.DataFrame([
                {
                    "Fatura #": inv['invoice_number'],
                    "Parceiro": inv['partner'],
                    "País": inv['country'],
                    "Período": f"{inv['month_name']} {inv['year']}",
                    "Valor Total": f"{inv['currency']} {inv['total_amount']:,.2f}",
                    "Valor Pago": f"{inv['currency']} {inv.get('payment_amount', 0):,.2f}",
                    "Valor Restante": f"{inv['currency']} {inv['total_amount'] - inv.get('payment_amount', 0):,.2f}",
                    "Status": "Paga" if inv.get('paid', False) else "Parcialmente Paga" if inv.get('payment_amount', 0) > 0 else "Não Paga",
                    "Data de Pagamento": inv.get('payment_date', '').strftime("%d/%m/%Y") if hasattr(inv.get('payment_date', ''), 'strftime') else inv.get('payment_date', '')
                } for inv in st.session_state.invoices
            ])
            
            st.dataframe(invoice_status_df, use_container_width=True)
