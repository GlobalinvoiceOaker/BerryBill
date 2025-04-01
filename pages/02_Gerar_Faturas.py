import streamlit as st
import pandas as pd
import random
import string
import os
from datetime import datetime, timedelta
from utils.invoice_generator import generate_invoices_from_data, get_invoice_download_link
from utils.data_processor import load_country_settings
from utils.auth import login_required
from utils.access_control import check_access, show_access_denied
from assets.logo_header import render_logo
from utils.exchange_rate import get_bc_exchange_rate, get_exchange_rates_for_countries

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
        
        # Configurações avançadas
        with st.expander("Configurações Avançadas de Faturamento"):
            # Data de emissão
            col_issue_date, col_exchange_rate = st.columns(2)
            with col_issue_date:
                issue_date = st.date_input("Data de Emissão", value=datetime.now())
            
            # Opções de câmbio
            with col_exchange_rate:
                use_bc_exchange_rate = st.checkbox("Usar taxa de câmbio do Banco Central", 
                                               value=st.session_state.get('use_bc_auto_rate', True),
                                               key='use_bc_auto_rate_checkbox')
                
                # Atualiza o estado da sessão
                st.session_state.use_bc_auto_rate = use_bc_exchange_rate
                
                if use_bc_exchange_rate:
                    # Se usuário quiser usar taxa do BC, tente obtê-la automaticamente
                    try:
                        exchange_rate_bc = get_bc_exchange_rate(issue_date)
                        if exchange_rate_bc:
                            st.success(f"Taxa obtida com sucesso: {exchange_rate_bc:.4f}")
                            st.session_state.current_bc_rate = exchange_rate_bc
                        else:
                            st.warning("Não foi possível obter a taxa de câmbio para a data selecionada. Será usada a taxa padrão.")
                    except Exception as e:
                        st.warning(f"Erro ao obter taxa: {str(e)}. Usando taxa padrão.")
            
            # Opções de parcelamento
            enable_installments = st.checkbox("Habilitar parcelamento das faturas")
            
            if enable_installments:
                col_num_inst, col_first_due = st.columns(2)
                
                with col_num_inst:
                    num_installments = st.number_input("Número de Parcelas", min_value=1, max_value=12, value=2)
                
                with col_first_due:
                    first_due_days = st.number_input("Dias até o vencimento da primeira parcela", 
                                                  min_value=1, max_value=90, value=30)
                
                # Distribuição dos valores
                installment_distribution = st.radio(
                    "Distribuição das parcelas",
                    options=["Iguais", "Percentual"],
                    horizontal=True
                )
                
                if installment_distribution == "Percentual":
                    st.info("Defina a porcentagem de cada parcela (o total deve ser 100%)")
                    
                    percentages = []
                    cols = st.columns(min(4, num_installments))
                    
                    for i in range(num_installments):
                        col_idx = i % 4
                        with cols[col_idx]:
                            default_pct = 100 / num_installments
                            pct = st.number_input(
                                f"Parcela {i+1} (%)", 
                                min_value=1.0, 
                                max_value=100.0, 
                                value=float(f"{default_pct:.1f}"),
                                key=f"pct_{i}"
                            )
                            percentages.append(pct)
                    
                    # Validar total de porcentagens
                    total_pct = sum(percentages)
                    if abs(total_pct - 100.0) > 0.01:
                        st.warning(f"A soma das porcentagens ({total_pct:.1f}%) deve ser 100%. Por favor, ajuste os valores.")
                    
                    # Armazenar na sessão para uso posterior
                    st.session_state.installment_percentages = percentages
                
                # Calcular dias entre parcelas (assume uma distribuição uniforme)
                days_between_payments = st.number_input("Dias entre parcelas", 
                                                    min_value=15, 
                                                    max_value=90, 
                                                    value=30)
                
                # Armazenar configurações para uso posterior
                st.session_state.installment_config = {
                    "enabled": True,
                    "num_installments": num_installments,
                    "first_due_days": first_due_days,
                    "distribution": installment_distribution,
                    "days_between": days_between_payments
                }
            else:
                # Se não usar parcelamento, limpar configurações anteriores
                if 'installment_config' in st.session_state:
                    st.session_state.installment_config = {"enabled": False}
        
        # Exibir dados filtrados
        st.markdown("#### Visualização dos Dados Filtrados")
        st.dataframe(filtered_data.head(10), use_container_width=True)
        
        # Botão de geração de faturas
        if st.button("Gerar Faturas"):
            with st.spinner("Gerando faturas..."):
                # Gerar faturas básicas
                invoices = generate_invoices_from_data(filtered_data)
                
                # Adicionar informações de data de emissão e câmbio
                for invoice in invoices:
                    # Adicionar data de emissão
                    invoice['issue_date'] = issue_date
                    
                    # Adicionar taxa de câmbio do BC se disponível
                    if use_bc_exchange_rate and 'current_bc_rate' in st.session_state:
                        invoice['exchange_rate'] = st.session_state.current_bc_rate
                        invoice['amount_usd'] = invoice['total_amount'] / st.session_state.current_bc_rate
                    
                    # Adicionar informações de parcelamento se habilitado
                    if 'installment_config' in st.session_state and st.session_state.installment_config.get('enabled', False):
                        config = st.session_state.installment_config
                        
                        # Calcular datas e valores das parcelas
                        installments = []
                        
                        # Usar distribuição percentual se escolhida
                        if config['distribution'] == "Percentual" and 'installment_percentages' in st.session_state:
                            percentages = st.session_state.installment_percentages
                            
                            # Ajustar para garantir que a soma seja exatamente 100%
                            if abs(sum(percentages) - 100.0) > 0.01:
                                adjustment = 100.0 - sum(percentages)
                                percentages[-1] += adjustment
                            
                            # Criar parcelas com valores baseados nas porcentagens
                            for i in range(config['num_installments']):
                                due_date = issue_date + timedelta(days=config['first_due_days'] + (i * config['days_between']))
                                amount = invoice['total_amount'] * (percentages[i] / 100.0)
                                
                                installments.append({
                                    'number': i+1,
                                    'due_date': due_date,
                                    'amount': amount
                                })
                        else:
                            # Divisão igual entre parcelas
                            equal_amount = invoice['total_amount'] / config['num_installments']
                            
                            for i in range(config['num_installments']):
                                due_date = issue_date + timedelta(days=config['first_due_days'] + (i * config['days_between']))
                                
                                installments.append({
                                    'number': i+1,
                                    'due_date': due_date,
                                    'amount': equal_amount
                                })
                        
                        # Adicionar à fatura
                        invoice['installments'] = installments
                
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
                        
                        # Mostrar data de emissão se disponível
                        if 'issue_date' in selected_invoice and selected_invoice['issue_date']:
                            issue_date = selected_invoice['issue_date']
                            if isinstance(issue_date, datetime):
                                issue_date_str = issue_date.strftime('%d/%m/%Y')
                            else:
                                issue_date_str = issue_date.strftime('%d/%m/%Y') if hasattr(issue_date, 'strftime') else str(issue_date)
                            st.markdown(f"**Data de Emissão:** {issue_date_str}")
                        else:
                            st.markdown(f"**Data:** {selected_invoice['created_at'].strftime('%d/%m/%Y')}")
                            
                        st.markdown(f"**Parceiro:** {selected_invoice['partner']}")
                        st.markdown(f"**País:** {selected_invoice['country']}")
                        st.markdown(f"**Período:** {selected_invoice['month_name']} {selected_invoice['year']}")
                    
                    with col2:
                        st.markdown(f"**Total de Vendas:** {selected_invoice['currency']} {selected_invoice['total_sell_out']:,.2f}")
                        st.markdown(f"**Valor de Royalties:** {selected_invoice['currency']} {selected_invoice['royalty_amount']:,.2f}")
                        st.markdown(f"**Valor do Fundo de Publicidade:** {selected_invoice['currency']} {selected_invoice['ad_fund_amount']:,.2f}")
                        st.markdown(f"**Valor de Impostos:** {selected_invoice['currency']} {selected_invoice['tax_amount']:,.2f}")
                        st.markdown(f"**Valor Total:** {selected_invoice['currency']} {selected_invoice['total_amount']:,.2f}")
                        if 'amount_usd' in selected_invoice:
                            st.markdown(f"**Total USD:** $ {selected_invoice['amount_usd']:,.2f}")
                        
                    # Mostrar informações de parcelamento, se houverem
                    if 'installments' in selected_invoice and selected_invoice['installments']:
                        st.markdown("---")
                        st.markdown("**Plano de Parcelamento:**")
                        
                        for i, installment in enumerate(selected_invoice['installments']):
                            due_date = installment['due_date']
                            due_date_str = due_date.strftime('%d/%m/%Y') if hasattr(due_date, 'strftime') else str(due_date)
                            st.markdown(f"Parcela {i+1}: {selected_invoice['currency']} {installment['amount']:,.2f} - Vencimento: {due_date_str}")
                    
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
            
            # Categoria de fatura
            invoice_categories = [
                "Royaltie", 
                "Ad-fund", 
                "Master Franchise Fee", 
                "Franchise Fee", 
                "CPG Distribution", 
                "Development Agreement", 
                "Other Recomes"
            ]
            invoice_category = st.selectbox("Categoria de Fatura", options=invoice_categories)
            
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
                # Mapeamento de códigos de país para nomes completos (atualizados para 3 letras)
                country_names = {
                    'BRA': 'Brasil',
                    'USA': 'Estados Unidos',
                    'ESP': 'Espanha',
                    'PRT': 'Portugal',
                    'MEX': 'México',
                    'COL': 'Colômbia',
                    'ARG': 'Argentina',
                    'CHL': 'Chile',
                    'PER': 'Peru',
                    'ITA': 'Itália',
                    'GBR': 'Reino Unido',
                    'FRA': 'França',
                    'DEU': 'Alemanha',
                    'AUS': 'Austrália',
                    'NZL': 'Nova Zelândia',
                    'JPN': 'Japão',
                    'CHN': 'China',
                    'ARE': 'Emirados Árabes Unidos',
                    'SAU': 'Arábia Saudita',
                    'KWT': 'Kuwait',
                    'QAT': 'Qatar',
                    # Também mantemos a compatibilidade com códigos de 2 letras
                    'BR': 'Brasil',
                    'US': 'Estados Unidos',
                    'ES': 'Espanha',
                    'PT': 'Portugal',
                    'MX': 'México',
                    'CO': 'Colômbia',
                    'AR': 'Argentina',
                    'CL': 'Chile',
                    'PE': 'Peru',
                    'IT': 'Itália',
                    'UK': 'Reino Unido',
                    'FR': 'França',
                    'DE': 'Alemanha',
                    'AU': 'Austrália',
                    'NZ': 'Nova Zelândia',
                    'JP': 'Japão',
                    'CN': 'China',
                    'AE': 'Emirados Árabes Unidos',
                    'SA': 'Arábia Saudita',
                    'KW': 'Kuwait',
                    'QA': 'Qatar',
                }
                
                # Criar opções de país com nome e código para o selectbox
                country_options = []
                country_codes = {}
                for code in country_settings.keys():
                    name = country_names.get(code, code)
                    display_name = f"{name} ({code})"
                    country_options.append(display_name)
                    country_codes[display_name] = code
                
                # Exibir selectbox com nomes completos
                country_display = st.selectbox("País", options=country_options)
                
                # Extrair o código do país da opção selecionada
                country = country_codes[country_display]
            
            with col_partner:
                partner = st.text_input("Nome do Parceiro/Master", 
                                      placeholder="Ex: Global Retail Partners")
            
            # Data de emissão e vencimento
            st.markdown("### Datas da Fatura")
            col_issue_date, col_due_date = st.columns(2)
            with col_issue_date:
                issue_date = st.date_input("Data de Emissão", value=datetime.now())
            
            with col_due_date:
                # Data de vencimento padrão 30 dias após a emissão
                default_due_date = issue_date + timedelta(days=30)
                due_date = st.date_input("Data de Vencimento", value=default_due_date)
                
                # Verificar se a data de vencimento é posterior à data de emissão
                if due_date < issue_date:
                    st.warning("A data de vencimento não pode ser anterior à data de emissão.")
            
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
                # Ajuste aqui: multiplicamos por 100 para exibir como percentual e dividimos ao salvar
                default_royalty = country_settings.get(country, {}).get('royalty_rate', 0.05) * 100
                royalty_rate = st.number_input("Taxa de Royalties (%)", 
                                            min_value=0.0, max_value=100.0, 
                                            value=default_royalty, 
                                            format="%.2f")
            
            with col_adfund:
                # Ajuste aqui: multiplicamos por 100 para exibir como percentual e dividimos ao salvar
                default_adfund = country_settings.get(country, {}).get('ad_fund_rate', 0.02) * 100
                ad_fund_rate = st.number_input("Taxa do Fundo de Publicidade (%)", 
                                             min_value=0.0, max_value=100.0, 
                                             value=default_adfund, 
                                             format="%.2f")
            
            with col_tax:
                # Ajuste aqui: multiplicamos por 100 para exibir como percentual e dividimos ao salvar
                default_tax = country_settings.get(country, {}).get('tax_rate', 0.0) * 100
                tax_rate = st.number_input("Taxa de Imposto (%)", 
                                         min_value=0.0, max_value=100.0, 
                                         value=default_tax, 
                                         format="%.2f")
            
            # Opções de parcelamento
            st.markdown("### Opções de Parcelamento")
            enable_installments = st.checkbox("Habilitar parcelamento da fatura")
            
            # Configurações de parcelamento (se habilitado)
            installments_data = []
            if enable_installments:
                col_num_installments, col_first_due = st.columns(2)
                
                with col_num_installments:
                    num_installments = st.number_input("Número de Parcelas", min_value=1, max_value=12, value=2)
                
                with col_first_due:
                    # Primeira parcela vence em 30 dias por padrão
                    first_due_date = st.date_input("Data de Vencimento da Primeira Parcela", 
                                               value=issue_date + timedelta(days=30))
                
                # Se a primeira data for anterior à data de emissão, alerta o usuário
                if first_due_date < issue_date:
                    st.warning("A data de vencimento da primeira parcela é anterior à data de emissão da fatura.")
                
                # Distribuição do valor
                st.markdown("#### Distribuição do Valor por Parcela")
                
                # Calcular valores - mesmo método atualizado
                # 1. Calcula impostos locais sobre o total de vendas
                tax_amount = total_sales * (tax_rate / 100)
                # 2. Subtrai impostos para calcular base para royalties e fundo
                base_amount = total_sales - tax_amount
                # 3. Calcula royalties e fundo sobre a base
                royalty_amount = base_amount * (royalty_rate / 100)
                ad_fund_amount = base_amount * (ad_fund_rate / 100)
                # 4. Calcula subtotal e total
                subtotal = royalty_amount + ad_fund_amount
                total_amount = subtotal + tax_amount
                
                # Distribuir em parcelas iguais por padrão
                equal_amount = total_amount / num_installments
                
                # Interface para configurar cada parcela
                installments_data = []
                
                for i in range(num_installments):
                    col_inst_num, col_inst_date, col_inst_amount = st.columns([1, 2, 2])
                    
                    with col_inst_num:
                        st.markdown(f"**Parcela {i+1}**")
                    
                    with col_inst_date:
                        # Calcular data de vencimento desta parcela (30 dias entre parcelas)
                        due_date = first_due_date + timedelta(days=i*30)
                        due_date_str = due_date.strftime("%d/%m/%Y")
                        st.text_input(f"Vencimento parcela {i+1}", value=due_date_str, key=f"due_date_{i}", disabled=True)
                    
                    with col_inst_amount:
                        inst_amount = st.number_input(f"Valor parcela {i+1}", 
                                                   min_value=0.01, 
                                                   value=round(equal_amount, 2),
                                                   format="%.2f",
                                                   key=f"inst_amount_{i}")
                    
                    # Guardar informações da parcela
                    installments_data.append({
                        'number': i+1,
                        'due_date': due_date,
                        'amount': inst_amount
                    })
                
                # Verificar se a soma das parcelas é igual ao valor total
                total_installments = sum(inst['amount'] for inst in installments_data)
                if abs(total_installments - total_amount) > 0.01:
                    st.warning(f"A soma das parcelas ({total_installments:.2f}) é diferente do valor total da fatura ({total_amount:.2f}).")
            
            # Taxa de câmbio
            st.markdown("### Taxa de Câmbio")
            
            # Botão para obtenção de taxa de câmbio não pode estar no formulário
            # Movido para fora do formulário e substituído por checkbox e sessão
            use_bc_rate = st.checkbox("Usar taxa de câmbio do Banco Central", 
                                    value=st.session_state.get('use_bc_rate', False),
                                    key='use_bc_rate_checkbox')
            
            # Atualiza o estado da sessão com a escolha do usuário
            st.session_state.use_bc_rate = use_bc_rate
            
            # Se o usuário quiser usar a taxa do BC, tenta obtê-la automaticamente
            if use_bc_rate:
                try:
                    # Usa a data de emissão atual do formulário
                    current_issue_date = issue_date
                    exchange_rate_bc = get_bc_exchange_rate(current_issue_date)
                    
                    if exchange_rate_bc:
                        st.session_state.exchange_rate_bc = exchange_rate_bc
                        st.success(f"Taxa do Banco Central obtida: {exchange_rate_bc:.4f}")
                    else:
                        st.warning("Não foi possível obter a taxa para a data selecionada. Usando taxa padrão.")
                except Exception as e:
                    st.warning(f"Erro ao obter taxa: {str(e)}. Usando taxa padrão.")
            
            # Campo para taxa de câmbio (usa a do BC se disponível)
            default_rate = 0.0
            if use_bc_rate and 'exchange_rate_bc' in st.session_state:
                default_rate = st.session_state.exchange_rate_bc
            else:
                default_rate = country_settings.get(country, {}).get('exchange_rate', 1.0)
                
            exchange_rate = st.number_input("Taxa de Câmbio (para USD)", 
                                        min_value=0.01, 
                                        value=float(default_rate), 
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
                    # Calcular valores - primeiro aplica impostos locais, depois aplica as alíquotas
                    # 1. Calcula impostos locais sobre o total de vendas
                    tax_amount = total_sales * (tax_rate / 100)
                    # 2. Subtrai impostos para calcular base para royalties e fundo
                    base_amount = total_sales - tax_amount
                    # 3. Calcula royalties e fundo sobre a base
                    royalty_amount = base_amount * (royalty_rate / 100)
                    ad_fund_amount = base_amount * (ad_fund_rate / 100)
                    # 4. Calcula subtotal e total
                    subtotal = royalty_amount + ad_fund_amount
                    total_amount = subtotal + tax_amount
                    # 5. Conversão para USD
                    amount_usd = total_amount / exchange_rate
                    
                    # Gerar número da fatura
                    invoice_number = generate_invoice_number(country, partner)
                    
                    # Criar dados da fatura
                    invoice_data = {
                        'partner': partner,
                        'country': country,
                        'invoice_category': invoice_category,  # Adicionando categoria de fatura
                        'month': month,
                        'year': year,
                        'month_name': month_name,
                        'total_sales': total_sales,
                        'total_sell_out': total_sales,
                        'royalty_rate': royalty_rate / 100,  # Dividir por 100 para armazenar como decimal
                        'royalty_amount': royalty_amount,
                        'ad_fund_rate': ad_fund_rate / 100,  # Dividir por 100 para armazenar como decimal
                        'ad_fund_amount': ad_fund_amount,
                        'subtotal': subtotal,
                        'tax_rate': tax_rate / 100,  # Dividir por 100 para armazenar como decimal
                        'tax_amount': tax_amount,
                        'total_amount': total_amount,
                        'amount_usd': amount_usd,
                        'currency': currency,
                        'exchange_rate': exchange_rate,
                        'invoice_number': invoice_number,
                        'issue_date': issue_date,
                        'due_date': due_date,  # Adicionando a data de vencimento
                        'created_at': datetime.now(),
                        'sent': False,
                        'paid': False,
                        'payment_amount': 0,
                        'notes': notes,
                        'due_status': 'A Vencer'  # Status inicial
                    }
                    
                    # Adicionar informações de parcelamento, se habilitado
                    if enable_installments and installments_data:
                        invoice_data['installments'] = installments_data
                    
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
            
            # Mostrar data de emissão e vencimento
            if 'issue_date' in invoice and invoice['issue_date']:
                issue_date = invoice['issue_date']
                if isinstance(issue_date, datetime):
                    issue_date_str = issue_date.strftime('%d/%m/%Y')
                else:
                    issue_date_str = issue_date.strftime('%d/%m/%Y') if hasattr(issue_date, 'strftime') else str(issue_date)
                st.markdown(f"**Data de Emissão:** {issue_date_str}")
            else:
                st.markdown(f"**Data de Emissão:** {invoice['created_at'].strftime('%d/%m/%Y')}")
            
            # Mostrar data de vencimento (se não tiver parcelamento)
            if 'due_date' in invoice and invoice['due_date'] and ('installments' not in invoice or not invoice['installments']):
                due_date = invoice['due_date']
                if isinstance(due_date, datetime):
                    due_date_str = due_date.strftime('%d/%m/%Y')
                else:
                    due_date_str = due_date.strftime('%d/%m/%Y') if hasattr(due_date, 'strftime') else str(due_date)
                st.markdown(f"**Data de Vencimento:** {due_date_str}")
                
            st.markdown(f"**Parceiro:** {invoice['partner']}")
            
            # Mapeamento de códigos de país para nomes completos (atualizados para 3 letras)
            country_names = {
                'BRA': 'Brasil',
                'USA': 'Estados Unidos',
                'ESP': 'Espanha',
                'PRT': 'Portugal',
                'MEX': 'México',
                'COL': 'Colômbia',
                'ARG': 'Argentina',
                'CHL': 'Chile',
                'PER': 'Peru',
                'ITA': 'Itália',
                'GBR': 'Reino Unido',
                'FRA': 'França',
                'DEU': 'Alemanha',
                'AUS': 'Austrália',
                'NZL': 'Nova Zelândia',
                'JPN': 'Japão',
                'CHN': 'China',
                'ARE': 'Emirados Árabes Unidos',
                'SAU': 'Arábia Saudita',
                'KWT': 'Kuwait',
                'QAT': 'Qatar',
                # Também mantemos a compatibilidade com códigos de 2 letras
                'BR': 'Brasil',
                'US': 'Estados Unidos',
                'ES': 'Espanha',
                'PT': 'Portugal',
                'MX': 'México',
                'CO': 'Colômbia',
                'AR': 'Argentina',
                'CL': 'Chile',
                'PE': 'Peru',
                'IT': 'Itália',
                'UK': 'Reino Unido',
                'FR': 'França',
                'DE': 'Alemanha',
                'AU': 'Austrália',
                'NZ': 'Nova Zelândia',
                'JP': 'Japão',
                'CN': 'China',
                'AE': 'Emirados Árabes Unidos',
                'SA': 'Arábia Saudita',
                'KW': 'Kuwait',
                'QA': 'Qatar',
            }
            
            # Obtém o nome completo do país ou usa o código se não estiver no mapeamento
            country_code = invoice['country']
            country_name = country_names.get(country_code, country_code)
            st.markdown(f"**País:** {country_name}")
            
            # Mostrar categoria da fatura
            if 'invoice_category' in invoice:
                st.markdown(f"**Categoria:** {invoice['invoice_category']}")
                
            st.markdown(f"**Período:** {invoice['month_name']} {invoice['year']}")
            
            # Separador
            st.markdown("<hr>", unsafe_allow_html=True)
            
            # Valores
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Cálculos:**")
                st.markdown(f"Vendas: {invoice['currency']} {invoice['total_sales']:,.2f}")
                st.markdown(f"Royalties ({invoice['royalty_rate']*100:.1f}%): {invoice['currency']} {invoice['royalty_amount']:,.2f}")
                st.markdown(f"Fundo ({invoice['ad_fund_rate']*100:.1f}%): {invoice['currency']} {invoice['ad_fund_amount']:,.2f}")
                st.markdown(f"Impostos ({invoice['tax_rate']*100:.1f}%): {invoice['currency']} {invoice['tax_amount']:,.2f}")
            
            with col2:
                st.markdown("**Totais:**")
                st.markdown(f"Total: {invoice['currency']} {invoice['total_amount']:,.2f}")
                st.markdown(f"Total USD: $ {invoice['amount_usd']:,.2f}")
                st.markdown(f"Taxa de Câmbio: {invoice['exchange_rate']}")
                st.markdown(f"Status: {invoice['due_status']}")
                
            # Mostrar informações de parcelamento se disponíveis
            if 'installments' in invoice and invoice['installments']:
                st.markdown("<hr>", unsafe_allow_html=True)
                st.markdown("**Plano de Parcelamento:**")
                
                for i, installment in enumerate(invoice['installments']):
                    due_date = installment['due_date']
                    due_date_str = due_date.strftime('%d/%m/%Y') if hasattr(due_date, 'strftime') else str(due_date)
                    st.markdown(f"Parcela {i+1}: {invoice['currency']} {installment['amount']:,.2f} - Vencimento: {due_date_str}")
            
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
        # Mapeamento de códigos de país para nomes completos (atualizados para 3 letras)
        country_names = {
            'BRA': 'Brasil',
            'USA': 'Estados Unidos',
            'ESP': 'Espanha',
            'PRT': 'Portugal',
            'MEX': 'México',
            'COL': 'Colômbia',
            'ARG': 'Argentina',
            'CHL': 'Chile',
            'PER': 'Peru',
            'ITA': 'Itália',
            'GBR': 'Reino Unido',
            'FRA': 'França',
            'DEU': 'Alemanha',
            'AUS': 'Austrália',
            'NZL': 'Nova Zelândia',
            'JPN': 'Japão',
            'CHN': 'China',
            'ARE': 'Emirados Árabes Unidos',
            'SAU': 'Arábia Saudita',
            'KWT': 'Kuwait',
            'QAT': 'Qatar',
            # Também mantemos a compatibilidade com códigos de 2 letras
            'BR': 'Brasil',
            'US': 'Estados Unidos',
            'ES': 'Espanha',
            'PT': 'Portugal',
            'MX': 'México',
            'CO': 'Colômbia',
            'AR': 'Argentina',
            'CL': 'Chile',
            'PE': 'Peru',
            'IT': 'Itália',
            'UK': 'Reino Unido',
            'FR': 'França',
            'DE': 'Alemanha',
            'AU': 'Austrália',
            'NZ': 'Nova Zelândia',
            'JP': 'Japão',
            'CN': 'China',
            'AE': 'Emirados Árabes Unidos',
            'SA': 'Arábia Saudita',
            'KW': 'Kuwait',
            'QA': 'Qatar',
        }
            
        invoices_df = pd.DataFrame([
            {
                "Fatura #": inv['invoice_number'],
                "Parceiro": inv['partner'],
                "País": country_names.get(inv['country'], inv['country']),  # Nome completo do país
                "Categoria": inv.get('invoice_category', 'Royaltie'),  # Valor padrão para faturas antigas
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
