import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import cm

def md_to_paragraphs(md_text):
    lines = md_text.splitlines()
    story = []
    styles = getSampleStyleSheet()
    h = ParagraphStyle('Heading', parent=styles['Heading2'], spaceAfter=6)
    p = ParagraphStyle('Body', parent=styles['BodyText'], leading=14, spaceAfter=6)
    bullets = ('- ', '* ', '+ ')
    for line in lines:
        if not line.strip():
            story.append(Spacer(1, 6))
            continue
        if line.startswith('### '):
            story.append(Paragraph(line[4:], h))
        elif line.startswith('## '):
            story.append(Paragraph(line[3:], h))
        elif line.startswith(bullets):
            story.append(Paragraph(line, p))
        else:
            story.append(Paragraph(line, p))
    return story

def export_user_guide(src_path='docs/UserGuide.md', out_path='UserGuide.pdf'):
    with open(src_path, 'r', encoding='utf-8') as f:
        md_text = f.read()
    doc = SimpleDocTemplate(out_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    story = md_to_paragraphs(md_text)
    doc.build(story)
    return os.path.abspath(out_path)

if __name__ == '__main__':
    path = export_user_guide()
    print(path)

