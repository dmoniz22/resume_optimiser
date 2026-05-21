import json
import re
from collections import OrderedDict
import fitz
from docx import Document
from app.config import settings
from app.services.llm_client import get_llm_client

EXTRACT_META_PROMPT = """Extract basic metadata from this resume. Output ONLY valid JSON.

{{
  "full_name": "string or null",
  "email": "string or null", 
  "phone": "string or null",
  "location": "string or null",
  "years_of_experience": 5.0,
  "skills_detected": {{"hard": ["skill1"], "soft": ["skill1"]}},
  "education": [{{"degree": "string", "school": "string", "year": 2020}}]
}}

Resume text:
{text}"""


def is_education_line(line: str) -> bool:
    patterns = [
        r"(?i)^(master|bachelor|doctor|phd|fellowship|certificate|diploma) of",
        r"(?i)^(facrr[m]?|jcca)\b",
        r"(?i)^(rural and remote medicine|general practice)",
        r"(?i)\b(university of|college of|institute of|school of)",
    ]
    return any(re.search(p, line) for p in patterns)


def is_role_start(line: str) -> bool:
    """Detect lines that start a new job role within Professional Experience."""
    has_date = bool(re.search(r"\b\d{2}/\d{4}\b|\b\d{4}\s*[–-]\s*\d{4}\b|\bcurrent\b|\bpresent\b", line, re.IGNORECASE))
    has_org = bool(re.search(r",\s*(.+)$", line))  # has a comma followed by organization
    has_title = bool(re.search(
        r"(?i)\b(head|director|physician|registrar|instructor|officer|practitioner|specialist|surgeon|nurse|anesthetist|lecturer|educator|fellow|intern|resident|manager|lead|coordinator|supervisor|general|staff|chair|honorary|adjunct|non-executive|board)\b",
        line
    ))
    is_short = 15 < len(line) < 200
    return (has_date and has_title) or (has_title and has_org and is_short)


def is_membership_line(line: str) -> bool:
    patterns = [
        r"(?i)^member\b",
        r"(?i)^registered with\b",
        r"(?i)\b(member of|member,)\b",
    ]
    return any(re.search(p, line) for p in patterns)


def is_certification_line(line: str) -> bool:
    patterns = [
        r"(?i)\b(instructor|advanced life support|management of|early management|practical obstetric|pre-hospital|crisis management|effective management)\b",
    ]
    return any(re.search(p, line) for p in patterns)


def is_publication_line(line: str) -> bool:
    patterns = [
        r"\(\d{4}\)",  # (2009)
        r"(?i)\b(j\.\s|journal\b|neurosci|society for|publication|refereed)",
    ]
    return any(re.search(p, line) for p in patterns)


def is_presentation_line(line: str) -> bool:
    patterns = [
        r"(?i)\b(presentation|conference|society for|annual meeting)\b",
    ]
    return any(re.search(p, line) for p in patterns)


def is_volunteer_line(line: str) -> bool:
    patterns = [
        r"(?i)^(scouts|st john|ambulance|troop|cub|division,)",
        r"(?i)(scout|venturer|volunteer)",
    ]
    return any(re.search(p, line) for p in patterns)


def extract_text_from_pdf(file_path: str) -> str:
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


async def parse_resume_text(raw_text: str) -> dict:
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    if not lines:
        return {}

    sections = []
    i = 0

    # --- Professional Summary (first paragraph) ---
    if lines[0] and len(lines[0]) > 100 and not is_education_line(lines[0]) and not is_role_start(lines[0]):
        summary_bullets = [{"text": lines[0], "is_quantified": False}]
        # Include any continuation lines (short lines that aren't patterns)
        i = 1
        while i < len(lines) and not is_education_line(lines[i]) and not is_role_start(lines[i]) and not is_membership_line(lines[i]):
            if len(lines[i]) > 30:
                summary_bullets.append({"text": lines[i], "is_quantified": False})
            i += 1
        sections.append({"title": "Professional Summary", "bullets": summary_bullets})
    else:
        i = 0

    # --- Education (max ~30 lines) ---
    edu_bullets = []
    edu_count = 0
    while i < len(lines) and edu_count < 30 and (is_education_line(lines[i]) or (edu_bullets and not is_role_start(lines[i]) and not is_membership_line(lines[i]) and not is_certification_line(lines[i]) and not is_publication_line(lines[i]) and not is_presentation_line(lines[i]) and not is_volunteer_line(lines[i]))):
        edu_bullets.append({"text": lines[i], "is_quantified": False})
        i += 1
        edu_count += 1
    if edu_bullets:
        sections.append({"title": "Education", "bullets": edu_bullets})

    # --- Professional Experience (with role sub-sections) ---
    exp_bullets = []
    while i < len(lines):
        line = lines[i]
        
        # Check if we've hit a non-experience section
        if is_membership_line(line) or is_certification_line(line) or is_publication_line(line) or is_presentation_line(line) or is_volunteer_line(line):
            # Check if this is a cluster start (at least 2 lines of the new type)
            j = i
            cluster_count = 0
            while j < len(lines) and j < i + 5:
                if is_membership_line(lines[j]): cluster_count += 1
                elif is_certification_line(lines[j]): cluster_count += 1
                elif is_publication_line(lines[j]): cluster_count += 1
                elif is_presentation_line(lines[j]): cluster_count += 1
                elif is_volunteer_line(lines[j]): cluster_count += 1
                j += 1
            if cluster_count >= 2:
                break
        
        if is_role_start(line):
            exp_bullets.append({"text": f"── {line} ──", "is_quantified": False})
        else:
            exp_bullets.append({"text": line, "is_quantified": False})
        i += 1
    
    if exp_bullets:
        sections.append({"title": "Professional Experience", "bullets": exp_bullets})

    # --- Remaining sections ---
    remaining = []
    while i < len(lines):
        remaining.append({"text": lines[i], "is_quantified": False})
        i += 1

    if remaining:
        # Classify remaining into sub-sections
        sub_sections = OrderedDict()
        current_type = None
        
        for b in remaining:
            line = b["text"]
            if is_membership_line(line):
                current_type = "Professional Memberships"
            elif is_certification_line(line):
                current_type = "Certifications"
            elif is_publication_line(line):
                current_type = "Publications"
            elif is_presentation_line(line):
                current_type = "Presentations"
            elif is_volunteer_line(line):
                current_type = "Volunteer Experience"
            
            stype = current_type or "Other"
            if stype not in sub_sections:
                sub_sections[stype] = []
            sub_sections[stype].append(b)
        
        for title, bullets in sub_sections.items():
            if bullets:
                sections.append({"title": title, "bullets": bullets})

    # AI metadata extraction
    try:
        client = get_llm_client()
        resp = client.chat.completions.create(
            model=settings.AI_MODEL_EXTRACT,
            messages=[
                {"role": "system", "content": "Output ONLY valid JSON."},
                {"role": "user", "content": EXTRACT_META_PROMPT.format(text=raw_text[:3000])},
            ],
            temperature=0.1,
            max_tokens=2048,
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rstrip("```")
        meta = json.loads(content)
    except Exception:
        meta = {}

    return {
        "full_name": meta.get("full_name"),
        "email": meta.get("email"),
        "phone": meta.get("phone"),
        "location": meta.get("location"),
        "sections": sections,
        "skills_detected": meta.get("skills_detected", {"hard": [], "soft": []}),
        "years_of_experience": meta.get("years_of_experience"),
        "education": meta.get("education", []),
    }


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")
