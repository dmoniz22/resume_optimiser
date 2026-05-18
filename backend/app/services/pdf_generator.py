import os
from app.config import settings

PDF_STYLES = """
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
        font-size: 18pt;
        font-weight: 700;
        margin-bottom: 3pt;
        color: #1a1a1a;
    }
    .contact {
        font-size: 9.5pt;
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
    .bullet::before { content: "• "; color: #2c3e50; }
    .skills-line {
        margin-top: 2pt;
        line-height: 1.5;
    }
    .education-entry {
        margin-bottom: 1pt;
        padding-left: 12pt;
    }
"""


def build_resume_html(structured_data: dict, optimized_bullets: list[dict] | None = None) -> str:
    name = structured_data.get("full_name", "")
    email = structured_data.get("email", "")
    phone = structured_data.get("phone", "")
    location = structured_data.get("location", "")

    contact_parts = []
    if email:
        contact_parts.append(email)
    if phone:
        contact_parts.append(phone)
    if location:
        contact_parts.append(location)
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

            if optimized_bullets:
                for opt in optimized_bullets:
                    if opt.get("section") == title and opt.get("bullet_index") == i:
                        bullet_text = opt.get("optimized", text)
                        break

            if not bullet_text or not bullet_text.strip():
                continue
            section_html += f'<div class="bullet">{bullet_text}</div>'

        sections_html.append(section_html)

    skills = structured_data.get("skills_detected", {}) or {}
    hard_skills = skills.get("hard", [])
    if hard_skills and not any(s.lower() in ("skills", "technical skills", "core competencies") for s in (s_.get("title", "") for s_ in structured_data.get("sections", []))):
        sections_html.append(
            f'<div class="section-title">Skills</div>'
            f'<div class="skills-line">{", ".join(hard_skills)}</div>'
        )

    education = structured_data.get("education", []) or []
    if education:
        edu_html = '<div class="section-title">Education</div>'
        for edu in education:
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")
            parts = [p for p in [degree, school, str(year) if year else ""] if p]
            edu_html += f'<div class="education-entry">{" — ".join(parts)}</div>'
        sections_html.append(edu_html)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{PDF_STYLES}</style></head>
<body>
<div class="header">
    <div class="name">{name or ""}</div>
    <div class="contact">{contact_line}</div>
</div>
{"".join(sections_html)}
</body></html>"""


async def generate_pdf(optimization_id: str, structured_data: dict, optimized_bullets: list[dict] | None = None) -> str:
    from weasyprint import HTML

    html = build_resume_html(structured_data, optimized_bullets)
    output_path = os.path.join(settings.UPLOAD_DIR, f"{optimization_id}.pdf")

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
