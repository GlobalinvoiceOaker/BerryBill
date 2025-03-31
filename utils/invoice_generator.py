import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import streamlit as st
import base64
import io
import pandas as pd

def create_invoice_pdf(invoice_data):
    """
    Cria um PDF de fatura a partir dos dados fornecidos
    
    Parâmetros:
    - invoice_data: Dicionário contendo informações da fatura
    
    Retorna:
    - bytes: Arquivo PDF como bytes
    """
    buffer = io.BytesIO()
    
    # Cria o PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=inch/2,
        leftMargin=inch/2,
        topMargin=inch/2,
        bottomMargin=inch/2
    )
    
    # Obtém estilos
    styles = getSampleStyleSheet()
    
    # Cria estilos personalizados
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#4A1F60'),
        spaceAfter=12
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#3A174E'),
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=6
    )
    
    # Cria elementos de conteúdo
    elements = []
    
    # Título
    elements.append(Paragraph("FATURA", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Tabela de informações da fatura
    invoice_data_items = [
        ["Número da Fatura:", invoice_data['invoice_number']],
        ["Data:", datetime.now().strftime("%d/%m/%Y")],
        ["Data de Vencimento:", (datetime.now() + pd.Timedelta(days=30)).strftime("%d/%m/%Y")],
        ["Período:", f"{invoice_data['month_name']} {invoice_data['year']}"]
    ]
    
    invoice_table = Table(invoice_data_items, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#3A174E')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Tabela De-Para (informações de faturamento)
    from_to_data = [
        ["De:", "Para:"],
        ["Nome da Sua Empresa", invoice_data['partner']],
        ["Seu Endereço Linha 1", "Endereço do Parceiro Linha 1"],
        ["Sua Cidade, Estado, CEP", "Cidade do Parceiro, Estado, CEP"],
        ["Seu País", invoice_data['country']]
    ]
    
    from_to_table = Table(from_to_data, colWidths=[2.5*inch, 2.5*inch])
    from_to_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#3A174E')),
        ('FONT', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(from_to_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Cabeçalho do resumo
    elements.append(Paragraph("Resumo", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    # Tabela de resumo
    summary_data = [
        ["Descrição", "Taxa", "Valor", f"Valor ({invoice_data['currency']})"],
        ["Total de Vendas", "", "", f"{invoice_data['total_sell_out']:,.2f}"],
        ["Royalties", f"{invoice_data['royalty_rate']*100:.1f}%", "", f"{invoice_data['royalty_amount']:,.2f}"],
        ["Fundo de Publicidade", f"{invoice_data['ad_fund_rate']*100:.1f}%", "", f"{invoice_data['ad_fund_amount']:,.2f}"],
        ["Subtotal", "", "", f"{invoice_data['subtotal']:,.2f}"],
        ["Impostos", f"{invoice_data['tax_rate']*100:.1f}%", "", f"{invoice_data['tax_amount']:,.2f}"],
        ["Total a Pagar", "", "", f"{invoice_data['total_amount']:,.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1.5*inch, 1.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A1F60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F0F0')),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5 * inch))
    
    # Informações de pagamento
    elements.append(Paragraph("Informações de Pagamento", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    payment_info = [
        ["Nome do Banco:", "Nome do Seu Banco"],
        ["Nome da Conta:", "Nome da Sua Empresa"],
        ["Número da Conta:", "XXXX-XXXX-XXXX-XXXX"],
        ["Agência:", "XXXX-X"],
        ["SWIFT/BIC:", "XXXXXXXXXXX"]
    ]
    
    payment_table = Table(payment_info, colWidths=[2*inch, 3*inch])
    payment_table.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#3A174E')),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    
    elements.append(payment_table)
    elements.append(Spacer(1, 0.25 * inch))
    
    # Termos e notas
    elements.append(Paragraph("Termos e Condições", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    terms_text = """
    1. O pagamento deve ser feito dentro de 30 dias da data da fatura.
    2. Por favor, inclua o número da fatura na referência do seu pagamento.
    3. Para dúvidas sobre esta fatura, entre em contato com financeiro@suaempresa.com.br.
    """
    
    elements.append(Paragraph(terms_text, normal_style))
    
    # Constrói o PDF
    doc.build(elements)
    
    # Obtém o PDF do buffer
    buffer.seek(0)
    return buffer.getvalue()

def get_invoice_download_link(invoice_data, link_text="Baixar PDF"):
    """
    Gera um link de download para o PDF da fatura
    
    Parâmetros:
    - invoice_data: Dicionário contendo informações da fatura
    - link_text: Texto a ser exibido para o link de download
    
    Retorna:
    - str: Link HTML para download do PDF
    """
    # Gera o PDF
    pdf = create_invoice_pdf(invoice_data)
    
    # Codifica para base64
    b64 = base64.b64encode(pdf).decode()
    
    # Gera um nome de arquivo seguro
    filename = f"Fatura_{invoice_data['invoice_number']}_{invoice_data['partner']}.pdf"
    filename = filename.replace(" ", "_")
    
    # Cria o link de download
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;padding:10px 15px;background-color:#3A174E;color:white;border-radius:5px;">{link_text}</a>'
    
    return href

def generate_invoices_from_data(data):
    """
    Gera faturas a partir de dados processados
    
    Parâmetros:
    - data: DataFrame contendo dados de venda processados
    
    Retorna:
    - Lista de dicionários de faturas geradas
    """
    from utils.data_processor import group_data_by_partner
    
    # Agrupa dados por parceiro e mês
    grouped_data = group_data_by_partner(data)
    
    # Gera faturas
    generated_invoices = []
    for group in grouped_data:
        invoice = {
            **group,
            'sent': False,
            'paid': False,
            'payment_date': None,
            'payment_amount': 0,
            'pdf': create_invoice_pdf(group)
        }
        generated_invoices.append(invoice)
    
    return generated_invoices
