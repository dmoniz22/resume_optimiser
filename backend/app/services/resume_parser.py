import json
import re
from collections import Counter
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

SECTION_PATTERNS = [
    ("Education", [
        r"(?i)^(master|bachelor|doctor|phd|fellowship|certificate|diploma) of",
        r"(?i)^(medical school|university|college) of",
        r"(?i)^(facrr[m]?|jcca)\b",
    ]),
    ("Professional Experience", [
        r"(?i)\b(head|director|physician|registrar|instructor|officer|practitioner|specialist|surgeon|nurse|anesthetist|lecturer)\b",
        r"(?i)\b(interim|clinical|medical|staff)\b",
    ]),
    ("Professional Memberships", [
        r"(?i)^member\b",
        r"(?i)^registered with\b",
        r"(?i)\b(member of|member,)\b",
    ]),
    ("Certifications", [
        r"(?i)\b(instructor|advanced|management|training|certified)\b",
    ]),
    ("Publications", [
        r"(?i)\b(moniz| \(\d{4}\) |j\.\s|journal\b|neurosci|society for)",
    ]),
    ("Presentations", [
        r"(?i)\b(presentation|conference|society for|annual meeting)",
    ]),
    ("Volunteer Experience", [
        r"(?i)^(scouts|st john|ambulance|troop|cub|division)",
    ]),
]


def classify_line(line: str) -> str:
    for section_name, patterns in SECTION_PATTERNS:
        for pat in patterns:
            if re.search(pat, line):
                return section_name
    return ""


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

    # Classify every line
    classified = [(classify_line(line) or "", line) for line in lines]
    
    # Determine dominant section type in sliding windows (smooth changes)
    window = 3
    smoothed = []
    for i in range(len(classified)):
        window_types = [classified[j][0] for j in range(max(0, i-window), min(len(classified), i+window+1)) if classified[j][0]]
        if window_types:
            from collections import Counter
            most_common = Counter(window_types).most_common(1)[0][0]
            smoothed.append(most_common)
        else:
            smoothed.append("")
    
    # Build sections from smoothed classifications
    sections = []
    current_type = None
    current_lines = []
    
    for i, (stype, line) in enumerate(zip(smoothed, [c[1] for c in classified])):
        if stype and stype != current_type:
            if current_lines:
                sections.append({"title": current_type or "Professional Summary", "bullets": current_lines})
            current_type = stype
            current_lines = [{"text": line, "is_quantified": False}]
        else:
            if not current_type:
                current_type = "Professional Summary"
            current_lines.append({"text": line, "is_quantified": False})
    
    if current_lines:
        sections.append({"title": current_type or "Professional Summary", "bullets": current_lines})
    
    # Merge tiny sections (< 3 bullets) into neighbors
    # Also merge adjacent sections of the same type
    merged = []
    for s in sections:
        if len(s["bullets"]) < 3 and merged:
            merged[-1]["bullets"].extend(s["bullets"])
        elif merged and merged[-1]["title"] == s["title"]:
            merged[-1]["bullets"].extend(s["bullets"])
        else:
            merged.append(s)
    sections = merged
    
    # Second pass: merge sections of same type that got separated
    final = []
    for s in sections:
        if final and final[-1]["title"] == s["title"]:
            final[-1]["bullets"].extend(s["bullets"])
        else:
            final.append(s)
    sections = final
    
    # Third pass: merge Professional Memberships and Certifications into
    # Professional Experience if they have < 5 bullets (probably inline mentions)
    experience_idx = None
    cleaned = []
    for s in sections:
        if s["title"] == "Professional Experience":
            experience_idx = len(cleaned)
            cleaned.append(s)
        elif s["title"] in ("Professional Memberships", "Certifications") and len(s["bullets"]) < 5 and experience_idx is not None:
            cleaned[experience_idx]["bullets"].extend(s["bullets"])
        else:
            experience_idx = None
            cleaned.append(s)
    sections = cleaned

    # Consolidate: merge all same-title sections into one
    from collections import OrderedDict
    consolidated: OrderedDict = OrderedDict()
    section_order = []
    for s in sections:
        title = s["title"]
        if title not in consolidated:
            consolidated[title] = []
            section_order.append(title)
        consolidated[title].extend(s["bullets"])
    sections = [{"title": t, "bullets": consolidated[t]} for t in section_order]

    # AI metadata extraction from first 3000 chars
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
