import os
from app.config import settings

TEMPLATES = {
    "modern": {
        "name": "Modern",
        "description": "Clean sans-serif with navy accents — the default",
        "css": """
    @page {
        size: letter;
        margin: 0.6in 0.75in;
    }
    body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 10.5pt;
        line-height: 1.35;
        color: #1a1a1a;
    }
    .header {
        text-align: center;
        margin-bottom: 10pt;
        padding-bottom: 8pt;
        border-bottom: 1.5pt solid #2c3e50;
    }
    .name {
        font-size: 16pt;
        font-weight: 700;
        margin-bottom: 2pt;
        color: #1a1a1a;
    }
    .contact {
        font-size: 9pt;
        color: #555;
    }
    .section-title {
        font-size: 11pt;
        font-weight: 700;
        color: #2c3e50;
        border-bottom: 0.8pt solid #2c3e50;
        padding-bottom: 2pt;
        margin-top: 14pt;
        margin-bottom: 5pt;
        text-transform: uppercase;
        letter-spacing: 0.8pt;
    }
    .bullet {
        margin-bottom: 3pt;
        padding-left: 12pt;
        text-indent: -12pt;
        text-align: justify;
    }
    .bullet::before { content: "\\2022"; color: #2c3e50; margin-right: 5pt; }
    .role-title {
        font-weight: 700;
        font-size: 10.5pt;
        margin-top: 6pt;
        margin-bottom: 1pt;
        color: #1a1a1a;
    }
    .skills-line {
        margin-top: 2pt;
        line-height: 1.5;
    }
    .education-entry {
        margin-bottom: 1pt;
        padding-left: 12pt;
    }
""",
    },
    "classic": {
        "name": "Classic",
        "description": "Traditional serif with small-caps — formal and timeless",
        "css": """
    @page {
        size: letter;
        margin: 0.7in 0.8in;
    }
    body {
        font-family: Georgia, "Times New Roman", Times, serif;
        font-size: 10.5pt;
        line-height: 1.4;
        color: #1a1a1a;
    }
    .header {
        text-align: center;
        margin-bottom: 12pt;
        padding-bottom: 6pt;
        border-bottom: 1pt solid #000;
    }
    .name {
        font-size: 15pt;
        font-weight: 700;
        font-variant: small-caps;
        letter-spacing: 1.5pt;
        margin-bottom: 3pt;
        color: #000;
    }
    .contact {
        font-size: 9pt;
        color: #444;
    }
    .section-title {
        font-size: 10.5pt;
        font-weight: 700;
        font-variant: small-caps;
        letter-spacing: 1.2pt;
        color: #000;
        border-bottom: 0.5pt solid #000;
        padding-bottom: 2pt;
        margin-top: 14pt;
        margin-bottom: 5pt;
    }
    .bullet {
        margin-bottom: 3pt;
        padding-left: 14pt;
        text-indent: -14pt;
        text-align: justify;
    }
    .bullet::before { content: "\\2013"; font-weight: 700; margin-right: 5pt; }
    .role-title {
        font-weight: 700;
        font-size: 10.5pt;
        margin-top: 6pt;
        margin-bottom: 1pt;
        color: #000;
    }
    .skills-line {
        margin-top: 2pt;
        line-height: 1.5;
    }
    .education-entry {
        margin-bottom: 1pt;
        padding-left: 14pt;
    }
""",
    },
    "compact": {
        "name": "Compact",
        "description": "Dense layout that fits more content — banking/consulting style",
        "css": """
    @page {
        size: letter;
        margin: 0.5in 0.65in;
    }
    body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 9.5pt;
        line-height: 1.25;
        color: #1a1a1a;
    }
    .header {
        text-align: left;
        margin-bottom: 6pt;
        padding-bottom: 4pt;
        border-bottom: 1pt solid #333;
    }
    .name {
        font-size: 14pt;
        font-weight: 700;
        margin-bottom: 1pt;
        color: #1a1a1a;
    }
    .contact {
        font-size: 8pt;
        color: #555;
    }
    .section-title {
        font-size: 9.5pt;
        font-weight: 700;
        color: #333;
        border-bottom: 0.5pt solid #999;
        padding-bottom: 1pt;
        margin-top: 8pt;
        margin-bottom: 3pt;
        text-transform: uppercase;
        letter-spacing: 0.5pt;
    }
    .bullet {
        margin-bottom: 1.5pt;
        padding-left: 10pt;
        text-indent: -10pt;
        text-align: justify;
    }
    .bullet::before { content: "\\2022"; margin-right: 5pt; }
    .role-title {
        font-weight: 700;
        font-size: 10pt;
        margin-top: 5pt;
        margin-bottom: 1pt;
        color: #1a1a1a;
    }
    .skills-line {
        margin-top: 1pt;
        font-size: 8.5pt;
        line-height: 1.35;
    }
    .education-entry {
        margin-bottom: 0.5pt;
        padding-left: 10pt;
        font-size: 9pt;
    }
""",
    },
    "creative": {
        "name": "Creative",
        "description": "Modern with a blue accent header bar — stands out visually",
        "css": """
    @page {
        size: letter;
        margin: 0in;
        @top-left {
            content: "";
            width: 100%;
            height: 22pt;
            background: #2563eb;
        }
    }
    @page {
        margin: 22pt 0.7in 0.55in 0.7in;
    }
    body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 10pt;
        line-height: 1.35;
        color: #1a1a1a;
    }
    .header {
        margin-bottom: 10pt;
        padding-bottom: 6pt;
        border-bottom: 1pt solid #e5e7eb;
    }
    .name {
        font-size: 16pt;
        font-weight: 700;
        margin-bottom: 2pt;
        color: #2563eb;
    }
    .contact {
        font-size: 9pt;
        color: #666;
    }
    .section-title {
        font-size: 10.5pt;
        font-weight: 700;
        color: #2563eb;
        border-bottom: none;
        padding-bottom: 1pt;
        margin-top: 12pt;
        margin-bottom: 5pt;
        text-transform: uppercase;
        letter-spacing: 0.6pt;
    }
    .bullet {
        margin-bottom: 3pt;
        padding-left: 12pt;
        text-indent: -12pt;
        text-align: justify;
        border-left: 1.5pt solid #dbeafe;
        padding-left: 14pt;
    }
    .bullet::before { content: "\\25B8"; color: #2563eb; font-size: 8pt; margin-right: 5pt; }
    .role-title {
        font-weight: 700;
        font-size: 10.5pt;
        margin-top: 6pt;
        margin-bottom: 1pt;
        color: #2563eb;
    }
    .skills-line {
        margin-top: 2pt;
        line-height: 1.5;
    }
    .education-entry {
        margin-bottom: 1pt;
        padding-left: 14pt;
        border-left: 1.5pt solid #dbeafe;
    }
""",
    },
}


