"""Shared look-and-feel for the Genius Guide v2 PDF set.

Every book in the set uses the same palette, styles and page furniture so the
five PDFs read as one series. Import `book()` to get a configured doc template.
"""
from __future__ import annotations

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

PAGE_W, PAGE_H = letter
MARGIN = 40

# ── Palette ──────────────────────────────────────────────────────────────────
INK = colors.HexColor("#0F172A")
SLATE = colors.HexColor("#334155")
MUTE = colors.HexColor("#64748B")
FAINT = colors.HexColor("#94A3B8")
LINE = colors.HexColor("#CBD5E1")
HAIR = colors.HexColor("#E2E8F0")
TEAL = colors.HexColor("#0D9488")
TEAL_DK = colors.HexColor("#0F766E")
BAND = colors.HexColor("#F0FDFA")
BAND2 = colors.HexColor("#F8FAFC")
WHITE = colors.white

# Weight badges -- how expensive an action is to run.
WEIGHT_COLORS = {
    "Feather": colors.HexColor("#15803D"),
    "Light": colors.HexColor("#0D9488"),
    "Medium": colors.HexColor("#B45309"),
    "Heavy": colors.HexColor("#C2410C"),
    "Very heavy": colors.HexColor("#B91C1C"),
}
WEIGHT_MEANING = {
    "Feather": "one tiny bridge round-trip, effectively instant",
    "Light": "one round-trip, small payload back",
    "Medium": "one big payload, or a handful of chained calls",
    "Heavy": "loops over many tracks/clips/notes, or heavy local compute",
    "Very heavy": "real-time wall-clock work, or a full-session scan",
}

# Model badges -- which chat model to point at a given job.
MODEL_COLORS = {
    "CLAUDE": colors.HexColor("#B45309"),
    "GPT": colors.HexColor("#0369A1"),
    "GROK": colors.HexColor("#7C3AED"),
    "GEMINI": colors.HexColor("#15803D"),
    "ANY": colors.HexColor("#475569"),
}
MODEL_WHY = {
    "CLAUDE": "precise multi-step Live automation / exact tool sequencing",
    "GPT": "balanced generalist, strong second choice for automation",
    "GROK": "long-form theory and creative coaching, big-context digestion",
    "GEMINI": "fast, cheap single-fact lookups and simple citations",
    "ANY": "simple enough that model choice barely matters",
}

COMPLEXITY_COLORS = {
    "Starter": colors.HexColor("#15803D"),
    "Intermediate": colors.HexColor("#0369A1"),
    "Advanced": colors.HexColor("#B45309"),
    "Expert": colors.HexColor("#B91C1C"),
}

SERIES = "LIVE ACTIONS GENIUS — USER GUIDE"


# ── Styles ───────────────────────────────────────────────────────────────────
def styles() -> dict[str, ParagraphStyle]:
    ss = getSampleStyleSheet()
    s: dict[str, ParagraphStyle] = {}

    s["title"] = ParagraphStyle(
        "title", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=30,
        leading=35, textColor=INK, alignment=0, spaceAfter=4,
    )
    s["subtitle"] = ParagraphStyle(
        "subtitle", parent=ss["Normal"], fontName="Helvetica", fontSize=13,
        leading=18, textColor=TEAL_DK, spaceAfter=14,
    )
    s["booknum"] = ParagraphStyle(
        "booknum", parent=ss["Normal"], fontName="Helvetica-Bold", fontSize=10,
        leading=13, textColor=TEAL, spaceAfter=6,
    )
    s["h1"] = ParagraphStyle(
        "h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=18,
        leading=22, textColor=INK, spaceBefore=16, spaceAfter=7,
    )
    s["h2"] = ParagraphStyle(
        "h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=13,
        leading=17, textColor=TEAL_DK, spaceBefore=13, spaceAfter=5,
    )
    s["h3"] = ParagraphStyle(
        "h3", parent=ss["Heading3"], fontName="Helvetica-Bold", fontSize=10.5,
        leading=14, textColor=SLATE, spaceBefore=9, spaceAfter=3,
    )
    s["body"] = ParagraphStyle(
        "body", parent=ss["Normal"], fontName="Helvetica", fontSize=9.5,
        leading=13.5, textColor=SLATE, spaceAfter=6,
    )
    s["small"] = ParagraphStyle(
        "small", parent=s["body"], fontSize=8.3, leading=11.5, textColor=MUTE,
    )
    s["cell"] = ParagraphStyle(
        "cell", parent=ss["Normal"], fontName="Helvetica", fontSize=8.2,
        leading=11, textColor=SLATE,
    )
    s["cellb"] = ParagraphStyle(
        "cellb", parent=s["cell"], fontName="Helvetica-Bold", textColor=INK,
    )
    s["mono"] = ParagraphStyle(
        "mono", parent=ss["Normal"], fontName="Courier-Bold", fontSize=8.2,
        leading=11, textColor=TEAL_DK,
    )
    s["monobody"] = ParagraphStyle(
        "monobody", parent=ss["Normal"], fontName="Courier", fontSize=8.4,
        leading=12, textColor=INK, leftIndent=9, spaceAfter=4,
    )
    s["prompt"] = ParagraphStyle(
        "prompt", parent=ss["Normal"], fontName="Helvetica-Oblique", fontSize=9.2,
        leading=13, textColor=INK, leftIndent=10, rightIndent=8, spaceAfter=3,
    )
    s["bullet"] = ParagraphStyle(
        "bullet", parent=s["body"], leftIndent=15, bulletIndent=4, spaceAfter=3.5,
    )
    s["note"] = ParagraphStyle(
        "note", parent=s["body"], fontSize=8.8, leading=12.5, leftIndent=9,
        rightIndent=9, textColor=SLATE,
    )
    return s


