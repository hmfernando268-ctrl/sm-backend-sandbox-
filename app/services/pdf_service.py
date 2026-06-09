"""
Genera recetas médicas en PDF usando ReportLab puro.
Sin dependencias de sistema, funciona en Windows sin configuración extra.
"""
import json
import io
from datetime import datetime


def generar_receta_html(doctor, paciente, receta, medicamentos: list) -> dict:
    """Retorna un dict con los datos estructurados para el PDF."""
    return {
        "doctor": f"Dr. {doctor.nombre} {doctor.apellido}",
        "cedula": doctor.cedula_profesional or "N/A",
        "especialidad": doctor.especialidad or "Médico General",
        "consultorio": doctor.consultorio.nombre,
        "paciente": f"{paciente.nombre} {paciente.apellido}",
        "fecha": datetime.now().strftime("%d/%m/%Y"),
        "folio": f"RX-{str(receta.id)[:8].upper()}",
        "diagnostico": receta.diagnostico,
        "medicamentos": medicamentos,
        "indicaciones": receta.indicaciones or "",
    }


def html_a_pdf(datos) -> bytes:
    """
    Genera PDF a partir del dict de datos.
    Si recibe string HTML (compatibilidad), lo maneja también.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    # Si viene como string HTML (llamada legacy), crear datos mínimos
    if isinstance(datos, str):
        datos = {
            "doctor": "Doctor", "cedula": "N/A", "especialidad": "General",
            "consultorio": "Consultorio", "paciente": "Paciente",
            "fecha": datetime.now().strftime("%d/%m/%Y"), "folio": "RX-00000000",
            "diagnostico": "Ver receta", "medicamentos": [], "indicaciones": "",
        }

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    AZUL = colors.HexColor('#0284c7')
    AZUL_CLARO = colors.HexColor('#eff6ff')
    GRIS = colors.HexColor('#64748b')
    GRIS_CLARO = colors.HexColor('#f8fafc')
    BORDE = colors.HexColor('#e2e8f0')

    story = []

    # ── ENCABEZADO ────────────────────────────────────────────
    header_data = [[
        Paragraph(f"<font color='#0284c7' size='16'><b>{datos['doctor']}</b></font><br/>"
                  f"<font color='#64748b' size='9'>Cédula: {datos['cedula']} | {datos['especialidad']}</font><br/>"
                  f"<font color='#64748b' size='9'>{datos['consultorio']}</font>",
                  ParagraphStyle('h', fontName='Helvetica', leading=16)),
        Paragraph("❤", ParagraphStyle('logo', fontSize=28, textColor=AZUL, alignment=TA_RIGHT)),
    ]]
    header_table = Table(header_data, colWidths=[14*cm, 3*cm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=AZUL, spaceAfter=12))

    # ── META: paciente / fecha / folio ────────────────────────
    meta_data = [
        [
            Paragraph("<font size='8' color='#94a3b8'>PACIENTE</font>", ParagraphStyle('ml')),
            Paragraph("<font size='8' color='#94a3b8'>FECHA</font>", ParagraphStyle('ml')),
            Paragraph("<font size='8' color='#94a3b8'>FOLIO</font>", ParagraphStyle('ml')),
        ],
        [
            Paragraph(f"<b>{datos['paciente']}</b>", ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=11)),
            Paragraph(f"<b>{datos['fecha']}</b>", ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=11)),
            Paragraph(f"<b>{datos['folio']}</b>", ParagraphStyle('mv', fontName='Helvetica-Bold', fontSize=11)),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[7*cm, 4*cm, 5*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), GRIS_CLARO),
        ('BOX', (0,0), (-1,-1), 0.5, BORDE),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [GRIS_CLARO]),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    # ── DIAGNÓSTICO ───────────────────────────────────────────
    story.append(Paragraph(
        "<font size='8' color='#94a3b8'><b>DIAGNÓSTICO</b></font>",
        ParagraphStyle('label', spaceAfter=4)
    ))
    diag_table = Table(
        [[Paragraph(datos['diagnostico'], ParagraphStyle('diag', fontSize=11, textColor=colors.HexColor('#1e40af')))]],
        colWidths=[17*cm]
    )
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), AZUL_CLARO),
        ('LEFTPADDING', (0,0), (-1,-1), 12),
        ('RIGHTPADDING', (0,0), (-1,-1), 12),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
        ('LINEAFTER', (0,0), (0,-1), 3, AZUL),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 14))

    # ── MEDICAMENTOS ──────────────────────────────────────────
    story.append(Paragraph(
        "<font size='8' color='#94a3b8'><b>MEDICAMENTOS PRESCRITOS</b></font>",
        ParagraphStyle('label', spaceAfter=4)
    ))

    meds = datos.get('medicamentos', [])
    if meds:
        med_data = [[
            Paragraph('<b>Medicamento</b>', ParagraphStyle('th', textColor=colors.white, fontSize=10)),
            Paragraph('<b>Dosis</b>', ParagraphStyle('th', textColor=colors.white, fontSize=10)),
            Paragraph('<b>Frecuencia</b>', ParagraphStyle('th', textColor=colors.white, fontSize=10)),
            Paragraph('<b>Duración</b>', ParagraphStyle('th', textColor=colors.white, fontSize=10)),
        ]]
        for i, m in enumerate(meds):
            bg = colors.white if i % 2 == 0 else GRIS_CLARO
            med_data.append([
                Paragraph(f"<b>{m.get('nombre','')}</b>", ParagraphStyle('td', fontSize=10)),
                Paragraph(m.get('dosis',''), ParagraphStyle('td', fontSize=10, textColor=GRIS)),
                Paragraph(m.get('frecuencia',''), ParagraphStyle('td', fontSize=10, textColor=GRIS)),
                Paragraph(m.get('duracion','—'), ParagraphStyle('td', fontSize=10, textColor=GRIS)),
            ])

        med_table = Table(med_data, colWidths=[6*cm, 3.5*cm, 4.5*cm, 3*cm])
        row_bgs = [('BACKGROUND', (0, i+1), (-1, i+1),
                    colors.white if i % 2 == 0 else GRIS_CLARO) for i in range(len(meds))]
        med_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), AZUL),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, BORDE),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ] + row_bgs))
        story.append(med_table)
    else:
        story.append(Paragraph("Sin medicamentos prescritos.", ParagraphStyle('nd', textColor=GRIS, fontSize=10)))

    # ── INDICACIONES ──────────────────────────────────────────
    if datos.get('indicaciones'):
        story.append(Spacer(1, 14))
        story.append(Paragraph(
            "<font size='8' color='#94a3b8'><b>INDICACIONES ESPECIALES</b></font>",
            ParagraphStyle('label', spaceAfter=4)
        ))
        ind_table = Table(
            [[Paragraph(datos['indicaciones'], ParagraphStyle('ind', fontSize=10, textColor=colors.HexColor('#92400e')))]],
            colWidths=[17*cm]
        )
        ind_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fefce8')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#fde68a')),
            ('PADDING', (0,0), (-1,-1), 10),
        ]))
        story.append(ind_table)

    # ── FIRMA ─────────────────────────────────────────────────
    story.append(Spacer(1, 30))
    firma_data = [[
        Paragraph(
            f"<font size='9' color='#94a3b8'>Documento generado electrónicamente<br/>{datos['fecha']} — Sistema Médico Digital</font>",
            ParagraphStyle('footer', fontSize=9)
        ),
        Paragraph(
            f"<font size='9' color='#64748b'>________________________<br/><b>{datos['doctor']}</b><br/>Cédula: {datos['cedula']}</font>",
            ParagraphStyle('firma', fontSize=9, alignment=TA_CENTER)
        ),
    ]]
    firma_table = Table(firma_data, colWidths=[9*cm, 8*cm])
    firma_table.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('LINEABOVE', (0,0), (-1,-1), 0.5, BORDE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(firma_table)

    doc.build(story)
    return buffer.getvalue()