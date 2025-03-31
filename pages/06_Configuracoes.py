import streamlit as st
import json
import os
from utils.data_processor import load_country_settings, save_country_settings
import pandas as pd

st.set_page_config(
    page_title="Settings - Invoice Management System",
    page_icon="⚙️",
    layout="wide"
)

# Custom styling
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

# Header
st.markdown('<div class="main-header">Settings</div>', unsafe_allow_html=True)
st.markdown('<div class="description">Configure system settings and preferences</div>', unsafe_allow_html=True)

# Country Settings
st.markdown('<div class="sub-header">Country Settings</div>', unsafe_allow_html=True)
st.markdown("Configure royalty rates, ad fund rates, and tax rates for each country")

# Load current settings
country_settings = load_country_settings()

# Mapeamento de códigos de país para nomes completos
country_names = {
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

# Convert to DataFrame for easier editing
settings_data = []
for country_code, rates in country_settings.items():
    # Obter nome completo do país ou usar o código se não estiver no mapeamento
    country_name = country_names.get(country_code, country_code)
    settings_data.append({
        "Country Code": country_code,  # Mantendo o código para uso interno
        "Country": country_name,      # Nome completo para exibição
        "Royalty Rate (%)": rates["royalty_rate"] * 100,
        "Ad Fund Rate (%)": rates["ad_fund_rate"] * 100,
        "Tax Rate (%)": rates["tax_rate"] * 100
    })

settings_df = pd.DataFrame(settings_data)

# Edit settings
edited_df = st.data_editor(
    settings_df,
    use_container_width=True,
    column_config={
        "Country Code": st.column_config.TextColumn("Country Code", disabled=True),
        "Country": st.column_config.TextColumn("Country Name", disabled=True),
        "Royalty Rate (%)": st.column_config.NumberColumn(
            "Royalty Rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f %%"
        ),
        "Ad Fund Rate (%)": st.column_config.NumberColumn(
            "Ad Fund Rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f %%"
        ),
        "Tax Rate (%)": st.column_config.NumberColumn(
            "Tax Rate (%)",
            min_value=0.0,
            max_value=100.0,
            step=0.1,
            format="%.1f %%"
        )
    },
    num_rows="dynamic"
)

# Add new country
with st.expander("Add New Country"):
    with st.form("add_country_form"):
        new_country = st.text_input("Country Code (2-3 letters)", max_chars=3)
        new_royalty = st.number_input("Royalty Rate (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)
        new_ad_fund = st.number_input("Ad Fund Rate (%)", min_value=0.0, max_value=100.0, value=2.0, step=0.1)
        new_tax = st.number_input("Tax Rate (%)", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
        
        add_country = st.form_submit_button("Add Country")
        
        if add_country and new_country:
            # Check if country already exists
            if new_country in country_settings:
                st.error(f"Country {new_country} already exists!")
            else:
                # Add new country
                new_country_upper = new_country.upper()
                country_settings[new_country_upper] = {
                    "royalty_rate": new_royalty / 100,
                    "ad_fund_rate": new_ad_fund / 100,
                    "tax_rate": new_tax / 100
                }
                
                # Save settings
                save_country_settings(country_settings)
                
                # Obter o nome completo do país, se disponível
                country_name = country_names.get(new_country_upper, new_country_upper)
                st.success(f"País {country_name} ({new_country_upper}) adicionado com sucesso!")
                st.rerun()

# Save settings button
if st.button("Save Settings"):
    # Update settings from edited DataFrame
    updated_settings = {}
    for _, row in edited_df.iterrows():
        # Importante: Usamos o código do país (não o nome completo) ao salvar as configurações
        country_code = row["Country Code"]
        updated_settings[country_code] = {
            "royalty_rate": row["Royalty Rate (%)"] / 100,
            "ad_fund_rate": row["Ad Fund Rate (%)"] / 100,
            "tax_rate": row["Tax Rate (%)"] / 100
        }
    
    # Save updated settings
    save_country_settings(updated_settings)
    
    st.success("Settings saved successfully!")

# Email Settings
st.markdown('<div class="sub-header">Email Settings</div>', unsafe_allow_html=True)
st.markdown("Configure email server settings for sending invoices")

# Load current email settings
smtp_server = st.text_input(
    "SMTP Server",
    value=st.session_state.get('smtp_server', os.getenv('SMTP_SERVER', ''))
)
smtp_port = st.text_input(
    "SMTP Port",
    value=st.session_state.get('smtp_port', os.getenv('SMTP_PORT', '587'))
)
smtp_username = st.text_input(
    "SMTP Username",
    value=st.session_state.get('smtp_username', os.getenv('SMTP_USERNAME', ''))
)
smtp_password = st.text_input(
    "SMTP Password",
    value=st.session_state.get('smtp_password', os.getenv('SMTP_PASSWORD', '')),
    type="password"
)
sender_email = st.text_input(
    "Sender Email",
    value=st.session_state.get('sender_email', os.getenv('SENDER_EMAIL', ''))
)

# Save email settings
if st.button("Save Email Settings"):
    st.session_state.smtp_server = smtp_server
    st.session_state.smtp_port = smtp_port
    st.session_state.smtp_username = smtp_username
    st.session_state.smtp_password = smtp_password
    st.session_state.sender_email = sender_email
    
    st.success("Email settings saved successfully!")

# System Information
st.markdown('<div class="sub-header">System Information</div>', unsafe_allow_html=True)

# Create expandable sections for different types of info
with st.expander("Data Overview"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        num_invoices = len(st.session_state.invoices) if hasattr(st.session_state, 'invoices') else 0
        st.metric("Total Invoices", num_invoices)
    
    with col2:
        has_imported_data = "Yes" if 'imported_data' in st.session_state and st.session_state.imported_data is not None else "No"
        st.metric("Data Imported", has_imported_data)
    
    with col3:
        num_countries = len(country_settings)
        st.metric("Configured Countries", num_countries)

with st.expander("Reset Application Data"):
    st.warning("⚠️ This will reset all application data. This action cannot be undone.")
    
    if st.button("Reset All Data"):
        # Clear session state
        for key in list(st.session_state.keys()):
            if key != "_is_running":
                del st.session_state[key]
        
        st.success("Application data has been reset.")
        st.rerun()

# Footer
st.markdown("---")
st.markdown("© 2023 Invoice Management System | Powered by Streamlit")
