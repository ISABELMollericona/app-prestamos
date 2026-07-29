"""
Generación automatizada de documentos de préstamo
Contratos, cronogramas, vouchers de pago
"""
from io import BytesIO
from datetime import datetime
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, Image, PageBreak)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT


def generar_cronograma_pagos(prestamo, amortizaciones):
    """Genera PDF con el cronograma de pagos"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=20*mm, bottomMargin=15*mm,
                             leftMargin=15*mm, rightMargin=15*mm)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Titulo', parent=styles['Title'],
                                  fontSize=16, spaceAfter=6,
                                  textColor=HexColor('#1a237e'))
    subtitle_style = ParagraphStyle('Subtitulo', parent=styles['Normal'],
                                     fontSize=10, spaceAfter=4,
                                     textColor=HexColor('#424242'))
    header_style = ParagraphStyle('Header', parent=styles['Normal'],
                                   fontSize=8, textColor=HexColor('#ffffff'))

    elements = []

    elements.append(Paragraph('MICREDIT - Microfinanzas', title_style))
    elements.append(Paragraph('CRONOGRAMA DE PAGOS', subtitle_style))
    elements.append(Spacer(1, 10*mm))

    info_data = [
        ['Cliente:', prestamo.cliente.nombre_completo],
        ['Documento:', f"{prestamo.cliente.tipo_documento}: {prestamo.cliente.numero_documento}"],
        ['Código Préstamo:', prestamo.codigo_prestamo],
        ['Monto Aprobado:', f"Bs {float(prestamo.monto_aprobado):,.2f}"],
        ['Tasa:', f"{float(prestamo.tasa_interes_valor or 0) * 100:.2f}% {prestamo.tipo_tasa or 'mensual'}"],
        ['Plazo:', f"{prestamo.plazo_meses} meses"],
        ['Cuota:', f"Bs {float(prestamo.monto_cuota or 0):,.2f}"],
        ['Frecuencia:', prestamo.frecuencia_pago.capitalize()],
        ['Método:', 'Francés (Cuota Fija)' if prestamo.metodo_amortizacion == 'frances' else 'Americano (Solo Intereses)' if prestamo.metodo_amortizacion == 'americano' else 'Alemán (Amortización Constante)'],
        ['Fecha Desembolso:', prestamo.fecha_desembolso.strftime('%d/%m/%Y') if prestamo.fecha_desembolso else '-'],
    ]

    info_table = Table(info_data, colWidths=[120, 300])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8*mm))

    headers = ['N°', 'Vencimiento', 'Saldo Inicial', 'Cuota', 'Interés',
               'Amortización', 'Seguro', 'Total', 'Saldo Final']
    col_widths = [20, 60, 65, 55, 55, 60, 45, 55, 65]

    data = [headers]
    for a in amortizaciones:
        data.append([
            str(a.numero_cuota),
            a.fecha_vencimiento.strftime('%d/%m/%Y'),
            f"Bs {float(a.saldo_inicial or 0):,.2f}",
            f"Bs {float(a.monto_cuota or 0):,.2f}",
            f"Bs {float(a.interes or 0):,.2f}",
            f"Bs {float(a.amortizacion or 0):,.2f}",
            f"Bs {float(a.seguro_desgravamen or 0):,.2f}",
            f"Bs {float(a.total_cuota or 0):,.2f}",
            f"Bs {float(a.saldo_final or 0):,.2f}",
        ])

    amort_table = Table(data, colWidths=col_widths, repeatRows=1)
    amort_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1a237e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, HexColor('#f5f5f5')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(amort_table)

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f'Generado el: {datetime.now().strftime("%d/%m/%Y %H:%M")}', subtitle_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def _build_contrato_base(doc, prestamo, titulo, tipo_doc):
    """Construye las primeras secciones comunes de un contrato de prestamo"""
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Titulo', parent=styles['Title'],
                                  fontSize=14, spaceAfter=6,
                                  textColor=HexColor('#1a237e'))
    normal_style = ParagraphStyle('NormalDoc', parent=styles['Normal'],
                                   fontSize=10, spaceAfter=4, leading=14)
    bold_style = ParagraphStyle('BoldDoc', parent=normal_style,
                                 fontName='Helvetica-Bold')

    elements = []
    elements.append(Paragraph('MICREDIT - Microfinanzas', title_style))
    elements.append(Paragraph(titulo, ParagraphStyle(
        'Subt', parent=styles['Normal'], fontSize=12,
        textColor=HexColor('#1a237e'), spaceAfter=12)))
    elements.append(Spacer(1, 8*mm))

    c = prestamo.cliente
    fecha_actual = datetime.now().strftime('%d/%m/%Y')
    monto_str = f"Bs {float(prestamo.monto_aprobado or prestamo.monto_solicitado):,.2f}"
    tasa_str = f"{float(prestamo.tasa_interes_valor or 0) * 100:.2f}% {prestamo.tipo_tasa or 'mensual'}"

    clausulas = [
        f"<b>PRIMERO.- (PARTES INTERVINIENTES).-</b> El presente {tipo_doc} se celebra entre <b>{c.nombre_completo}</b>, identificado con {c.tipo_documento} Nro. {c.numero_documento}, con domicilio en {c.direccion or 'la ciudad'}, en adelante EL DEUDOR; y MICREDIT S.R.L., en adelante EL ACREEDOR.",
        f"<b>SEGUNDO.- (OBJETO).-</b> EL ACREEDOR otorga un prestamo a EL DEUDOR por la suma de {monto_str}, que el deudor se obliga a devolver en {prestamo.plazo_meses} meses, con una tasa de interes de {tasa_str}, bajo el sistema de amortizacion {prestamo.metodo_amortizacion}, conforme al cronograma de pagos adjunto.",
        f"<b>TERCERO.- (FORMA DE PAGO).-</b> EL DEUDOR se obliga a pagar cuotas {prestamo.frecuencia_pago} por el monto de Bs {float(prestamo.monto_cuota or 0):,.2f}, los dias de vencimiento establecidos en el cronograma.",
        f"<b>CUARTO.- (INTERESES Y MORA).-</b> En caso de mora, EL DEUDOR pagara un interes moratorio del 0.5% diario sobre el monto de la cuota impaga.",
        f"<b>QUINTO.- (DOMICILIO).-</b> Las partes senalan como sus domicilios los indicados en la clausula primera, donde se realizaran las notificaciones.",
        f"<b>SEXTO.- (JURISDICCION).-</b> Las partes se someten a la jurisdiccion de los tribunales de la ciudad.",
    ]

    for clausula in clausulas:
        elements.append(Paragraph(clausula, normal_style))
        elements.append(Spacer(1, 3*mm))

    elements.append(Spacer(1, 10*mm))
    elements.append(Paragraph(f'Firmado en la ciudad, a los {datetime.now().day} dias del mes de {datetime.now().strftime("%B")} de {datetime.now().year}.', normal_style))
    elements.append(Spacer(1, 8*mm))

    firma_data = [
        ['____________________________', '____________________________'],
        [c.nombre_completo, 'MICREDIT S.R.L.'],
        ['DEUDOR', 'ACREEDOR'],
    ]
    firma_table = Table(firma_data, colWidths=[220, 220])
    firma_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(firma_table)

    return elements


def generar_contrato_prenda_venta(prestamo):
    """Contrato de Venta con Pacto de Rescate - Garantia Prendaria"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=20*mm, bottomMargin=15*mm,
                             leftMargin=20*mm, rightMargin=20*mm)
    elements = _build_contrato_base(
        doc, prestamo,
        'CONTRATO DE VENTA CON PACTO DE RESCATE',
        'Contrato de Venta con Pacto de Rescate'
    )
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_contrato_prenda_dacion(prestamo):
    """Dacion en Pago - Garantia Prendaria"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=20*mm, bottomMargin=15*mm,
                             leftMargin=20*mm, rightMargin=20*mm)
    elements = _build_contrato_base(
        doc, prestamo,
        'CONTRATO DE DACION EN PAGO',
        'Contrato de Dacion en Pago'
    )
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_contrato_prenda_garantia(prestamo):
    """Prestamo con Garantia Prendaria"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=20*mm, bottomMargin=15*mm,
                             leftMargin=20*mm, rightMargin=20*mm)
    elements = _build_contrato_base(
        doc, prestamo,
        'CONTRATO DE PRESTAMO CON GARANTIA PRENDARIA',
        'Contrato de Prestamo con Garantia Prendaria'
    )
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generar_voucher_pago(pago, cuotas):
    """Genera comprobante de pago"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             topMargin=15*mm, bottomMargin=15*mm,
                             leftMargin=15*mm, rightMargin=15*mm)

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph('MICREDIT - Microfinanzas', ParagraphStyle(
        'Titulo', parent=styles['Title'], fontSize=14, textColor=HexColor('#1a237e'))))
    elements.append(Paragraph('COMPROBANTE DE PAGO', ParagraphStyle(
        'Subt', parent=styles['Normal'], fontSize=11, spaceAfter=10)))
    elements.append(Spacer(1, 5*mm))

    info = [
        ['Código:', pago.codigo_pago],
        ['Cliente:', pago.cliente.nombre_completo],
        ['Préstamo:', pago.prestamo.codigo_prestamo],
        ['Monto Total:', f"Bs {float(pago.monto_total):,.2f}"],
        ['Cuotas Pagadas:', ', '.join(str(c.numero_cuota) for c in cuotas)],
        ['Método:', pago.metodo_pago.capitalize()],
        ['Fecha:', pago.fecha_pago.strftime('%d/%m/%Y %H:%M')],
    ]

    t = Table(info, colWidths=[100, 350])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    elements.append(t)

    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph('¡Gracias por su pago!', ParagraphStyle(
        'Gracias', parent=styles['Normal'], fontSize=11, alignment=TA_CENTER,
        textColor=HexColor('#2e7d32'))))

    doc.build(elements)
    buffer.seek(0)
    return buffer
