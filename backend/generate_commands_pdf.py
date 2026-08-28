import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header line (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "F.R.I.D.A.Y. AI Assistant — Official Voice & Automation Cheat Sheet")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 558, 742)

        # Footer
        page_text = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 35, page_text)
        self.drawString(54, 35, "Confidential & Proprietary — F.R.I.D.A.Y. Project")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 48, 558, 48)
        self.restoreState()

def build_pdf():
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "FRIDAY_Commands_Guide.pdf")
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor('#0f172a'),
        alignment=0,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#475569'),
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'SectionH1',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=16,
        textColor=colors.HexColor('#0284c7'),
        spaceBefore=12,
        spaceAfter=6
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#0f172a')
    )

    cell_code = ParagraphStyle(
        'CellCode',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#0369a1')
    )

    cell_text = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#334155')
    )

    header_cell = ParagraphStyle(
        'HeaderCell',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
        textColor=colors.white
    )

    story = []

    # Title & Subtitle
    story.append(Paragraph("F.R.I.D.A.Y. AI Assistant", title_style))
    story.append(Paragraph("Complete Voice, Tiling & Deep Automation Command Cheat Sheet", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=12))

    sections = [
        (
            "1. 📱 Application Control & Multi-Window Tiling",
            [
                ("Open App", '"Open Spotify", "Open Calculator", "Launch VSCode"', "Launches application instantly"),
                ("Close App", '"Close Spotify", "Quit Chrome", "Band kardo Calculator"', "Safely terminates target application"),
                ("4-Corner Tiling", '"Chrome top-left me, VS Code right me, Terminal bottom-left me"', "Precise 4-corner multi-window tiling"),
                ("Auto Grid Tiling", '"Tile Chrome and VS Code", "Split screen Spotify and Terminal"', "2, 3, or 4 app auto-grid tiling"),
                ("Minimize All", '"Minimize all", "Show desktop", "Clean workspace"', "Minimizes windows to reveal desktop")
            ]
        ),
        (
            "2. 🎵 Spotify & Media Deep Automation",
            [
                ("Search & Play Song", '"Play Believer on Spotify", "Spotify par Arijit Singh bajao"', "Direct Spotify search URI & song playback"),
                ("Media Play / Pause", '"Play music", "Pause music", "Gaana roko", "Chalao"', "Controls active system media playback"),
                ("Next / Prev Track", '"Next song", "Skip track", "Agla gaana"', "Skips to the next music track")
            ]
        ),
        (
            "3. 🌐 Browser & Web Search Automation",
            [
                ("YouTube Search", '"Search on YouTube quantum computing", "YouTube search lofi"', "Opens YouTube search results directly"),
                ("Google Search", '"Search on Google latest AI news", "Google search machine learning"', "Opens Google web search in default browser"),
                ("Direct Domain", '"Open github.com", "Open reddit.com", "Open chatgpt.com"', "Opens direct web domains")
            ]
        ),
        (
            "4. 📁 File & Folder Management Subsystem",
            [
                ("Create Folder", '"Create folder AI_Projects", "Folder banao Assignments"', "Creates folder on Desktop"),
                ("Create File", '"Create file notes.txt", "File banao summary.txt"', "Creates text file on Desktop"),
                ("Organize Downloads", '"Organize downloads", "Clean downloads", "Downloads organize kardo"', "Auto-sorts files into Images, Docs, Code, etc."),
                ("Safe Delete to Trash", '"Delete file draft.txt", "Remove file temp.pdf"', "Safely moves file to OS Trash/Recycle Bin"),
                ("Search File", '"Search file resume.pdf", "Find file report.docx", "File dhundo"', "Fast recursive search across user folders"),
                ("Recent Downloads", '"Recent downloads", "Latest downloads dikhao"', "Lists latest downloads with size & date")
            ]
        ),
        (
            "5. 📋 Advanced Clipboard & Text Utilities",
            [
                ("Read Clipboard", '"Read clipboard", "What\'s in clipboard", "Clipboard padho"', "Speaks & retrieves clipboard contents"),
                ("Copy Text", '"Copy API_KEY_SECRET", "Clipboard copy Hello FRIDAY"', "Writes text to clipboard & stores history"),
                ("Transform Uppercase", '"Make clipboard uppercase", "Uppercase clipboard"', "Converts clipboard text to UPPERCASE"),
                ("Transform Lowercase", '"Make clipboard lowercase", "Lowercase clipboard"', "Converts clipboard text to lowercase")
            ]
        ),
        (
            "6. 🚀 Multi-Step Automated Workflows",
            [
                ("Meeting Mode", '"Start meeting mode", "Meeting routine"', "Mutes audio + Opens Zoom/Meet + Notes + Tiles"),
                ("Focus Mode", '"Start focus mode", "Deep work mode"', "Closes distractions + Opens VS Code + 35% Volume"),
                ("Coding Mode", '"Start coding mode", "Coding shuru"', "Tiles VS Code (50% L), Terminal & Browser (25% R)")
            ]
        ),
        (
            "7. 🔊 System Audio, Brightness & Security",
            [
                ("Volume Control", '"Set volume to 50", "Volume 80", "Aawaz badhao/kam karo"', "Sets system output volume level"),
                ("Mute / Unmute", '"Mute sound", "Unmute sound", "Aawaz chalu/band karo"', "Mutes or un-mutes system sound"),
                ("Screen Brightness", '"Set brightness to 70", "Brightness 100", "Chamak kam karo"', "Sets screen display brightness"),
                ("Screenshot", '"Take a screenshot", "Capture screen"', "Captures full screen to Desktop"),
                ("Lock Computer", '"Lock screen", "Lock mac", "Screen lock kardo"', "Instantly locks computer"),
                ("Clear Memory", '"Clear history", "Delete memory", "Memory clear kardo"', "Clears conversation & action history")
            ]
        )
    ]

    col_widths = [120, 210, 174]

    for title, rows in sections:
        story.append(Paragraph(title, h1_style))
        table_data = [[
            Paragraph("Command Category", header_cell),
            Paragraph("Voice / Text Command Syntax", header_cell),
            Paragraph("Automated Action Executed", header_cell)
        ]]

        for cat, cmd, desc in rows:
            table_data.append([
                Paragraph(cat, cell_bold),
                Paragraph(cmd, cell_code),
                Paragraph(desc, cell_text)
            ])

        t = Table(table_data, colWidths=col_widths, repeatRows=1)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0284c7')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#f8fafc'), colors.white]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ]))
        story.append(t)
        story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[PDF] Successfully created: {pdf_path}")

if __name__ == "__main__":
    build_pdf()