class GuideCanvas(canvas.Canvas):
    """Page furniture: running head, footer, page N of M."""

    footer_left = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved)
        for state in self._saved:
            self.__dict__.update(state)
            self._decorate(total)
            super().showPage()
        super().save()

    def _decorate(self, total: int):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(MUTE)
        if self._pageNumber > 1:
            self.drawString(MARGIN, PAGE_H - 28, SERIES)
            self.drawRightString(PAGE_W - MARGIN, PAGE_H - 28, self.running_title)
            self.setStrokeColor(LINE)
            self.setLineWidth(0.5)
            self.line(MARGIN, PAGE_H - 31, PAGE_W - MARGIN, PAGE_H - 31)
        self.setFillColor(FAINT)
        self.drawString(MARGIN, 20, self.footer_left)
        self.drawRightString(PAGE_W - MARGIN, 20, f"Page {self._pageNumber} of {total}")
        self.setStrokeColor(LINE)
        self.setLineWidth(0.5)
        self.line(MARGIN, 28, PAGE_W - MARGIN, 28)
        self.restoreState()


def make_canvas(running_title: str, footer_left: str):
    """Build a GuideCanvas subclass bound to this book's header/footer text."""
    return type("BoundCanvas", (GuideCanvas,), {
        "running_title": running_title,
        "footer_left": footer_left,
    })


def doc(path: str, title: str) -> SimpleDocTemplate:
    return SimpleDocTemplate(
        path, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=46, bottomMargin=40,
        title=title, author="DigiDreamWeaver",
    )


# ── Reusable flowables ───────────────────────────────────────────────────────
def rule(color=LINE, width=0.8, space_after=8):
    return HRFlowable(width="100%", thickness=width, color=color,
                      spaceBefore=2, spaceAfter=space_after)


def badge(text: str, color) -> Table:
    """A small solid colour chip with white text."""
    st = ParagraphStyle("badge", fontName="Helvetica-Bold", fontSize=6.6,
                        leading=8.4, textColor=WHITE, alignment=1)
    t = Table([[Paragraph(text.upper(), st)]], colWidths=[len(text) * 4.3 + 12], rowHeights=[12])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), color),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 2),
        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
    ]))
    return t


def callout(flowables, fill=BAND, border=TEAL, pad=9):
    """Boxed aside."""
    t = Table([[flowables]], colWidths=[PAGE_W - 2 * MARGIN])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fill),
        ("BOX", (0, 0), (-1, -1), 0.8, border),
        ("LEFTPADDING", (0, 0), (-1, -1), pad),
        ("RIGHTPADDING", (0, 0), (-1, -1), pad),
        ("TOPPADDING", (0, 0), (-1, -1), pad - 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), pad - 2),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def data_table(rows, col_widths, header=True, zebra=True, font_size=8.2):
    """Standard bordered table with a teal header row."""
    t = Table(rows, colWidths=col_widths, repeatRows=1 if header else 0)
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, HAIR),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]
    if header:
        cmds += [
            ("BACKGROUND", (0, 0), (-1, 0), TEAL_DK),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), font_size),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 5),
            ("TOPPADDING", (0, 0), (-1, 0), 5),
        ]
    if zebra:
        start = 1 if header else 0
        for i in range(start, len(rows)):
            if (i - start) % 2 == 1:
                cmds.append(("BACKGROUND", (0, i), (-1, i), BAND2))
    t.setStyle(TableStyle(cmds))
    return t


def cover(story, s, book_no: str, title: str, subtitle: str, blurb: str,
          contents: list[str], meta: str):
    """Standard cover page for a book in the series."""
    story.append(Spacer(1, 42))
    story.append(Paragraph(SERIES, s["booknum"]))
    story.append(rule(TEAL, 1.6, 12))
    story.append(Paragraph(f"Book {book_no}", s["booknum"]))
    story.append(Paragraph(title, s["title"]))
    story.append(Paragraph(subtitle, s["subtitle"]))
    story.append(Paragraph(blurb, s["body"]))
    story.append(Spacer(1, 14))
    inner = [Paragraph("<b>In this book</b>", s["h3"])]
    for c in contents:
        inner.append(Paragraph(c, s["bullet"], bulletText="•"))
    story.append(callout(inner))
    story.append(Spacer(1, 12))
    story.append(Paragraph(meta, s["small"]))
    story.append(PageBreak())
