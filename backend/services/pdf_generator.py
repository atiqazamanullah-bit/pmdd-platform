from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import os

def generate_academic_pdf(project_id: str, title: str, report_data: dict, output_path: str):
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=18)
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='CenterTitle', alignment=1, fontSize=18, spaceAfter=20, fontName="Times-Bold"))
    styles.add(ParagraphStyle(name='APAHeading1', fontSize=14, spaceAfter=10, fontName="Times-Bold"))
    styles.add(ParagraphStyle(name='APABodyText', fontSize=12, spaceAfter=10, fontName="Times-Roman", leading=24))
    
    Story = []
    
    # Title Page style headers
    Story.append(Paragraph(f"Linguistic Analysis Report: {title}", styles['CenterTitle']))
    Story.append(Paragraph(f"Project ID: {project_id}", styles['CenterTitle']))
    Story.append(Spacer(1, 24))
    
    # Abstract / Reliability Metrics
    Story.append(Paragraph("Abstract & Reliability Metrics", styles['APAHeading1']))
    rel = report_data.get("reliability", {})
    Story.append(Paragraph(f"Overall Reliability Score: {rel.get('overallScore', 'N/A')}", styles['APABodyText']))
    Story.append(Paragraph(f"Evidence Strength: {rel.get('evidenceStrength', 'N/A')}", styles['APABodyText']))
    Story.append(Paragraph(f"Theoretical Defensibility: {rel.get('theoreticalDefensibility', 'N/A')}", styles['APABodyText']))
    Story.append(Paragraph(f"Cross-Agent Agreement: {rel.get('crossAgentAgreement', 'N/A')}", styles['APABodyText']))
    Story.append(Spacer(1, 12))
    
    # Findings
    Story.append(Paragraph("Synthesized Findings", styles['APAHeading1']))
    findings = report_data.get("findings", [])
    
    for idx, f in enumerate(findings):
        Story.append(Paragraph(f"Finding {idx+1}: {f.get('finding_type', 'General')}", styles['APAHeading1']))
        Story.append(Paragraph(f"<b>Theory:</b> {f.get('theory', 'N/A')}", styles['APABodyText']))
        Story.append(Paragraph(f"<b>Interpretation:</b> {f.get('interpretation', 'N/A')}", styles['APABodyText']))
        
        quotes = f.get('quotes', [])
        if quotes:
            Story.append(Paragraph("<b>Primary Evidence:</b>", styles['APABodyText']))
            for q in quotes:
                Story.append(Paragraph(f'"{q}"', ParagraphStyle(name='Quote', parent=styles['APABodyText'], leftIndent=20, fontName="Times-Italic")))
        
        Story.append(Spacer(1, 12))
        
    doc.build(Story)
    return output_path