def build_resume_html(structured_data: dict, optimized_bullets: list[dict] | None = None, template: str = "modern") -> str:
    css = TEMPLATES.get(template, TEMPLATES["modern"])["css"]

    name = structured_data.get("full_name", "")
    email = structured_data.get("email", "")
    phone = structured_data.get("phone", "")
    location = structured_data.get("location", "")
    linkedin = structured_data.get("linkedin", "")

    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
    if linkedin:
        contact_parts.append(linkedin)
    contact_line = "  |  ".join(contact_parts)

    sections_html = []

    for section in structured_data.get("sections", []):
        title = section.get("title", "").strip()
        if not title:
            continue
        bullets = section.get("bullets", [])

        if title.lower() in ("skills", "technical skills", "core competencies"):
            skills_text = []
            for bullet in bullets:
                t = bullet.get("text", bullet) if isinstance(bullet, dict) else bullet
                skills_text.append(t)
            combined = ", ".join(skills_text) if skills_text else ""
            sections_html.append(
                f'<div class="section-title">{title}</div>'
                f'<div class="skills-line">{combined}</div>'
            )
            continue

        if title.lower() in ("education", "academics"):
            entries = []
            for bullet in bullets:
                t = bullet.get("text", bullet) if isinstance(bullet, dict) else bullet
                entries.append(f'<div class="education-entry">{t}</div>')
            sections_html.append(
                f'<div class="section-title">{title}</div>'
                f'{"".join(entries)}'
            )
            continue

        section_html = f'<div class="section-title">{title}</div>'

        for i, bullet in enumerate(bullets):
            text = bullet.get("text", bullet) if isinstance(bullet, dict) else bullet
            bullet_text = text
            is_role = isinstance(bullet, dict) and bullet.get("is_role_title")

            if optimized_bullets:
                for opt in optimized_bullets:
                    if opt.get("section") == title and opt.get("bullet_index") == i:
                        bullet_text = opt.get("optimized", text)
                        break

            if not bullet_text or not bullet_text.strip():
                continue

            if is_role:
                section_html += f'<div class="role-title">{bullet_text}</div>'
            else:
                section_html += f'<div class="bullet">{bullet_text}</div>'

        sections_html.append(section_html)

    skills = structured_data.get("skills_detected", {}) or {}
    hard_skills = skills.get("hard", [])
    existing_skill_titles = [s.get("title", "").lower() for s in structured_data.get("sections", [])]
    if hard_skills and not any(t in ("skills", "technical skills", "core competencies") for t in existing_skill_titles):
        sections_html.append(
            f'<div class="section-title">Skills</div>'
            f'<div class="skills-line">{", ".join(hard_skills)}</div>'
        )

    education = structured_data.get("education", []) or []
    if education:
        has_edu_section = any(t.lower() in ("education", "academics") for t in (s.get("title", "") for s in structured_data.get("sections", [])))
        if not has_edu_section:
            edu_html = '<div class="section-title">Education</div>'
            for edu in education:
                degree = edu.get("degree", "")
                school = edu.get("school", "")
                year = edu.get("year", "")
                parts = [p for p in [degree, school, str(year) if year else ""] if p]
                edu_html += f'<div class="education-entry">{" — ".join(parts)}</div>'
            sections_html.append(edu_html)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{css}</style></head>
