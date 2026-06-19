"""
Generation de documents PDF (reportlab).

Couvre :
- RF-19 : recu de vente (`build_sale_receipt_pdf`), au format ticket de caisse.
- RF-29 : export de rapports en PDF (`build_dashboard_report_pdf`).
- Rapport credits clients (`build_credits_report_pdf`).
"""
from __future__ import annotations

import io
from datetime import datetime
from decimal import Decimal

from flask import Response, current_app
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, mm
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm as MM
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def pdf_response(buffer: io.BytesIO, filename: str, inline: bool = True) -> Response:
    buffer.seek(0)
    disposition = "inline" if inline else "attachment"
    return Response(
        buffer.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": disposition + "; filename=\"" + filename + "\""},
    )


def _fmt_amount(value) -> str:
    try:
        amount = int(Decimal(str(value)).to_integral_value())
    except Exception:
        amount = int(value or 0)
    return "{:,}".format(amount).replace(",", " ")


# ---------------------------------------------------------------------------
# RF-19 : recu de vente (format ticket de caisse)
# ---------------------------------------------------------------------------

RECEIPT_WIDTH = 80 * mm


def build_sale_receipt_pdf(sale) -> io.BytesIO:
    company_name = current_app.config.get("COMPANY_NAME", "Gescom BF")
    company_address = current_app.config.get("COMPANY_ADDRESS", "")
    company_phone = current_app.config.get("COMPANY_PHONE", "")

    line_count = len(sale.lines)
    height = (78 + line_count * 5) * mm

    buf = io.BytesIO()
    c = pdfcanvas.Canvas(buf, pagesize=(RECEIPT_WIDTH, height))

    width = RECEIPT_WIDTH
    x_center = width / 2
    x_left = 4 * mm
    x_right = width - 4 * mm
    y = height - 6 * mm

    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(x_center, y, company_name)
    y -= 4.5 * mm

    c.setFont("Helvetica", 7)
    if company_address:
        c.drawCentredString(x_center, y, company_address)
        y -= 3.5 * mm
    if company_phone:
        c.drawCentredString(x_center, y, "Tel : " + company_phone)
        y -= 3.5 * mm

    y -= 1.5 * mm
    c.line(x_left, y, x_right, y)
    y -= 4.5 * mm

    c.setFont("Helvetica-Bold", 9)
    title = "AVOIR" if sale.status == "AVOIR_EMIS" else "RECU DE VENTE"
    c.drawCentredString(x_center, y, title)
    y -= 4.5 * mm

    c.setFont("Helvetica", 7)
    created_at = sale.created_at or datetime.utcnow()
    info_rows = [
        "Reference : " + sale.reference,
        "Date : " + created_at.strftime("%d/%m/%Y %H:%M"),
        "Site : " + (sale.branch.name if sale.branch else "-"),
        "Caissier : " + (sale.cashier.full_name if sale.cashier else "-"),
    ]
    if sale.customer:
        info_rows.append("Client : " + sale.customer.full_name)
    if sale.refund_of_sale_id:
        info_rows.append("Avoir sur vente : " + sale.refund_of_sale_id)

    for row in info_rows:
        c.drawString(x_left, y, row)
        y -= 3.5 * mm

    y -= 1.5 * mm
    c.line(x_left, y, x_right, y)
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 7)
    c.drawString(x_left, y, "Article")
    c.drawRightString(width - 26 * mm, y, "Qte")
    c.drawRightString(width - 14 * mm, y, "P.U.")
    c.drawRightString(x_right, y, "Total")
    y -= 3.5 * mm

    c.setFont("Helvetica", 7)
    for line in sale.lines:
        name = line.product.name if line.product else "?"
        if len(name) > 24:
            name = name[:23] + "..."
        c.drawString(x_left, y, name)
        c.drawRightString(width - 26 * mm, y, str(line.quantity))
        c.drawRightString(width - 14 * mm, y, _fmt_amount(line.unit_price_applied))
        c.drawRightString(x_right, y, _fmt_amount(line.line_total))
        y -= 3.5 * mm

    y -= 1.5 * mm
    c.line(x_left, y, x_right, y)
    y -= 4.5 * mm

    c.setFont("Helvetica", 8)
    c.drawString(x_left, y, "Sous-total")
    c.drawRightString(x_right, y, _fmt_amount(sale.subtotal) + " FCFA")
    y -= 4 * mm

    if sale.discount_rate:
        c.drawString(x_left, y, "Remise (" + str(sale.discount_rate) + "%)")
        c.drawRightString(x_right, y, "-" + _fmt_amount(sale.discount_amount) + " FCFA")
        y -= 4 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_left, y, "TOTAL")
    c.drawRightString(x_right, y, _fmt_amount(sale.total) + " FCFA")
    y -= 5 * mm

    c.setFont("Helvetica", 7)
    payment_labels = {
        "CASH": "Especes",
        "MOBILE_MONEY": "Mobile Money",
        "CREDIT": "Credit",
    }
    c.drawString(
        x_left, y, "Mode de paiement : " + payment_labels.get(sale.payment_type, sale.payment_type)
    )
    y -= 4 * mm

    if sale.status == "AVOIR_EMIS":
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x_center, y, "** AVOIR EMIS **")
        y -= 4 * mm

    y -= 1.5 * mm
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(x_center, y, "Merci de votre confiance !")

    c.showPage()
    c.save()
    return buf


