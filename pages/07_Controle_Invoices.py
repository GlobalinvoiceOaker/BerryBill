import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from utils.invoice_generator import get_invoice_download_link
import json

st.set_page_config(
    page_title="Controle de Invoices - Sistema de Gerenciamento de Faturas",
    page_icon="📊",
    layout="wide"
)

# Estilo personalizado
try:
    with open('assets/style.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
except:
    pass

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
    .action-button {
        margin: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Título da página
st.markdown('<div class="main-header">Controle de Invoices</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Gerencie todas as faturas do sistema em um único lugar.</div>', unsafe_allow_html=True)

# Verificar se existem faturas geradas
if 'invoices' not in st.session_state or not st.session_state.invoices:
    st.warning("Nenhuma fatura gerada. Por favor, gere faturas primeiro.")
    if st.button("Ir para Gerar Faturas"):
        st.switch_page("pages/02_Gerar_Faturas.py")
else:
    # Definir função para classificar faturas por status de vencimento
    def classificar_fatura_por_vencimento(invoice):
        try:
            # Extrair data de vencimento (assumindo que seja 30 dias após a criação)
            if 'created_at' in invoice:
                if isinstance(invoice['created_at'], str):
                    created_date = datetime.strptime(invoice['created_at'], "%Y-%m-%d")
                else:
                    created_date = invoice['created_at']
                
                due_date = created_date + timedelta(days=30)
                
                # Verificar se a fatura está paga
                if invoice.get('paid', False):
                    return "Liquidada"
                
                # Verificar se está vencida
                today = datetime.now()
                if due_date < today:
                    return "Vencida"
                else:
                    return "A Vencer"
            else:
                return "N/A"
        except Exception as e:
            st.error(f"Erro ao classificar fatura: {e}")
            return "Erro"

    # Adicionar classificação de vencimento para todas as faturas
    for invoice in st.session_state.invoices:
        if 'due_status' not in invoice:
            invoice['due_status'] = classificar_fatura_por_vencimento(invoice)

    # Filtros
    st.markdown('<div class="sub-header">Filtros</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filtro por país
        paises = sorted(list({inv.get('country', 'N/A') for inv in st.session_state.invoices}))
        pais_selecionado = st.selectbox("Filtrar por País", options=["Todos"] + paises)
    
    with col2:
        # Filtro por Master (parceiro)
        masters = sorted(list({inv.get('partner', 'N/A') for inv in st.session_state.invoices}))
        master_selecionado = st.selectbox("Filtrar por Master", options=["Todos"] + masters)
    
    with col3:
        # Filtro por status de vencimento
        status_options = ["Todos", "A Vencer", "Vencida", "Liquidada"]
        status_selecionado = st.selectbox("Filtrar por Status", options=status_options)
    
    # Filtro por número de invoice
    numero_invoice = st.text_input("Filtrar por Número de Invoice", "")

    # Aplicar filtros
    faturas_filtradas = st.session_state.invoices
    
    if pais_selecionado != "Todos":
        faturas_filtradas = [inv for inv in faturas_filtradas if inv.get('country', 'N/A') == pais_selecionado]
    
    if master_selecionado != "Todos":
        faturas_filtradas = [inv for inv in faturas_filtradas if inv.get('partner', 'N/A') == master_selecionado]
    
    if status_selecionado != "Todos":
        faturas_filtradas = [inv for inv in faturas_filtradas if inv.get('due_status', 'N/A') == status_selecionado]
    
    if numero_invoice:
        faturas_filtradas = [inv for inv in faturas_filtradas if numero_invoice.lower() in inv.get('invoice_number', '').lower()]

    # Exibir resultados
    st.markdown('<div class="sub-header">Invoices</div>', unsafe_allow_html=True)
    
    if not faturas_filtradas:
        st.info("Nenhuma fatura encontrada com os filtros aplicados.")
    else:
        # Preparar dados para exibição
        faturas_display = []
        for idx, inv in enumerate(faturas_filtradas):
            # Criar um dicionário com os dados para exibição
            faturas_display.append({
                "ID": idx,
                "Fatura #": inv.get('invoice_number', 'N/A'),
                "Master": inv.get('partner', 'N/A'),
                "País": inv.get('country', 'N/A'),
                "Período": f"{inv.get('month_name', 'N/A')} {inv.get('year', 'N/A')}",
                "Valor USD": f"USD {inv.get('amount_usd', 0):,.2f}",
                "Valor Local": f"{inv.get('currency', '')} {inv.get('total_amount', 0):,.2f}",
                "Status": inv.get('due_status', 'N/A'),
                "Data Criação": inv.get('created_at', 'N/A').strftime("%d/%m/%Y") if hasattr(inv.get('created_at', 'N/A'), 'strftime') else inv.get('created_at', 'N/A')
            })

        # Exibir na tabela
        faturas_df = pd.DataFrame(faturas_display)
        
        # Adicionar estilos para status
        def highlight_status(val):
            if val == "Liquidada":
                return 'background-color: #d4edda; color: #155724'
            elif val == "Vencida":
                return 'background-color: #f8d7da; color: #721c24'
            elif val == "A Vencer":
                return 'background-color: #fff3cd; color: #856404'
            return ''
        
        # Aplicar estilo
        styled_df = faturas_df.style.applymap(highlight_status, subset=['Status'])
        
        # Remover a coluna ID da visualização, mas manter para referência
        cols_to_display = [col for col in faturas_df.columns if col != "ID"]
        
        # Exibir a tabela
        st.dataframe(faturas_df[cols_to_display], use_container_width=True)
        
        # Ações para faturas selecionadas
        st.markdown('<div class="sub-header">Ações</div>', unsafe_allow_html=True)
        
        # Selecionar fatura para ação
        selected_invoice_idx = st.selectbox("Selecione uma fatura para realizar ações:", 
                                        options=list(range(len(faturas_filtradas))),
                                        format_func=lambda x: f"{faturas_filtradas[x].get('invoice_number', 'N/A')} - {faturas_filtradas[x].get('partner', 'N/A')} ({faturas_filtradas[x].get('country', 'N/A')})")
        
        selected_invoice = faturas_filtradas[selected_invoice_idx]
        
        # Exibir informações detalhadas da fatura selecionada
        st.markdown("#### Detalhes da Fatura Selecionada")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Fatura #:** {selected_invoice.get('invoice_number', 'N/A')}")
            st.markdown(f"**Master:** {selected_invoice.get('partner', 'N/A')}")
            st.markdown(f"**País:** {selected_invoice.get('country', 'N/A')}")
            st.markdown(f"**Período:** {selected_invoice.get('month_name', 'N/A')} {selected_invoice.get('year', 'N/A')}")
        
        with col2:
            st.markdown(f"**Valor USD:** USD {selected_invoice.get('amount_usd', 0):,.2f}")
            st.markdown(f"**Valor Local:** {selected_invoice.get('currency', '')} {selected_invoice.get('total_amount', 0):,.2f}")
            st.markdown(f"**Status:** {selected_invoice.get('due_status', 'N/A')}")
            created_at = selected_invoice.get('created_at', 'N/A')
            st.markdown(f"**Data de Criação:** {created_at.strftime('%d/%m/%Y') if hasattr(created_at, 'strftime') else created_at}")
        
        # Botões de ação
        st.markdown("#### Ações Disponíveis")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            # Botão para visualizar fatura
            if st.button("Visualizar Invoice", use_container_width=True, key="view_invoice"):
                st.markdown("### Visualização da Invoice")
                
                # Exibir detalhes da fatura
                st.json(json.dumps({k: str(v) if isinstance(v, (datetime, pd.Timestamp)) else v 
                                   for k, v in selected_invoice.items() 
                                   if k not in ['pdf_bytes', 'image_bytes']}, indent=4))

        with col2:
            # Botão para download do PDF
            pdf_link = get_invoice_download_link(selected_invoice, "Baixar PDF")
            st.markdown(pdf_link, unsafe_allow_html=True)
        
        with col3:
            # Botão para marcar como paga
            if st.button("Marcar como Paga" if not selected_invoice.get('paid', False) else "Desmarcar Pagamento", 
                        use_container_width=True,
                        key="pay_invoice"):
                
                # Encontrar a invoice original na lista de sessão e atualizar
                for inv in st.session_state.invoices:
                    if inv.get('invoice_number') == selected_invoice.get('invoice_number'):
                        inv['paid'] = not inv.get('paid', False)
                        inv['due_status'] = "Liquidada" if inv['paid'] else classificar_fatura_por_vencimento(inv)
                        if inv['paid']:
                            inv['payment_date'] = datetime.now()
                            inv['payment_amount'] = inv.get('total_amount', 0)
                        else:
                            inv.pop('payment_date', None)
                            inv['payment_amount'] = 0
                
                st.success(f"Fatura {selected_invoice.get('invoice_number')} marcada como {'paga' if not selected_invoice.get('paid', False) else 'não paga'}!")
                st.rerun()
        
        with col4:
            # Botão para editar dados da fatura
            if st.button("Editar Dados", use_container_width=True, key="edit_invoice"):
                st.session_state.edit_invoice_id = selected_invoice.get('invoice_number')
                st.session_state.edit_invoice_data = selected_invoice
                st.rerun()
        
        with col5:
            # Botão para excluir fatura
            if st.button("Excluir Invoice", use_container_width=True, key="delete_invoice"):
                # Confirmar exclusão
                st.warning(f"Tem certeza que deseja excluir a fatura {selected_invoice.get('invoice_number')}?")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Sim, excluir", key="confirm_delete"):
                        # Encontrar e remover a fatura da lista
                        st.session_state.invoices = [inv for inv in st.session_state.invoices 
                                                   if inv.get('invoice_number') != selected_invoice.get('invoice_number')]
                        st.success(f"Fatura {selected_invoice.get('invoice_number')} excluída com sucesso!")
                        st.rerun()
                
                with col2:
                    if st.button("Cancelar", key="cancel_delete"):
                        st.rerun()
        
        # Formulário de edição de fatura (ativo apenas quando editar é clicado)
        if 'edit_invoice_id' in st.session_state and st.session_state.edit_invoice_id:
            st.markdown("#### Editar Fatura")
            
            edit_data = st.session_state.edit_invoice_data
            
            with st.form("edit_invoice_form"):
                # Campos editáveis
                partner = st.text_input("Master", value=edit_data.get('partner', ''))
                country = st.text_input("País", value=edit_data.get('country', ''))
                total_amount = st.number_input("Valor Total", value=float(edit_data.get('total_amount', 0)))
                amount_usd = st.number_input("Valor USD", value=float(edit_data.get('amount_usd', 0)))
                currency = st.text_input("Moeda", value=edit_data.get('currency', ''))
                
                # Botões do formulário
                col1, col2 = st.columns(2)
                with col1:
                    submit = st.form_submit_button("Salvar Alterações")
                
                with col2:
                    cancel = st.form_submit_button("Cancelar")
                
                if submit:
                    # Atualizar a fatura na lista de sessão
                    for inv in st.session_state.invoices:
                        if inv.get('invoice_number') == edit_data.get('invoice_number'):
                            inv['partner'] = partner
                            inv['country'] = country
                            inv['total_amount'] = total_amount
                            inv['amount_usd'] = amount_usd
                            inv['currency'] = currency
                    
                    # Limpar estado de edição
                    st.session_state.edit_invoice_id = None
                    st.session_state.edit_invoice_data = None
                    
                    st.success(f"Fatura {edit_data.get('invoice_number')} atualizada com sucesso!")
                    st.rerun()
                
                if cancel:
                    # Limpar estado de edição
                    st.session_state.edit_invoice_id = None
                    st.session_state.edit_invoice_data = None
                    st.rerun()

    # Seção para navegação
    st.markdown("---")
    st.markdown("#### Navegação")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Voltar para Dashboard", use_container_width=True):
            st.switch_page("app.py")
    
    with col2:
        if st.button("Ir para Gerar Faturas", use_container_width=True):
            st.switch_page("pages/02_Gerar_Faturas.py")
    
    with col3:
        if st.button("Ir para Relatórios", use_container_width=True):
            st.switch_page("pages/05_Relatorios_Financeiros.py")