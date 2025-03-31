import streamlit as st
import base64
import os
from PIL import Image

# Caminho para a imagem do logo
LOGO_PATH = 'assets/images/oakberry_logo.jpg'

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode('utf-8')

def get_logo_html(width=300):
    # Verifica se o arquivo do logo existe
    if os.path.isfile(LOGO_PATH):
        # Usa a imagem OAKBERRY como logo
        logo_html = f"""
        <div style="text-align: center; margin-bottom: 10px;">
            <img src="data:image/jpeg;base64,{get_image_base64(LOGO_PATH)}" width="{width}px" alt="OAKBERRY Logo">
        </div>
        """
        return logo_html
    else:
        # Cor principal do app
        primary_color = "#4A1F60"
        
        # HTML/CSS para criar um logotipo simples como fallback
        logo_html = f"""
        <div style="
            background-color: {primary_color}; 
            color: white; 
            border-radius: 10px; 
            padding: 20px; 
            display: flex; 
            align-items: center;
            width: {width}px;
            ">
            <div style="
                background-color: white; 
                width: 60px; 
                height: 80px; 
                border-radius: 5px; 
                display: flex; 
                flex-direction: column; 
                justify-content: space-between; 
                padding: 10px;
                margin-right: 15px;
                ">
                <div style="height: 8px; background-color: {primary_color}; border-radius: 2px;"></div>
                <div style="height: 8px; background-color: {primary_color}; border-radius: 2px;"></div>
                <div style="height: 8px; background-color: {primary_color}; border-radius: 2px; width: 70%;"></div>
                <div style="height: 15px; background-color: {primary_color}; border-radius: 2px; opacity: 0.7;"></div>
            </div>
            <div>
                <div style="font-size: 24px; font-weight: bold;">Invoice Manager</div>
                <div style="font-size: 16px;">Sistema de Faturas</div>
            </div>
        </div>
        """
        return logo_html

def render_logo(width=300):
    if os.path.isfile(LOGO_PATH):
        try:
            # Usar st.image é mais eficiente para imagens
            img = Image.open(LOGO_PATH)
            st.image(img, width=width)
        except Exception:
            # Fallback para HTML se o carregamento da imagem falhar
            logo_html = get_logo_html(width)
            st.markdown(logo_html, unsafe_allow_html=True)
    else:
        logo_html = get_logo_html(width)
        st.markdown(logo_html, unsafe_allow_html=True)

def get_icon_html(size=50):
    # Verifica se o arquivo do logo existe
    if os.path.isfile(LOGO_PATH):
        # Usa a imagem OAKBERRY como ícone
        icon_html = f"""
        <div style="text-align: center;">
            <img src="data:image/jpeg;base64,{get_image_base64(LOGO_PATH)}" width="{size}px" height="{size}px" 
                 style="border-radius: 50%; object-fit: cover;" alt="OAKBERRY Icon">
        </div>
        """
        return icon_html
    else:
        # Cor principal do app
        primary_color = "#4A1F60"
        
        # HTML/CSS para criar um ícone simples como fallback
        icon_html = f"""
        <div style="
            background-color: {primary_color}; 
            width: {size}px; 
            height: {size}px; 
            border-radius: 50%; 
            display: flex; 
            align-items: center; 
            justify-content: center;
            ">
            <div style="
                background-color: white; 
                width: {int(size*0.6)}px; 
                height: {int(size*0.8)}px; 
                border-radius: 3px; 
                position: relative;
                ">
                <div style="
                    position: absolute; 
                    top: 20%; 
                    left: 20%; 
                    right: 20%; 
                    height: 2px; 
                    background-color: {primary_color};
                    "></div>
                <div style="
                    position: absolute; 
                    top: 40%; 
                    left: 20%; 
                    right: 20%; 
                    height: 2px; 
                    background-color: {primary_color};
                    "></div>
                <div style="
                    position: absolute; 
                    top: 60%; 
                    left: 20%; 
                    right: 40%; 
                    height: 2px; 
                    background-color: {primary_color};
                    "></div>
            </div>
        </div>
        """
        return icon_html

def render_icon(size=50):
    if os.path.isfile(LOGO_PATH):
        try:
            # Usar st.image é mais eficiente para imagens
            img = Image.open(LOGO_PATH)
            st.image(img, width=size)
        except Exception:
            # Fallback para HTML se o carregamento da imagem falhar
            icon_html = get_icon_html(size)
            st.markdown(icon_html, unsafe_allow_html=True)
    else:
        icon_html = get_icon_html(size)
        st.markdown(icon_html, unsafe_allow_html=True)