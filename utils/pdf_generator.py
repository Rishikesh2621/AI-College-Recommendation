from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from utils.helper import money


def build_pdf_report(path: Path, profile: dict, recommendations: dict, counseling_markdown: str) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=A4,
        rightMargin=42,
        leftMargin=42,
        topMargin=110,
        bottomMargin=105,
    )
    styles = _styles()
    story = []

    story.append(Paragraph("COLLEGE RECOMMENDATION & COUNSELING REPORT", styles["DocTitle"]))
    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph(f"Prepared for: <b>{profile['full_name']}</b> &nbsp;&nbsp;|&nbsp;&nbsp; Date: {datetime.now().strftime('%d %B %Y')}", styles["DocMeta"]))
    story.append(Spacer(1, 0.25 * inch))

    branches = profile.get("branches") or []
    if not branches and profile.get("branch"):
        branches = [profile["branch"]]
    branches_str = " / ".join(branches)

    story.append(Paragraph("Student Information", styles["Heading"]))
    story.append(_table([
        ["Name", profile["full_name"]],
        ["Email", profile["email"]],
        ["Phone", profile["phone"]],
        ["Percentile", profile["percentile"]],
        ["Caste Category", profile["category"]],
        ["Gender", profile["gender"]],
        ["Preferred Branch", branches_str],
        ["Preferred City", profile.get("city") or "Flexible"],
    ], colWidths=[150, 361]))
    story.append(Spacer(1, 0.22 * inch))

    # Top 10 Recommended Colleges (Combined)
    _add_recommendation_table(story, styles, "Top Recommended Colleges (Combined)", recommendations.get("top", []))
    story.append(Spacer(1, 0.15 * inch))

    # Branch-wise recommendations
    for br, br_recs in recommendations.get("by_branch", {}).items():
        for group_name, group_colleges in br_recs.get("chance_groups", {}).items():
            if group_colleges:
                _add_recommendation_table(story, styles, f"{group_name} — {br}", group_colleges[:10])
                story.append(Spacer(1, 0.05 * inch))


    story.append(Spacer(1, 0.4 * inch))
    sig_data = [
        ["_______________________", "", "_______________________"],
        ["Parent's Signature", "", "Authorized Signature"]
    ]
    sig_table = Table(sig_data, colWidths=[200, 111, 200])
    sig_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1F2937")),
        ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(sig_table)

    doc.build(story, onFirstPage=_draw_header_footer, onLaterPages=_draw_header_footer)


def _add_recommendation_table(story: list, styles: dict, title: str, colleges: list[dict]) -> None:
    story.append(Paragraph(title, styles["Heading"]))
    if not colleges:
        story.append(Paragraph("No colleges found for this group.", styles["Body"]))
        return

    rows = [["College", "City", "Closing Score", "Chance", "Fees", "Placement"]]
    for college in colleges:
        rows.append([
            college["College Name"],
            college["City"],
            f"{college['Closing Percentile']:.1f}",
            college["chance"],
            money(college["Fees"]),
            f"{college['Placement Percentage']:.0f}%" if college["Placement Percentage"] > 0 else "—",
        ])
    story.append(_table(rows, header=True, colWidths=[190, 70, 70, 60, 60, 61]))
    story.append(Spacer(1, 0.18 * inch))


def _table(rows: list[list], header: bool = False, colWidths: list[float] | None = None) -> Table:
    styles = _styles()
    cell_style = styles["TableCell"]
    header_style = styles["TableHeader"]
    
    wrapped_rows = []
    for r_idx, row in enumerate(rows):
        wrapped_row = []
        for c_idx, cell in enumerate(row):
            if isinstance(cell, Paragraph):
                wrapped_row.append(cell)
            else:
                cell_str = str(cell) if cell is not None else ""
                style = header_style if (header and r_idx == 0) else cell_style
                wrapped_row.append(Paragraph(cell_str, style))
        wrapped_rows.append(wrapped_row)

    table = Table(wrapped_rows, colWidths=colWidths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#d7dde8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.extend([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B365D")),
        ])
    table.setStyle(TableStyle(style))
    return table