<body>
<div class="header">
    <div class="name">{name or ""}</div>
    <div class="contact">{contact_line}</div>
</div>
{"".join(sections_html)}
</body></html>"""


async def generate_pdf(optimization_id: str, structured_data: dict, optimized_bullets: list[dict] | None = None, template: str = "modern") -> str:
    from weasyprint import HTML

    html = build_resume_html(structured_data, optimized_bullets, template)
    suffix = f"_{template}" if template != "modern" else ""
    output_path = os.path.join(settings.UPLOAD_DIR, f"{optimization_id}{suffix}.pdf")

    HTML(string=html).write_pdf(output_path)
    return output_path


def build_cover_letter_html(full_name: str, contact_info: str, body: str) -> str:
    paragraphs = body.split("\n\n")
    body_html = "".join(f"<p>{p.strip()}</p>" for p in paragraphs if p.strip())

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>
    @page {{ size: letter; margin: 1in; }}
    body {{ font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 11pt; line-height: 1.5; color: #1a1a1a; }}
    .name {{ font-size: 16pt; font-weight: bold; margin-bottom: 2pt; }}
    .contact {{ font-size: 10pt; color: #555; margin-bottom: 16pt; }}
    p {{ margin-bottom: 8pt; text-align: justify; }}
</style></head><body>
<div class="name">{full_name}</div>
<div class="contact">{contact_info}</div>
{body_html}
</body></html>"""


async def generate_cover_letter_pdf(
    optimization_id: str,
    full_name: str,
    contact_info: str,
    body: str,
) -> str:
    from weasyprint import HTML

    html = build_cover_letter_html(full_name, contact_info, body)
    output_path = os.path.join(settings.UPLOAD_DIR, f"{optimization_id}_cover.pdf")

    HTML(string=html).write_pdf(output_path)
    return output_path


