import json
import re
import fitz
from docx import Document
from app.config import settings
from app.services.llm_client import get_llm_client

PARSE_STEP2_PROMPT = """Extract bullet points from this section of a resume. Output ONLY valid JSON.

Section: {section_title}

Rules:
1. Extract each distinct item as a separate bullet
2. Include job titles, dates, and organizations in bullet text
3. Preserve ALL factual content — names, dates, numbers
4. Do not invent or summarize — keep original wording

Output format:
{{
  "bullets": [
    {{"text": "bullet text preserving original wording", "is_quantified": false}}
  ]
}}

Section text:
{text}"""

EXTRACT_META_PROMPT = """Extract basic metadata from this resume header. Output ONLY valid JSON.

{{
  "full_name": "string or null",
  "email": "string or null", 
  "phone": "string or null",
  "location": "string or null",
  "years_of_experience": 5.0,
  "skills_detected": {{"hard": ["skill1"], "soft": ["skill1"]}},
  "education": [{{"degree": "string", "school": "string", "year": 2020}}]
}}

Resume header text:
{text}"""

SECTION_KEYWORDS = [
    ("summary", "professional summary", "profile", "objective"),
    ("education", "academic background", "training"),
    ("licensure", "certification", "license", "board certification"),
    ("professional experience", "employment", "work history", "work experience", "experience"),
    ("teaching", "teaching experience", "academic appointments"),
    ("volunteer", "volunteer experience", "community service"),
    ("committee", "committee memberships", "leadership"),
    ("membership", "professional memberships", "affiliations"),
    ("publication", "refereed publications", "research", "papers"),
    ("presentation", "presentations", "conferences", "invited talks"),
    ("award", "honors", "achievements", "honours"),
    ("skill", "technical skills", "clinical skills", "core competencies"),
    ("language", "languages"),
    ("reference", "references"),
]


def detect_sections(lines: list[str]) -> list[dict]:
    sections = []
    current_start = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
            
        line_lower = stripped.lower().rstrip(":").rstrip(".")
        
        is_header = False
        
        # Bold markers from docx extraction
        if stripped.startswith("## "):
            is_header = True
            stripped = stripped[3:]
        # ALL_CAPS headers (but not acronyms)
        elif stripped.isupper() and len(stripped) >= 5 and sum(1 for c in stripped if c in 'AEIOU') >= 1:
            is_header = True
        # Lines ending with colon
        elif stripped.endswith(":") and len(stripped) < 50:
            is_header = True
        # Keyword match
        else:
            for group in SECTION_KEYWORDS:
                for kw in group:
                    if line_lower == kw or line_lower.rstrip("s") == kw:
                        is_header = True
                        break
                    if kw.count(" ") >= 2 and line_lower.startswith(kw + " ") and len(line_lower) < 60:
                        is_header = True
                        break
                if is_header:
                    break
        
        if is_header and i > current_start:
            title = stripped.rstrip(":")
            sections.append({"title": title, "start": current_start, "end": i})
            current_start = i
    
    # Last section
    if current_start < len(lines):
        title = lines[current_start].strip().rstrip(":")
        sections.append({"title": title, "start": current_start, "end": len(lines)})
    
    return sections


JOB_TITLE_PATTERNS = [
    r"(?i)registrar\b", r"(?i)resident\b", r"(?i)physician\b", r"(?i)doctor\b",
    r"(?i)surgeon\b", r"(?i)nurse\b", r"(?i)director\b", r"(?i)manager\b",
    r"(?i)coordinator\b", r"(?i)supervisor\b", r"(?i)instructor\b", r"(?i)professor\b",
    r"(?i)officer\b", r"(?i)head\b", r"(?i)lead\b", r"(?i)chair\b", r"(?i)chief\b",
    r"(?i)interim\b", r"(?i)senior\b", r"(?i)junior\b", r"(?i)associate\b",
    r"(?i)clinical\b", r"(?i)medical\b", r"(?i)fellow\b",
]


def is_job_title(text: str) -> bool:
    text = text.replace("## ", "")
    for pattern in JOB_TITLE_PATTERNS:
        if re.search(pattern, text):
            return True
    return False


