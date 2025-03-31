import streamlit as st
import base64

def get_logo_html(width=300):
    # Cor principal do app
    primary_color = "#4A1F60"
    
    # HTML/CSS para criar um logotipo simples
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
    logo_html = get_logo_html(width)
    st.markdown(logo_html, unsafe_allow_html=True)

def get_icon_html(size=50):
    # Cor principal do app
    primary_color = "#4A1F60"
    
    # HTML/CSS para criar um ícone simples
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
    icon_html = get_icon_html(size)
    st.markdown(icon_html, unsafe_allow_html=True)