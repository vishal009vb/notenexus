"""
NoteNexus — PDF Export Routes
POST /api/export/pdf — Generate and return a formatted PDF of the notes
Generated on-demand, never stored.
"""
import io
from flask import Blueprint, request, jsonify, send_file
from firebase_admin import auth as firebase_auth
from backend.services.local_storage_service import get_user
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)

export_bp = Blueprint("export", __name__)

# ─── Color Palette ────────────────────────────────────────────────────────────
PRIMARY   = colors.HexColor("#4F46E5")   # Indigo
SECONDARY = colors.HexColor("#7C3AED")   # Purple
ACCENT    = colors.HexColor("#06B6D4")   # Cyan
LIGHTBG   = colors.HexColor("#F0F4FF")
DARK      = colors.HexColor("#1E1B4B")


def build_pdf(notes: dict, unit_title: str) -> bytes:
    """Build a beautiful PDF from the notes dict and return bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle("NNTitle",
        fontSize=22, textColor=PRIMARY, spaceAfter=6,
        fontName="Helvetica-Bold", leading=28)
    subtitle_style = ParagraphStyle("NNSubtitle",
        fontSize=11, textColor=colors.grey, spaceAfter=12,
        fontName="Helvetica")
    section_style = ParagraphStyle("NNSection",
        fontSize=14, textColor=colors.white, spaceBefore=14, spaceAfter=6,
        fontName="Helvetica-Bold", backColor=PRIMARY, leftIndent=-10,
        rightIndent=-10, leading=20, borderPadding=(4, 8, 4, 8))
    body_style = ParagraphStyle("NNBody",
        fontSize=10, textColor=DARK, leading=16,
        fontName="Helvetica", spaceAfter=4)
    term_style = ParagraphStyle("NNTerm",
        fontSize=10, textColor=PRIMARY, fontName="Helvetica-Bold",
        spaceAfter=2)
    q_style = ParagraphStyle("NNQ",
        fontSize=10, textColor=SECONDARY, fontName="Helvetica-Bold",
        spaceAfter=4, spaceBefore=8)
    bullet_style = ParagraphStyle("NNBullet",
        fontSize=10, textColor=DARK, leading=15, leftIndent=14,
        bulletIndent=4, fontName="Helvetica", spaceAfter=3)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    story.append(Paragraph("NoteNexus — AI BCA Notes Hub", subtitle_style))
    story.append(Paragraph(unit_title, title_style))
    story.append(Paragraph("KBCNMU · NEP 2020 · Exam-Oriented Notes", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY))
    story.append(Spacer(1, 0.4*cm))

    def section_header(text):
        story.append(Spacer(1, 0.3*cm))
        story.append(Paragraph(f"  {text}", section_style))
        story.append(Spacer(1, 0.2*cm))

    # ── Definitions ───────────────────────────────────────────────────────────
    defs = notes.get("definitions", [])
    if defs:
        section_header("📖 Definitions")
        table_data = [["Term", "Definition"]]
        for d in defs:
            table_data.append([
                Paragraph(str(d.get("term", "")), term_style),
                Paragraph(str(d.get("definition", "")), body_style)
            ])
        tbl = Table(table_data, colWidths=[4.5*cm, 12*cm])
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME",  (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",  (0, 0), (-1, 0), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [LIGHTBG, colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(tbl)

    # ── Key Points ────────────────────────────────────────────────────────────
    kp = notes.get("key_points", [])
    if kp:
        section_header("🔑 Key Points")
        for point in kp:
            story.append(Paragraph(f"• {point}", bullet_style))

    # ── Short Notes ───────────────────────────────────────────────────────────
    sn = notes.get("short_notes", [])
    if sn:
        section_header("📝 Short Notes")
        for item in sn:
            story.append(Paragraph(str(item.get("title", "")), q_style))
            story.append(Paragraph(str(item.get("content", "")), body_style))
            story.append(Spacer(1, 0.1*cm))

    # ── Long Answers ──────────────────────────────────────────────────────────
    la = notes.get("long_answers", [])
    if la:
        section_header("📚 Long Answers")
        for item in la:
            story.append(Paragraph(f"Q. {item.get('question', '')}", q_style))
            story.append(Paragraph(str(item.get("answer", "")), body_style))
            story.append(Spacer(1, 0.2*cm))

    # ── Important Questions ───────────────────────────────────────────────────
    iq = notes.get("important_questions", [])
    if iq:
        section_header("❓ Important Questions")
        for i, q in enumerate(iq, 1):
            story.append(Paragraph(f"{i}. {q}", bullet_style))

    # ── Quick Revision ────────────────────────────────────────────────────────
    qr = notes.get("quick_revision", [])
    if qr:
        section_header("⚡ Quick Revision")
        for fact in qr:
            story.append(Paragraph(f"✓ {fact}", bullet_style))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    story.append(Paragraph(
        "Generated by NoteNexus AI · KBCNMU BCA · For Educational Use Only",
        ParagraphStyle("footer", fontSize=8, textColor=colors.grey,
                       fontName="Helvetica", alignment=1)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()


@export_bp.route("/pdf", methods=["POST"])
def export_pdf():
    """Generate and return a PDF download from notes JSON."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return jsonify({"error": "Authentication required"}), 401
    try:
        from firebase_admin import auth as fb_auth
        decoded = fb_auth.verify_id_token(header[7:])
        user = get_user(decoded["uid"])
        if not user:
            return jsonify({"error": "User not found"}), 401
    except Exception:
        return jsonify({"error": "Invalid token"}), 401

    data = request.get_json() or {}
    notes = data.get("notes", {})
    unit_title = data.get("unitTitle", "BCA Notes")

    if not notes:
        return jsonify({"error": "No notes data provided"}), 400

    try:
        pdf_bytes = build_pdf(notes, unit_title)
        safe_title = "".join(c for c in unit_title if c.isalnum() or c in " _-")[:40]
        filename = f"NoteNexus_{safe_title}.pdf".replace(" ", "_")
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500