def _styles() -> dict:
    sample = getSampleStyleSheet()
    return {
        "DocTitle": ParagraphStyle("DocTitle", parent=sample["Title"], fontSize=16, leading=20, textColor=colors.HexColor("#1B365D"), alignment=1, spaceAfter=12),
        "DocMeta": ParagraphStyle("DocMeta", parent=sample["Normal"], fontSize=9, leading=11, textColor=colors.HexColor("#4B5563"), alignment=1, spaceAfter=10),
        "Heading": ParagraphStyle("Heading", parent=sample["Heading2"], fontSize=12, textColor=colors.HexColor("#1B365D"), spaceBefore=10, spaceAfter=6),
        "Subheading": ParagraphStyle("Subheading", parent=sample["Heading3"], fontSize=10, textColor=colors.HexColor("#1f2937"), spaceBefore=6, spaceAfter=4),
        "Body": ParagraphStyle("Body", parent=sample["BodyText"], fontSize=8.5, leading=12.5, spaceAfter=4),
        "Small": ParagraphStyle("Small", parent=sample["BodyText"], fontSize=7.5, leading=10, textColor=colors.HexColor("#64748b")),
        "TableCell": ParagraphStyle("TableCell", parent=sample["Normal"], fontSize=8, leading=10),
        "TableHeader": ParagraphStyle("TableHeader", parent=sample["Normal"], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold"),
    }


def _draw_header_footer(canvas, doc):
    canvas.saveState()
    W, H = A4
    
    # ---------------- HEADER ----------------
    # Left Section: FUTURE GROWTH FOUNDATION
    canvas.setFont("Helvetica-Bold", 18)
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.drawString(42, 802, "FUTURE GROWTH ")
    
    fg_width = canvas.stringWidth("FUTURE GROWTH ", "Helvetica-Bold", 18)
    canvas.setFillColor(colors.HexColor("#E87722"))
    canvas.drawString(42 + fg_width, 802, "FOUNDATION")
    
    # Underline/ADMISSION COUNSELLORS row
    canvas.setStrokeColor(colors.HexColor("#E87722"))
    canvas.setLineWidth(1)
    canvas.line(42, 788, 85, 788)
    
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(1.5)
    canvas.line(90, 784, 90, 792)
    
    canvas.setFont("Helvetica-Bold", 10)
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.drawString(98, 785, "ADMISSION COUNSELLORS")
    
    ac_width = canvas.stringWidth("ADMISSION COUNSELLORS", "Helvetica-Bold", 10)
    canvas.setStrokeColor(colors.HexColor("#E87722"))
    canvas.setLineWidth(1)
    canvas.line(98 + ac_width + 8, 788, 335, 788)
    
    # Subtitle: Guiding students toward a better future.
    canvas.setFont("Helvetica-Oblique", 9)
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.drawString(98, 770, "Guiding students ")
    gs_width = canvas.stringWidth("Guiding students ", "Helvetica-Oblique", 9)
    canvas.setFont("Helvetica-BoldOblique", 9)
    canvas.setFillColor(colors.HexColor("#E87722"))
    canvas.drawString(98 + gs_width, 770, "toward a better future.")
    
    # Vertical separator line
    canvas.setStrokeColor(colors.HexColor("#D1D5DB"))
    canvas.setLineWidth(1)
    canvas.line(W - 195, 765, W - 195, 815)
    
    # Right Section: Initiative of Sadguru Jog Maharaj
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#4B5563"))
    canvas.drawString(W - 185, 805, "An Educational Initiative of")
    
    canvas.setFont("Helvetica-Bold", 8.5)
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.drawString(W - 185, 793, "Shri Sadguru Jog Maharaj")
    canvas.drawString(W - 185, 782, "Shikshan Sanstha")
    
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#4B5563"))
    canvas.drawString(W - 185, 771, "Reg. No. E1829")
    
    # Bottom thick horizontal bar of header
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.rect(42, 750, (W - 84) * 0.7, 3, fill=True, stroke=False)
    canvas.setFillColor(colors.HexColor("#E87722"))
    canvas.rect(42 + (W - 84) * 0.7, 750, (W - 84) * 0.3, 3, fill=True, stroke=False)
    
    # ---------------- FOOTER ----------------
    # Your Career, Our Responsibility Centered
    canvas.setFont("Helvetica-BoldOblique", 9)
    canvas.setFillColor(colors.HexColor("#1B365D"))
    center_text = "Your Career, Our Responsibility"
    text_w = canvas.stringWidth(center_text, "Helvetica-BoldOblique", 9)
    canvas.drawCentredString(W / 2, 85, center_text)
    
    # Lines on either side of the footer text
    canvas.setStrokeColor(colors.HexColor("#B5A26B"))
    canvas.setLineWidth(1)
    canvas.line(42, 88, W / 2 - text_w / 2 - 15, 88)
    canvas.line(W / 2 + text_w / 2 + 15, 88, W - 42, 88)
    
    # Dots at the end of the lines
    canvas.setFillColor(colors.HexColor("#B5A26B"))
    canvas.circle(W / 2 - text_w / 2 - 15, 88, 2.5, fill=True, stroke=False)
    canvas.circle(W / 2 + text_w / 2 + 15, 88, 2.5, fill=True, stroke=False)
    
    # 4 columns for contact details
    col_y = 52
    
    # Column 1: Phone
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.circle(50, col_y + 4, 8, fill=True, stroke=False)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(50, col_y + 1, "P")
    
    canvas.setFont("Helvetica-Bold", 6.5)
    canvas.setFillColor(colors.HexColor("#1F2937"))
    canvas.drawString(62, col_y + 6, "+91-9356845961")
    canvas.drawString(62, col_y - 2, "+91-9325458435")
    
    # Column 2: Address
    canvas.setFillColor(colors.HexColor("#E87722"))
    canvas.circle(158, col_y + 4, 8, fill=True, stroke=False)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(158, col_y + 1, "A")
    
    canvas.setFont("Helvetica", 5.5)
    canvas.setFillColor(colors.HexColor("#1F2937"))
    canvas.drawString(170, col_y + 11, "Gurukrupa Apartment, 1st Floor,")
    canvas.drawString(170, col_y + 5, "Beside Domino's Pizza,")
    canvas.drawString(170, col_y - 1, "Near Somalwada Square,")
    canvas.drawString(170, col_y - 7, "Nagpur - 440024")
    
    # Column 3: Email
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.circle(295, col_y + 4, 8, fill=True, stroke=False)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(295, col_y + 1, "E")
    
    canvas.setFont("Helvetica-Bold", 6)
    canvas.setFillColor(colors.HexColor("#1F2937"))
    canvas.drawString(307, col_y + 1, "info.futuregrowthcounselling@gmail.com")
    
    # Column 4: Web
    canvas.setFillColor(colors.HexColor("#E87722"))
    canvas.circle(445, col_y + 4, 8, fill=True, stroke=False)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.setFillColor(colors.white)
    canvas.drawCentredString(445, col_y + 1, "W")
    
    canvas.setFont("Helvetica-Bold", 6)
    canvas.setFillColor(colors.HexColor("#1F2937"))
    canvas.drawString(457, col_y + 1, "www.futuregrowthfoundation.in")
    
    # Bottom double bar
    canvas.setFillColor(colors.HexColor("#1B365D"))
    canvas.rect(42, 15, (W - 84) * 0.7, 10, fill=True, stroke=False)
    
    canvas.setFillColor(colors.HexColor("#B5A26B"))
    p = canvas.beginPath()
    p.moveTo(42 + (W - 84) * 0.7 - 8, 15)
    p.lineTo(42 + (W - 84) * 0.7 - 2, 25)
    p.lineTo(42 + (W - 84) * 0.7 + 2, 25)
    p.lineTo(42 + (W - 84) * 0.7 - 4, 15)
    canvas.drawPath(p, fill=True, stroke=False)
    
    canvas.setFillColor(colors.HexColor("#E87722"))
    canvas.rect(42 + (W - 84) * 0.7, 15, (W - 84) * 0.3, 10, fill=True, stroke=False)
    
    # Page Number
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawRightString(W - 42, 29, f"Page {doc.page}")
    
    canvas.restoreState()
