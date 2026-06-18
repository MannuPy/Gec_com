"""
Génération de documents PDF (reportlab).

Couvre :
- RF-19 : reçu de vente (`build_sale_receipt_pdf`), au format ticket de caisse.
- RF-29 : export de rapports en PDF (`build_dashboard_report_pdf`), à partir
  des indicateurs du tableau de bord étendu (cf. blueprint `analytics`).
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
    """Construit une réponse Flask `application/pdf` à partir d'un buffer."""
    buffer.seek(0)
    disposition = "inline" if inline else "attachment"
    return Response(
        buffer.read(),
        mimetype="application/pdf",
        headers={"Content-Disposition": f'{disposition}; filename="{filename}"'},
    )


def _fmt_amount(value) -> str:
    """Formate un montant en FCFA avec séparateur de milliers (espace)."""
    try:
        amount = int(Decimal(value).to_integral_value())
    except Exception:
        amount = int(value or 0)
    return f"{amount:,}".replace(",", " ")


# ---------------------------------------------------------------------------
# RF-19 : reçu de vente (format ticket de caisse)
# ---------------------------------------------------------------------------

RECEIPT_WIDTH = 80 * mm


def build_sale_receipt_pdf(sale) -> io.BytesIO:
    """Génère le reçu PDF d'une vente (RF-19), au format ticket 80mm."""
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
        c.drawCentredString(x_center, y, f"Tél : {company_phone}")
        y -= 3.5 * mm

    y -= 1.5 * mm
    c.line(x_left, y, x_right, y)
    y -= 4.5 * mm

    c.setFont("Helvetica-Bold", 9)
    title = "AVOIR" if sale.status == "AVOIR_EMIS" else "REÇU DE VENTE"
    c.drawCentredString(x_center, y, title)
    y -= 4.5 * mm

    c.setFont("Helvetica", 7)
    created_at = sale.created_at or datetime.utcnow()
    rows = [
        f"Référence : {sale.reference}",
        f"Date : {created_at.strftime('%d/%m/%Y %H:%M')}",
        f"Site : {sale.branch.name if sale.branch else '-'}",
        f"Caissier : {sale.cashier.full_name if sale.cashier else '-'}",
    ]
    if sale.customer:
        rows.append(f"Client : {sale.customer.full_name}")
    if sale.refund_of_sale_id:
        rows.append(f"Avoir sur vente : {sale.refund_of_sale_id}")

    for row in rows:
        c.drawString(x_left, y, row)
        y -= 3.5 * mm

    y -= 1.5 * mm
    c.line(x_left, y, x_right, y)
    y -= 4 * mm

    c.setFont("Helvetica-Bold", 7)
    c.drawString(x_left, y, "Article")
    c.drawRightString(width - 26 * mm, y, "Qté")
    c.drawRightString(width - 14 * mm, y, "P.U.")
    c.drawRightString(x_right, y, "Total")
    y -= 3.5 * mm

    c.setFont("Helvetica", 7)
    for line in sale.lines:
        name = line.product.name if line.product else "?"
        if len(name) > 24:
            name = name[:23] + "…"
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
    c.drawRightString(x_right, y, f"{_fmt_amount(sale.subtotal)} FCFA")
    y -= 4 * mm

    if sale.discount_rate:
        c.drawString(x_left, y, f"Remise ({sale.discount_rate}%)")
        c.drawRightString(x_right, y, f"-{_fmt_amount(sale.discount_amount)} FCFA")
        y -= 4 * mm

    c.setFont("Helvetica-Bold", 10)
    c.drawString(x_left, y, "TOTAL")
    c.drawRightString(x_right, y, f"{_fmt_amount(sale.total)} FCFA")
    y -= 5 * mm

    c.setFont("Helvetica", 7)
    payment_labels = {
        "CASH": "Espèces",
        "MOBILE_MONEY": "Mobile Money",
        "CREDIT": "Crédit",
    }
    c.drawString(
        x_left, y, f"Mode de paiement : {payment_labels.get(sale.payment_type, sale.payment_type)}"
    )
    y -= 4 * mm

    if sale.status == "AVOIR_EMIS":
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x_center, y, "** AVOIR ÉMIS **")
        y -= 4 * mm

    y -= 1.5 * mm
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(x_center, y, "Merci de votre confiance !")

    c.showPage()
    c.save()
    return buf


# ---------------------------------------------------------------------------
# RF-29 : export de rapports (tableau de bord étendu)
# ---------------------------------------------------------------------------

def build_dashboard_report_pdf(dashboard_data: dict, top_products: list[dict] | None = None) -> io.BytesIO:
    """Génère un export PDF du tableau de bord étendu (RF-29).

    `dashboard_data` doit avoir la forme du payload de
    `GET /analytics/dashboard` (period_days, period_start, branches,
    consolidated). `top_products` est une liste optionnelle de dicts
    {name, sku, quantity_sold}.
    """
    company_name = current_app.config.get("COMPANY_NAME", "Gescom BF")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * MM,
        rightMargin=18 * MM,
        topMargin=16 * MM,
        bottomMargin=16 * MM,
        title="Rapport synthèse des ventes",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("ReportTitle", parent=styles["Title"], fontSize=16)
    subtitle_style = ParagraphStyle("ReportSubtitle", parent=styles["Normal"], textColor=colors.grey)

    elements = []
    elements.append(Paragraph(company_name, title_style))
    elements.append(Paragraph("Rapport synthèse des ventes — tableau de bord étendu", styles["Heading2"]))

    period_days = dashboard_data.get("period_days")
    period_start = dashboard_data.get("period_start", "")
    generated_at = datetime.utcnow().strftime("%d/%m/%Y %H:%M")
    elements.append(
        Paragraph(
            f"Période : {period_days} jours (à partir du {period_start[:10]}) — "
            f"Généré le {generated_at} UTC",
            subtitle_style,
        )
    )
    elements.append(Spacer(1, 8 * MM))

    # ---- Tableau par site ----
    elements.append(Paragraph("Ventilation par site", styles["Heading3"]))

    branch_header = ["Site", "Nb ventes", "Chiffre d'affaires", "Coût (achat)", "Marge", "Taux de marge"]
    branch_rows = [branch_header]
    for b in dashboard_data.get("branches", []):
        branch_rows.append(
            [
                b.get("branch_name", "-"),
                str(b.get("sales_count", 0)),
                f"{_fmt_amount(b.get('revenue'))} FCFA",
                f"{_fmt_amount(b.get('cost'))} FCFA",
                f"{_fmt_amount(b.get('margin'))} FCFA",
                f"{b.get('margin_rate_pct', 0)} %",
            ]
        )

    consolidated = dashboard_data.get("consolidated", {})
    branch_rows.append(
        [
            "TOTAL CONSOLIDÉ",
            str(consolidated.get("sales_count", 0)),
            f"{_fmt_amount(consolidated.get('revenue'))} FCFA",
            f"{_fmt_amount(consolidated.get('cost'))} FCFA",
            f"{_fmt_amount(consolidated.get('margin'))} FCFA",
            f"{consolidated.get('margin_rate_pct', 0)} %",
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

    # ---- Top produits (optionnel) ----
    if top_products:
        elements.append(Paragraph("Produits les plus vendus", styles["Heading3"]))
        product_rows = [["Produit", "Référence (SKU)", "Quantité vendue"]]
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

    elements.append(
        Paragraph("Merci pour votre confiance.", styles["Normal"])
    )
    doc.build(elements)
