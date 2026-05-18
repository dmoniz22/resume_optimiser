import uuid
import os
from app.config import settings

PDF_STYLES = """
    @page {
        size: letter;
        margin: 0.75in 1in;
    }
    body {
        font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
        font-size: 11pt;
        line-height: 1.4;
        color: #1a1a1a;
    }
    .header {
        text-align: center;
        margin-bottom: 12pt;
    }
    .name {
        font-size: 24pt;
        font-weight: bold;
        margin-bottom: 4pt;
    }
    .contact {
        font-size: 10pt;
        color: #555;
    }
    .contact span { margin: 0 8pt; }
    .section-title {
        font-size: 12pt;
        font-weight: bold;
        border-bottom: 1.5px solid #333;
        padding-bottom: 3pt;
        margin-top: 16pt;
        margin-bottom: 6pt;
        text-transform: uppercase;
        letter-spacing: 1pt;
    }
    .bullet {
        margin-bottom: 4pt;
        padding-left: 14pt;
        text-indent: -14pt;
    }
    .bullet::before { content: "• "; }
    .skill-tag {
        display: inline-block;
        margin-right: 6pt;
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
    contact_line = " | ".join(contact_parts)

    sections_html = []

    for section in structured_data.get("sections", []):
        title = section.get("title", "")
        bullets = section.get("bullets", [])

        section_html = f'<div class="section-title">{title}</div>'

        for i, bullet in enumerate(bullets):
            text = bullet.get("text", bullet) if isinstance(bullet, dict) else bullet
            bullet_text = text

            if optimized_bullets:
                for opt in optimized_bullets:
                    if opt.get("section") == title and opt.get("bullet_index") == i:
                        bullet_text = opt.get("optimized", text)
                        break

            section_html += f'<div class="bullet">{bullet_text}</div>'

        sections_html.append(section_html)

    skills = structured_data.get("skills_detected", {}) or {}
    hard_skills = skills.get("hard", [])
    if hard_skills:
        skills_html = '<div class="section-title">Skills</div><div>'
        skills_html += ", ".join(hard_skills)
        skills_html += "</div>"
        sections_html.append(skills_html)

    education = structured_data.get("education", []) or []
    if education:
        edu_html = '<div class="section-title">Education</div>'
        for edu in education:
            degree = edu.get("degree", "")
            school = edu.get("school", "")
            year = edu.get("year", "")
            edu_html += f'<div class="bullet">{degree} — {school}{" (" + str(year) + ")" if year else ""}</div>'
        sections_html.append(edu_html)

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><style>{PDF_STYLES}</style></head>
<body>
<div class="header">
    <div class="name">{name}</div>
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
    p {{ margin-bottom: 8pt; }}
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
