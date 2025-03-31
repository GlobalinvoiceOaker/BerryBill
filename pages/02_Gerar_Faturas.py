import streamlit as st
import pandas as pd
import random
import string
import os
from datetime import datetime
from utils.invoice_generator import generate_invoices_from_data, get_invoice_download_link
from utils.data_processor import load_country_settings
from utils.auth import login_required
from utils.access_control import check_access, show_access_denied
from assets.logo_header import render_logo

st.set_page_config(
    page_title="Gerar Faturas - Sistema de Gerenciamento de Faturas",
    page_icon="📄",
    layout="wide"
)

# Verifica login
username = login_required()

# Verifica permissão de acesso
if not check_access(["admin", "gerente"]):
    show_access_denied()

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
col1, col2 = st.columns([1, 3])
with col1:
    render_logo(width=150)
with col2:
    st.markdown('<div class="main-header">Gerar Faturas</div>', unsafe_allow_html=True)
    st.markdown('<div class="description">Crie faturas com base em dados processados ou manualmente</div>', unsafe_allow_html=True)

# Função para gerar número de fatura único
def generate_invoice_number(country, partner):
    """Gera um número de fatura único baseado no país, parceiro e data atual"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M')
    random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    country_code = country[:3].upper()
    partner_code = partner[:3].upper()
    
    return f"INV-{country_code}-{partner_code}-{timestamp}-{random_chars}"

# Tabs para os diferentes métodos de geração de faturas
tabs = st.tabs(["Gerar de Dados Importados", "Gerar Manualmente"])

with tabs[0]:
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
    
    if 'imported_data' in st.session_state and st.session_state.imported_data is not None:
        # Display faturas geradas (only if data is imported)
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

with tabs[1]:
    # Carrega as configurações de países
    country_settings = load_country_settings()
    
    # Layout principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Formulário para criar nova fatura
        with st.form("manual_invoice_form"):
            st.markdown("### Informações Básicas da Fatura")
            
            # Seletor de mês e ano
            col_month, col_year = st.columns(2)
            with col_month:
                month = st.selectbox("Mês", options=range(1, 13), 
                                    format_func=lambda x: datetime(2023, x, 1).strftime('%B'))
                month_name = datetime(2023, month, 1).strftime('%B')
                
            with col_year:
                current_year = datetime.now().year
                year = st.selectbox("Ano", options=range(current_year-2, current_year+1))
            
            # Seleção de país e parceiro
            col_country, col_partner = st.columns(2)
            with col_country:
                countries = list(country_settings.keys())
                country = st.selectbox("País", options=countries)
            
            with col_partner:
                partner = st.text_input("Nome do Parceiro/Master", 
                                      placeholder="Ex: Global Retail Partners")
            
            # Valores de vendas e taxas
            st.markdown("### Valores e Taxas")
            
            col_sales, col_currency = st.columns(2)
            with col_sales:
                total_sales = st.number_input("Valor Total de Vendas", 
                                           min_value=0.01, value=10000.00, 
                                           format="%.2f")
            
            with col_currency:
                if country in country_settings:
                    currency = country_settings[country].get('currency', 'USD')
                    st.text_input("Moeda", value=currency, disabled=True)
                else:
                    currency = st.text_input("Moeda", value="USD")
            
            # Taxas aplicáveis
            col_royalty, col_adfund, col_tax = st.columns(3)
            
            with col_royalty:
                default_royalty = country_settings.get(country, {}).get('royalty_rate', 5.0)
                royalty_rate = st.number_input("Taxa de Royalties (%)", 
                                            min_value=0.0, max_value=100.0, 
                                            value=default_royalty, 
                                            format="%.2f")
            
            with col_adfund:
                default_adfund = country_settings.get(country, {}).get('ad_fund_rate', 2.0)
                ad_fund_rate = st.number_input("Taxa do Fundo de Publicidade (%)", 
                                             min_value=0.0, max_value=100.0, 
                                             value=default_adfund, 
                                             format="%.2f")
            
            with col_tax:
                default_tax = country_settings.get(country, {}).get('tax_rate', 0.0)
                tax_rate = st.number_input("Taxa de Imposto (%)", 
                                         min_value=0.0, max_value=100.0, 
                                         value=default_tax, 
                                         format="%.2f")
            
            # Taxa de câmbio
            exchange_rate = st.number_input("Taxa de Câmbio (para USD)", 
                                          min_value=0.01, 
                                          value=country_settings.get(country, {}).get('exchange_rate', 1.0), 
                                          format="%.4f")
            
            # Informações adicionais
            st.markdown("### Informações Adicionais")
            
            notes = st.text_area("Notas ou Observações", 
                               placeholder="Observações adicionais para a fatura...", 
                               max_chars=500, 
                               height=100)
            
            # Botão de submissão
            submit = st.form_submit_button("Gerar Fatura", use_container_width=True)
            
            if submit:
                # Validar dados básicos
                if not partner:
                    st.error("Por favor, insira o nome do parceiro.")
                else:
                    # Calcular valores
                    royalty_amount = total_sales * (royalty_rate / 100)
                    ad_fund_amount = total_sales * (ad_fund_rate / 100)
                    subtotal = royalty_amount + ad_fund_amount
                    tax_amount = subtotal * (tax_rate / 100)
                    total_amount = subtotal + tax_amount
                    amount_usd = total_amount / exchange_rate
                    
                    # Gerar número da fatura
                    invoice_number = generate_invoice_number(country, partner)
                    
                    # Criar dados da fatura
                    invoice_data = {
                        'partner': partner,
                        'country': country,
                        'month': month,
                        'year': year,
                        'month_name': month_name,
                        'total_sales': total_sales,
                        'total_sell_out': total_sales,
                        'royalty_rate': royalty_rate,
                        'royalty_amount': royalty_amount,
                        'ad_fund_rate': ad_fund_rate,
                        'ad_fund_amount': ad_fund_amount,
                        'tax_rate': tax_rate,
                        'tax_amount': tax_amount,
                        'total_amount': total_amount,
                        'amount_usd': amount_usd,
                        'currency': currency,
                        'exchange_rate': exchange_rate,
                        'invoice_number': invoice_number,
                        'created_at': datetime.now(),
                        'sent': False,
                        'paid': False,
                        'payment_amount': 0,
                        'notes': notes,
                        'due_status': 'A Vencer'  # Status inicial
                    }
                    
                    # Armazenar no estado da sessão
                    if 'invoices' not in st.session_state:
                        st.session_state.invoices = []
                    
                    # Verificar se já existe uma fatura com o mesmo número
                    existing_numbers = [inv['invoice_number'] for inv in st.session_state.invoices]
                    if invoice_number in existing_numbers:
                        st.error(f"Uma fatura com o número {invoice_number} já existe. Por favor, tente novamente.")
                    else:
                        # Adicionar a nova fatura à lista
                        st.session_state.invoices.append(invoice_data)
                        st.success(f"Fatura {invoice_number} gerada com sucesso!")
                        st.session_state.last_generated_invoice = invoice_data
                        
                        # Recarregar o formulário para limpar os dados (opção para o usuário)
                        st.rerun()
    
    with col2:
        # Exibir detalhes da última fatura gerada
        if 'last_generated_invoice' in st.session_state:
            invoice = st.session_state.last_generated_invoice
            
            st.markdown("### Detalhes da Fatura Gerada")
            
            # Caixa visual para a fatura
            st.markdown('<div style="border:1px solid #ddd; border-radius:5px; padding:15px; background-color:#f8f9fa;">', unsafe_allow_html=True)
            
            # Número e informações básicas
            st.markdown(f"**Fatura #:** {invoice['invoice_number']}")
            st.markdown(f"**Data:** {invoice['created_at'].strftime('%d/%m/%Y')}")
            st.markdown(f"**Parceiro:** {invoice['partner']}")
            st.markdown(f"**País:** {invoice['country']}")
            st.markdown(f"**Período:** {invoice['month_name']} {invoice['year']}")
            
            # Separador
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Valores
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Cálculos:**")
                st.markdown(f"Vendas: {invoice['currency']} {invoice['total_sales']:,.2f}")
                st.markdown(f"Royalties ({invoice['royalty_rate']}%): {invoice['currency']} {invoice['royalty_amount']:,.2f}")
                st.markdown(f"Fundo ({invoice['ad_fund_rate']}%): {invoice['currency']} {invoice['ad_fund_amount']:,.2f}")
                st.markdown(f"Impostos ({invoice['tax_rate']}%): {invoice['currency']} {invoice['tax_amount']:,.2f}")
            
            with col2:
                st.markdown("**Totais:**")
                st.markdown(f"Total: {invoice['currency']} {invoice['total_amount']:,.2f}")
                st.markdown(f"Total USD: $ {invoice['amount_usd']:,.2f}")
                st.markdown(f"Taxa de Câmbio: {invoice['exchange_rate']}")
                st.markdown(f"Status: {invoice['due_status']}")
            
            # Fechar a caixa visual
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Link para download do PDF
            st.markdown("### Download da Fatura")
            st.markdown(get_invoice_download_link(invoice, "Baixar PDF da Fatura"), unsafe_allow_html=True)
        else:
            st.info("Gere uma fatura manual para ver os detalhes aqui")
            
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
        
        # Próximos passos
        st.markdown("#### Próximos Passos")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Enviar Faturas", key="enviar_manual"):
                st.switch_page("pages/03_Enviar_Faturas.py")
        
        with col2:
            if st.button("Reconciliar Pagamentos", key="reconciliar_manual"):
                st.switch_page("pages/04_Reconciliar_Pagamentos.py")
