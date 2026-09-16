"""Generación de recibos de pago (rol de pagos) en PDF con ReportLab."""
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)

# Paleta corporativa
AZUL_MARINO = colors.HexColor("#1E3A5F")
GRIS_PERLA = colors.HexColor("#E2E8F0")
VERDE = colors.HexColor("#10B981")


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("Titulo", parent=ss["Title"], textColor=AZUL_MARINO, fontSize=18))
    ss.add(ParagraphStyle("Sub", parent=ss["Normal"], textColor=AZUL_MARINO, fontSize=11, spaceAfter=2))
    ss.add(ParagraphStyle("Small", parent=ss["Normal"], fontSize=9, textColor=colors.HexColor("#334155")))
    return ss


def recibo_pago_pdf(nomina) -> bytes:
    emp = nomina.empleado
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm,
    )
    ss = _styles()
    elems = []

    elems.append(Paragraph("RECIBO DE PAGO / ROL INDIVIDUAL", ss["Titulo"]))
    elems.append(Paragraph(f"Período: {nomina.periodo}", ss["Sub"]))
    elems.append(Spacer(1, 8 * mm))

    info = [
        ["Empleado:", emp.nombre_completo, "Cédula:", emp.cedula],
        ["Departamento:", emp.departamento.nombre if emp.departamento else "-",
         "Cargo:", emp.cargo.nombre if emp.cargo else "-"],
        ["Fecha ingreso:", emp.fecha_ingreso.strftime("%d/%m/%Y"),
         "Días trabajados:", str(nomina.dias_trabajados)],
    ]
    t_info = Table(info, colWidths=[28 * mm, 62 * mm, 28 * mm, 56 * mm])
    t_info.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), AZUL_MARINO),
        ("TEXTCOLOR", (2, 0), (2, -1), AZUL_MARINO),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_PERLA),
        ("BOX", (0, 0), (-1, -1), 0.5, AZUL_MARINO),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.white),
    ]))
    elems.append(t_info)
    elems.append(Spacer(1, 8 * mm))

    # Ingresos y deducciones
    filas = [["CONCEPTO", "INGRESOS", "DEDUCCIONES"]]
    for d in nomina.ingresos:
        filas.append([d.concepto, f"${d.monto:,.2f}", ""])
    for d in nomina.deducciones:
        filas.append([d.concepto, "", f"${d.monto:,.2f}"])
    filas.append(["TOTALES", f"${nomina.total_ingresos:,.2f}", f"${nomina.total_deducciones:,.2f}"])

    t = Table(filas, colWidths=[86 * mm, 44 * mm, 44 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_MARINO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), GRIS_PERLA),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#94A3B8")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#F1F5F9")]),
    ]))
    elems.append(t)
    elems.append(Spacer(1, 8 * mm))

    neto = Table([["NETO A PAGAR", f"${nomina.neto_pagar:,.2f}"]], colWidths=[130 * mm, 44 * mm])
    neto.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), VERDE),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 12),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elems.append(neto)
    elems.append(Spacer(1, 18 * mm))

    firmas = Table([["_______________________", "_______________________"],
                    ["Empleador", "Empleado"]], colWidths=[87 * mm, 87 * mm])
    firmas.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, 1), AZUL_MARINO),
    ]))
    elems.append(firmas)
    elems.append(Spacer(1, 6 * mm))
    elems.append(Paragraph(
        "Documento generado automáticamente por el Sistema de RRHH y Nómina.", ss["Small"]
    ))

    doc.build(elems)
    buffer.seek(0)
    return buffer.read()