def _flatten_bullets(structured_data: dict, optimized_bullets: list[dict] | None = None) -> list[dict]:
    items = []
    for section in structured_data.get("sections", []):
        title = section.get("title", "").strip()
        if not title:
            continue
        items.append({"type": "section", "text": title})
        for i, bullet in enumerate(section.get("bullets", [])):
            text = bullet.get("text", bullet) if isinstance(bullet, dict) else bullet
            is_role = isinstance(bullet, dict) and bullet.get("is_role_title")

            if optimized_bullets:
                for opt in optimized_bullets:
                    if opt.get("section") == title and opt.get("bullet_index") == i:
                        text = opt.get("optimized", text)
                        break

            if not text or not text.strip():
                continue

            if is_role:
                items.append({"type": "role", "text": text})
            else:
                items.append({"type": "bullet", "text": text})

    skills = structured_data.get("skills_detected", {}) or {}
    hard_skills = skills.get("hard", [])
    existing_skill_titles = [s.get("title", "").lower() for s in structured_data.get("sections", [])]
    if hard_skills and not any(t in ("skills", "technical skills", "core competencies") for t in existing_skill_titles):
        items.append({"type": "section", "text": "Skills"})
        items.append({"type": "skills", "text": ", ".join(hard_skills)})

    education = structured_data.get("education", []) or []
    if education:
        has_edu_section = any(t.lower() in ("education", "academics") for t in (s.get("title", "") for s in structured_data.get("sections", [])))
        if not has_edu_section:
            items.append({"type": "section", "text": "Education"})
            for edu in education:
                degree = edu.get("degree", "")
                school = edu.get("school", "")
                year = edu.get("year", "")
                parts = [p for p in [degree, school, str(year) if year else ""] if p]
                items.append({"type": "bullet", "text": " — ".join(parts)})

    return items


def _set_bottom_border(paragraph, color: str = "2C3E50", size_pt: float = 1.0, space: int = 2) -> None:
    """Draw a bottom rule under a paragraph (mirrors the PDF's border-bottom)."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    pPr = paragraph._p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), str(max(2, int(round(size_pt * 8)))))  # eighths of a point
    bottom.set(qn("w:space"), str(space))
    bottom.set(qn("w:color"), color)
    pBdr.append(bottom)
    pPr.insert_element_before(pBdr, "w:shd", "w:tabs", "w:spacing", "w:ind", "w:jc", "w:rPr")


def _set_char_spacing(run, points: float) -> None:
    """Letter-spacing in twips (1/20 pt), matching the PDF's letter-spacing."""
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    rPr = run._element.get_or_add_rPr()
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:val"), str(int(round(points * 20))))
    rPr.append(spacing)