def merge_sections(sections: list[dict], lines: list[str]) -> list[dict]:
    if not sections:
        return []
    
    merged = [sections[0]]
    
    for s in sections[1:]:
        title = s["title"]
        prev = merged[-1]
        
        # If this looks like a job title, merge into previous section
        if is_job_title(title) and not any(kw in title.lower() for kw in ["publication", "presentation", "education", "certification", "licensure", "award", "skill"]):
            prev["end"] = s["end"]
            continue
        
        # If previous section is a job title and this one is too, merge
        if is_job_title(prev["title"]) and is_job_title(title):
            prev["end"] = s["end"]
            continue
        
        merged.append(s)
    
    # Rename the first large section to the right name
    if merged:
        first = merged[0]
        lines_section = lines[first["start"]:first["end"]]
        text = " ".join(lines_section).lower()
        
        if any(kw in text for kw in ["professional experience", "employment", "work experience"]):
            first["title"] = "Professional Experience"
        elif any(kw in text for kw in ["education", "degree", "bachelor", "master", "university"]):
            first["title"] = "Education"
        elif any(kw in text for kw in ["summary", "profile"]):
            first["title"] = "Professional Summary"
    
    return merged


def extract_text_from_pdf(file_path: str) -> str:
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def extract_text_from_docx(file_path: str) -> str:
    """Extract text preserving bold formatting as section headers (marked with ##)."""
    doc = Document(file_path)
    lines = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            lines.append("")
            continue
        # Check if paragraph has bold formatting (common for section headers)
        is_bold = any(run.bold for run in p.runs if run.text.strip())
        if is_bold and len(text) < 80:
            lines.append(f"## {text}")
        else:
            lines.append(text)
    return "\n".join(lines)


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


async def parse_resume_text(raw_text: str) -> dict:
    client = get_llm_client()
    lines = raw_text.split("\n")
    
    # Step 1: Python section detection
    raw_sections = detect_sections(lines)
    
    # Merge job titles into parent sections
    raw_sections = merge_sections(raw_sections, lines)
    
    # Step 2: AI parse each section
    parsed_sections = []
    for rs in raw_sections:
        start, end = rs["start"], rs["end"]
        title = rs["title"]
        section_lines = lines[start:end]
        section_text = "\n".join(section_lines)
        
        non_empty = [l for l in section_lines if l.strip() and not l.strip().startswith("## ")]
        if len(non_empty) < 2 or len(section_text) < 50:
            continue
        
        try:
            resp = client.chat.completions.create(
                model=settings.AI_MODEL_PARSE,
                messages=[
                    {"role": "system", "content": "Output ONLY valid JSON."},
                    {"role": "user", "content": PARSE_STEP2_PROMPT.format(section_title=title, text=section_text[:6000])},
                ],
                temperature=0.1,
                max_tokens=4096,
            )
            content = resp.choices[0].message.content.strip()
            if content.startswith("```"):
                content = content.split("\n", 1)[1].rstrip("```")
            result = json.loads(content)
            parsed_sections.append({
                "title": title,
                "bullets": result.get("bullets", []),
            })
        except Exception:
            bullets = [{"text": l, "is_quantified": False} for l in section_lines if l.strip() and not l.strip().startswith("## ") and len(l.strip()) > 2]
            parsed_sections.append({"title": title, "bullets": bullets})
    
    # Step 3: Metadata extraction from header
    header = "\n".join(lines[:40])[:3000]
    try:
        resp = client.chat.completions.create(
            model=settings.AI_MODEL_EXTRACT,
            messages=[
                {"role": "system", "content": "Output ONLY valid JSON."},
                {"role": "user", "content": EXTRACT_META_PROMPT.format(text=header)},
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
        "sections": parsed_sections,
        "skills_detected": meta.get("skills_detected", {"hard": [], "soft": []}),
        "years_of_experience": meta.get("years_of_experience"),
        "education": meta.get("education", []),
    }


def clean_sections(parsed: dict) -> dict:
    return parsed


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")