# ---------------------------------------------------------------------------
# RF-29 : export de rapports (tableau de bord etendu)
# ---------------------------------------------------------------------------

def build_dashboard_report_pdf(dashboard_data: dict, top_products: list | None = None) -> io.BytesIO:
    company_name = current_app.config.get("COMPANY_NAME", "Gescom BF")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * MM,
        rightMargin=18 * MM,
        topMargin=16 * MM,
        bottomMargin=16 * MM,
        title="Rapport synthese des ventes",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=16)
    subtitle_style = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], textColor=colors.grey)

    elements = []
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph("Rapport synthese des ventes", styles["Heading2"]))

    period_days = dashboard_data.get("period_days")
    period_start = dashboard_data.get("period_start", "")
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
    elements.append(
        Paragraph(
            "Periode : " + str(period_days) + " jours (a partir du " + str(period_start)[:10] + ") "
            + "-- Genere le " + generated_at + " UTC",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8 * MM))

    elements.append(Paragraph("Ventilation par site", styles["Heading3"]))

    branch_header = ["Site", "Nb ventes", "Chiffre d'affaires", "Cout (achat)", "Marge", "Taux de marge"]
    branch_rows = [branch_header]
    for b in dashboard_data.get("branches", []):
        branch_rows.append(
            [
                b.get("branch_name", "-"),
                str(b.get("sales_count", 0)),
                _fmt_amount(b.get("revenue")) + " FCFA",
                _fmt_amount(b.get("cost")) + " FCFA",
                _fmt_amount(b.get("margin")) + " FCFA",
                str(b.get("margin_rate_pct", 0)) + " %",
            ]
        )

    consolidated = dashboard_data.get("consolidated", {})
    branch_rows.append(
        [
            "TOTAL CONSOLIDE",
            str(consolidated.get("sales_count", 0)),
            _fmt_amount(consolidated.get("revenue")) + " FCFA",
            _fmt_amount(consolidated.get("cost")) + " FCFA",
            _fmt_amount(consolidated.get("margin")) + " FCFA",
            str(consolidated.get("margin_rate_pct", 0)) + " %",
        ]
    )

    branch_table = Table(branch_rows, repeatRows=1, hAlign="LEFT")
    branch_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f3f4f6")),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "LEFT"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(branch_table)
    elements.append(Spacer(1, 8 * MM))

    if top_products:
        elements.append(Paragraph("Produits les plus vendus", styles["Heading3"]))
        product_rows = [["Produit", "Reference (SKU)", "Quantite vendue"]]
        for p in top_products:
            product_rows.append([p.get("name", "-"), p.get("sku", "-"), str(p.get("quantity_sold", 0))])

        product_table = Table(product_rows, repeatRows=1, hAlign="LEFT")
        product_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        elements.append(product_table)
        elements.append(Spacer(1, 8 * MM))

    elements.append(Paragraph("Merci pour votre confiance.", styles["Normal"]))
    doc.build(elements)
    return buf