async def generate_docx(optimization_id: str, structured_data: dict, optimized_bullets: list[dict] | None = None) -> str:
    """Build the DOCX to match the 'modern' PDF template (navy rules, matching type scale)."""
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    NAVY = RGBColor(0x2C, 0x3E, 0x50)
    GREY = RGBColor(0x55, 0x55, 0x55)
    INK = RGBColor(0x1A, 0x1A, 0x1A)

    doc = Document()

    section = doc.sections[0]
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.75)
    section.right_margin = Inches(0.75)

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(10.5)
    style.font.color.rgb = INK
    style.paragraph_format.space_after = Pt(2)
    style.paragraph_format.space_before = Pt(0)
    style.paragraph_format.line_spacing = 1.15

    name = structured_data.get("full_name", "") or ""
    email = structured_data.get("email", "")
    phone = structured_data.get("phone", "")
    location = structured_data.get("location", "")
    linkedin = structured_data.get("linkedin", "")
    contact_parts = [p for p in [email, phone, location, linkedin] if p]
    contact_line = "  |  ".join(contact_parts)

    name_para = doc.add_paragraph()
    name_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    name_para.paragraph_format.space_after = Pt(2)
    run = name_para.add_run(name)
    run.bold = True
    run.font.size = Pt(16)
    run.font.name = "Arial"
    run.font.color.rgb = INK

    if contact_line:
        contact_para = doc.add_paragraph()
        contact_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        contact_para.paragraph_format.space_after = Pt(8)
        run = contact_para.add_run(contact_line)
        run.font.size = Pt(9)
        run.font.name = "Arial"
        run.font.color.rgb = GREY
        _set_bottom_border(contact_para, "2C3E50", 1.5, 6)
    elif name:
        _set_bottom_border(name_para, "2C3E50", 1.5, 6)

    items = _flatten_bullets(structured_data, optimized_bullets)
    EDU_TITLES = ("education", "academics")
    SKILL_TITLES = ("skills", "technical skills", "core competencies")
    i = 0
    while i < len(items):
        item = items[i]

        if item["type"] == "section":
            title = item["text"].strip()
            key = title.lower()

            para = doc.add_paragraph()
            para.paragraph_format.space_before = Pt(12)
            para.paragraph_format.space_after = Pt(5)
            run = para.add_run(title.upper())
            run.bold = True
            run.font.size = Pt(11)
            run.font.name = "Arial"
            run.font.color.rgb = NAVY
            _set_char_spacing(run, 0.8)
            _set_bottom_border(para, "2C3E50", 0.8, 2)
            i += 1

            if key in SKILL_TITLES:
                buf = []
                while i < len(items) and items[i]["type"] != "section":
                    buf.append(items[i]["text"])
                    i += 1
                if buf:
                    p = doc.add_paragraph(", ".join(buf))
                    p.paragraph_format.line_spacing = 1.3
                continue

            if key in EDU_TITLES:
                while i < len(items) and items[i]["type"] != "section":
                    p = doc.add_paragraph(items[i]["text"])
                    p.paragraph_format.left_indent = Inches(0.17)
                    p.paragraph_format.space_after = Pt(1)
                    i += 1
                continue

            continue

        if item["type"] == "role":
            para = doc.add_paragraph()
            para.paragraph_format.space_before = Pt(6)
            para.paragraph_format.space_after = Pt(1)
            run = para.add_run(item["text"])
            run.bold = True
            run.font.size = Pt(10.5)
            run.font.color.rgb = INK
        elif item["type"] == "skills":
            para = doc.add_paragraph(item["text"])
            para.paragraph_format.left_indent = Inches(0)
            para.paragraph_format.line_spacing = 1.3
        else:
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Inches(0.17)
            para.paragraph_format.first_line_indent = Inches(-0.17)
            para.paragraph_format.space_after = Pt(3)
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            bullet_run = para.add_run("\u2022  ")
            bullet_run.font.color.rgb = NAVY
            para.add_run(item["text"])
        i += 1

    output_path = os.path.join(settings.UPLOAD_DIR, f"{optimization_id}.docx")
    doc.save(output_path)
    return output_path


async def generate_txt(optimization_id: str, structured_data: dict, optimized_bullets: list[dict] | None = None) -> str:
    name = structured_data.get("full_name", "")
    email = structured_data.get("email", "")
    phone = structured_data.get("phone", "")
    location = structured_data.get("location", "")
    linkedin = structured_data.get("linkedin", "")
    contact_parts = [p for p in [email, phone, location, linkedin] if p]
    contact_line = "  |  ".join(contact_parts)

    lines = [name, contact_line, ""]

    items = _flatten_bullets(structured_data, optimized_bullets)
    for item in items:
        if item["type"] == "section":
            lines.append("")
            lines.append(item["text"].upper())
            lines.append("-" * len(item["text"]))
        elif item["type"] == "role":
            lines.append("")
            lines.append(item["text"])
        elif item["type"] == "skills":
            lines.append(item["text"])
        else:
            lines.append(f"  \u2022 {item['text']}")

    output_path = os.path.join(settings.UPLOAD_DIR, f"{optimization_id}.txt")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path
