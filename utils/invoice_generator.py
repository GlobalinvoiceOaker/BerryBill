import os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import streamlit as st
import base64
import io
import pandas as pd
from svglib.svglib import svg2rlg
from utils.exchange_rate import get_bc_exchange_rate

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
    
    # Logo da empresa (se existir)
    logo_path = 'assets/logo_header.svg'
    if os.path.exists(logo_path):
        # Converter SVG para objeto ReportLab
        logo_drawing = svg2rlg(logo_path)
        # Redimensionar se necessário
        logo_drawing.width = 2 * inch
        logo_drawing.height = 0.8 * inch
        # Adicionar ao documento
        elements.append(Image(logo_drawing, width=2*inch, height=0.8*inch))
        elements.append(Spacer(1, 0.15 * inch))
    
    # Título
    elements.append(Paragraph("FATURA", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    # Determinar datas de emissão e vencimento
    if 'issue_date' in invoice_data and invoice_data['issue_date']:
        issue_date = invoice_data['issue_date']
        if isinstance(issue_date, str):
            issue_date = datetime.strptime(issue_date, '%Y-%m-%d')
    else:
        issue_date = datetime.now()
        
    # Se houver parcelas, usamos a data da primeira parcela como vencimento
    if 'installments' in invoice_data and invoice_data['installments']:
        first_installment = invoice_data['installments'][0]
        due_date = first_installment['due_date']
        if isinstance(due_date, str):
            due_date = datetime.strptime(due_date, '%Y-%m-%d')
    else:
        # Caso contrário, usamos o padrão de 30 dias após a emissão
        due_date = issue_date + timedelta(days=30)
    
    # Formatação das datas para exibição
    issue_date_str = issue_date.strftime("%d/%m/%Y")
    due_date_str = due_date.strftime("%d/%m/%Y")
    
    # Tabela de informações da fatura
    invoice_data_items = [
        ["Número da Fatura:", invoice_data['invoice_number']],
        ["Data de Emissão:", issue_date_str],
        ["Data de Vencimento:", due_date_str],
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
        ["OAKBERRY AÇAI INC.", invoice_data['partner']],
        ["120 NW 25th Street, Ste 202", "Endereço do Parceiro Linha 1"],
        ["Miami, Florida 33127", "Cidade do Parceiro, Estado, CEP"],
        ["United States", invoice_data['country']]
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
    
    # Adicionar linha com valor em USD
    if 'amount_usd' in invoice_data:
        summary_data.append(["Total (USD)", "", "", f"$ {invoice_data['amount_usd']:,.2f}"])
    
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
    
    # Mostrar informações de parcelamento, se houverem
    if 'installments' in invoice_data and invoice_data['installments'] and len(invoice_data['installments']) > 0:
        elements.append(Paragraph("Plano de Parcelamento", header_style))
        elements.append(Spacer(1, 0.15 * inch))
        
        # Cabeçalho da tabela de parcelamento
        installment_data = [
            ["Parcela", "Vencimento", f"Valor ({invoice_data['currency']})"]
        ]
        
        # Adicionar cada parcela
        for i, installment in enumerate(invoice_data['installments']):
            due_date = installment['due_date']
            if isinstance(due_date, datetime):
                due_date_str = due_date.strftime("%d/%m/%Y")
            else:
                due_date_str = due_date
                
            installment_data.append([
                f"{i+1}/{len(invoice_data['installments'])}",
                due_date_str,
                f"{installment['amount']:,.2f}"
            ])
        
        # Criar e estilizar tabela de parcelamento
        installment_table = Table(installment_data, colWidths=[1.5*inch, 1.5*inch, 3*inch])
        installment_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4A1F60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.lightgrey)
        ]))
        
        elements.append(installment_table)
        elements.append(Spacer(1, 0.5 * inch))
    
    # Informações de pagamento
    elements.append(Paragraph("Informações de Pagamento", header_style))
    elements.append(Spacer(1, 0.15 * inch))
    
    payment_info = [
        ["Nome do Banco:", "Ebury Partners Belgium NV"],
        ["Nome da Conta:", "Oakberry Acai INC"],
        ["BIC/SWIFT:", "EBPBESM2"],
        ["IBAN:", "ES6568890001715897335238"],
        ["Endereço do Banco:", "Paseo de la Castellana, 202, Madrid, Spain"]
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
    1. O pagamento deve ser feito conforme as datas de vencimento indicadas.
    2. Por favor, inclua o número da fatura na referência do seu pagamento.
    3. Para dúvidas sobre esta fatura, entre em contato com financeiro@oakberry.com.
    4. Contas em atraso estão sujeitas a juros de 1% ao mês.
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