# ---------------------------------------------------------------------------
# Rapport PDF des credits clients
# ---------------------------------------------------------------------------

def build_credits_report_pdf(customers: list, branch_id: str | None = None) -> io.BytesIO:
    from datetime import date as _date

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=15 * MM,
        rightMargin=15 * MM,
        topMargin=20 * MM,
        bottomMargin=20 * MM,
    )
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle(
        "CreditTitle",
        parent=styles["Title"],
        fontSize=16,
        textColor=colors.HexColor("#011140"),
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "CreditSub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#6b7280"),
    )

    elements.append(Paragraph("Rapport des Credits Clients", title_style))
    subtitle = "Genere le " + _date.today().strftime("%d/%m/%Y")
    if branch_id:
        subtitle += " -- Boutique : " + branch_id
    elements.append(Paragraph(subtitle, sub_style))
    elements.append(Spacer(1, 6 * MM))

    total_encours = sum(float(c.credit_balance) for c in customers)
    nb_clients = len(customers)
    nb_depasse = sum(
        1 for c in customers
        if c.credit_limit and float(c.credit_limit) > 0
        and float(c.credit_balance) > float(c.credit_limit)
    )

    kpi_data = [
        ["Clients debiteurs", "Encours total (FCFA)", "Clients depassant la limite"],
        [str(nb_clients), _fmt_amount(total_encours), str(nb_depasse)],
    ]
    kpi_table = Table(kpi_data, hAlign="LEFT", colWidths=[60 * MM, 70 * MM, 60 * MM])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#011140")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 13),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.HexColor("#0439D9")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 8 * MM))

    elements.append(Paragraph("Detail par client", styles["Heading3"]))
    elements.append(Spacer(1, 3 * MM))

    table_data = [["Client", "Telephone", "Type", "Encours (FCFA)", "Limite (FCFA)", "% Util."]]
    for c in customers:
        balance = float(c.credit_balance)
        limit = float(c.credit_limit) if c.credit_limit else 0
        utilisation = str(round(balance / limit * 100, 1)) + " %" if limit > 0 else "---"
        table_data.append([
            c.full_name,
            c.phone or "---",
            c.customer_type,
            _fmt_amount(balance),
            _fmt_amount(limit) if limit > 0 else "---",
            utilisation,
        ])

    detail_table = Table(
        table_data,
        repeatRows=1,
        hAlign="LEFT",
        colWidths=[55 * MM, 30 * MM, 25 * MM, 35 * MM, 35 * MM, 20 * MM],
    )
    row_styles = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#011140")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d1d5db")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
    ]
    for i, c in enumerate(customers, 1):
        if c.credit_limit and float(c.credit_limit) > 0 and float(c.credit_balance) > float(c.credit_limit):
            row_styles.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#FEE2E2")))

    detail_table.setStyle(TableStyle(row_styles))
    elements.append(detail_table)
    elements.append(Spacer(1, 8 * MM))

    total_style = ParagraphStyle(
        "TotalLine",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#011140"),
    )
    elements.append(
        Paragraph(
            "<b>Total encours : " + _fmt_amount(total_encours) + " FCFA</b> -- "
            + str(nb_clients) + " client(s) debiteur(s)",
            total_style,
        )
    )

    doc.build(elements)
    return buf
