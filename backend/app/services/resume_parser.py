import json
import logging
import re
from collections import OrderedDict
import fitz
from docx import Document
from app.config import settings
from app.services.llm_client import get_llm_client
import asyncio

logger = logging.getLogger(__name__)

# Lines that look like a person name are never section headings or contact rows.
_NAME_BLOCKLIST = re.compile(
    r"(?i)\b(resume|curriculum|vitae|profile|summary|experience|education|skills|"
    r"references|contact|linkedin|github|page\s+\d)\b"
)
_NAME_TOKEN = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ'’.\-]+$")


def guess_header_fields(raw_text: str) -> dict:
    """Deterministic fallback for the resume header (name/email/phone/location/linkedin).

    The LLM extraction can fail (dead key, retired model, malformed JSON) and its
    exception is swallowed upstream. Without a fallback the generated resume loses
    the candidate's name and contact block entirely, so always keep a regex path.
    """
    text = raw_text or ""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    head = lines[:15]

    linkedin = None
    m = re.search(
        r"(?i)(?:https?://)?(?:[a-z]{2,3}\.)?(?:www\.)?linkedin\.com/(?:in|pub)/[A-Za-z0-9\-_%.]+",
        text,
    )
    if m:
        linkedin = re.sub(r"(?i)^(https?://)?(www\.)?", "", m.group(0)).rstrip("/")

    email = None
    m = re.search(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", text)
    if m:
        email = m.group(0)

    phone = None
    for ln in head:
        # Contact rows often hold email + phone on one line, so strip non-phone tokens first.
        cleaned = re.sub(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}", " ", ln)
        cleaned = re.sub(r"(?i)(https?://\S+|www\.\S+|linkedin\S*)", " ", cleaned)
        m = re.search(r"(?<![\w/])(\+?\d[\d\s().\-]{6,}\d)(?![\w/])", cleaned)
        if not m:
            continue
        digits = re.sub(r"\D", "", m.group(1))
        if 7 <= len(digits) <= 15:
            phone = m.group(1).strip()
            break

    location = None
    institution = re.compile(r"(?i)\b(institute|university|college|hospital|clinic|school|directors|ltd|inc|corp|group)\b")
    for ln in head[:6]:
        cand = ln.strip()
        if "@" in cand or len(cand) > 60 or institution.search(cand):
            continue
        parts = [p.strip() for p in cand.split(",")]
        if len(parts) < 2 or len(parts[0].split()) > 4:
            continue
        has_postal = re.search(r"\b[A-Z]\d[A-Z]\s?\d[A-Z]\d\b", cand) is not None  # Canadian
        has_state = any(re.fullmatch(r"[A-Z]{2}", p) or re.fullmatch(r"[A-Z]{2}\s+\d{5}", p) for p in parts[1:])
        if has_postal or has_state:
            location = cand
            break

    full_name = None
    for ln in head:
        cand = ln.strip()
        if not (3 <= len(cand) <= 60) or "@" in cand or re.search(r"\d", cand):
            continue
        if _NAME_BLOCKLIST.search(cand):
            continue
        words = cand.split()
        if not (2 <= len(words) <= 5):
            continue
        if not all(_NAME_TOKEN.match(w) for w in words):
            continue
        titled = cand.title() if cand.isupper() else cand
        if not all(w[:1].isupper() for w in titled.split()):
            continue
        full_name = titled
        break

    return {"full_name": full_name, "email": email, "phone": phone,
            "location": location, "linkedin": linkedin}


EXTRACT_META_PROMPT = """Extract basic metadata from this resume. Output ONLY valid JSON.

{{
  "full_name": "string or null",
  "email": "string or null", 
  "phone": "string or null",
  "location": "string or null",
  "linkedin": "linkedin.com/in/handle or null",
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
        r"(?i)^(rural and remote medicine|general practice)\b",
    ]
    return any(re.search(p, line) for p in patterns)


def is_role_start(line: str) -> bool:
    """Detect lines that start a new job role."""
    has_date = bool(re.search(r"\b\d{2}/\d{4}\b|\b\d{4}\s*[–-]\s*\d{4}\b|\bcurrent\b|\bpresent\b", line, re.IGNORECASE))
    has_org = bool(re.search(r",\s*.+", line))
    # Only match CLEAR job titles (first word is a title)
    first_word_title = bool(re.match(
        r"(?i)^\s*(head|director|physician|registrar|instructor|officer|practitioner|specialist|surgeon|anesthetist|lecturer|educator|fellow|intern|resident|coordinator|supervisor|chair|honorary|adjunct|non-executive|board|interim|general|staff|clinical|medical|rural|emergency|telehealth)\b",
        line
    ))
    is_short = 15 < len(line) < 200
    return (has_date or has_org) and first_word_title and is_short


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


def _docx_paragraph_lines(element) -> list[str]:
    """Every paragraph inside an element, including table cells and text boxes.

    `doc.paragraphs` only walks top-level body paragraphs, which is why resumes
    with the name/contact block in a table, text box or header lost their header
    entirely on the way in.
    """
    from docx.oxml.ns import qn

    lines = []
    for para in element.iter(qn("w:p")):
        line = "".join(t.text or "" for t in para.iter(qn("w:t"))).strip()
        if line:
            lines.append(line)
    return lines


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    parts: list[str] = []
    seen: set[str] = set()

    def add(lines: list[str]) -> None:
        for line in lines:
            if line not in seen:
                seen.add(line)
                parts.append(line)

    # Headers/footers first: many CV templates put the name + contact block there.
    for section in doc.sections:
        for hf in (section.header, section.first_page_header, section.footer, section.first_page_footer):
            try:
                add(_docx_paragraph_lines(hf._element))
            except Exception:  # missing/linked header parts
                continue

    add(_docx_paragraph_lines(doc.element.body))
    return "\n".join(parts)


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
        
        # Only break on CLEAR section transitions (publications, presentations, volunteer clusters)
        if is_publication_line(line) or is_presentation_line(line) or is_volunteer_line(line):
            # Confirm it's a real cluster (at least 2 consecutive lines matching the new type)
            future_count = 0
            for j in range(i, min(i+5, len(lines))):
                if is_publication_line(lines[j]) or is_presentation_line(lines[j]) or is_volunteer_line(lines[j]):
                    future_count += 1
            if future_count >= 2:
                break
        
        if is_role_start(line):
            exp_bullets.append({"text": line, "is_role_title": True, "is_quantified": False})
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
    meta = {}
    try:
        client = get_llm_client()
        resp = await asyncio.to_thread(
            client.chat.completions.create,
            model=settings.AI_MODEL_EXTRACT,
            messages=[
                {"role": "system", "content": "Output ONLY valid JSON."},
                {"role": "user", "content": EXTRACT_META_PROMPT.format(text=raw_text[:3000])},
            ],
            temperature=0.1,
            max_tokens=4096,
        )
        content = (resp.choices[0].message.content or "").strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rstrip("`").strip()
        try:
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # Thinking models occasionally wrap the JSON in prose — salvage the object.
            match = re.search(r"\{.*\}", content, re.S)
            parsed = json.loads(match.group(0)) if match else {}
        meta = parsed if isinstance(parsed, dict) else {}
    except Exception as exc:  # never lose the header to a model/JSON failure
        logger.warning("AI metadata extraction failed (%s); using regex fallback", repr(exc)[:200])
        meta = {}

    fallback = guess_header_fields(raw_text)
    if not meta.get("full_name") or not meta.get("email"):
        logger.info("metadata fallback used: name=%s email=%s",
                    bool(fallback["full_name"]), bool(fallback["email"]))

    return {
        "full_name": meta.get("full_name") or fallback["full_name"],
        "email": meta.get("email") or fallback["email"],
        "phone": meta.get("phone") or fallback["phone"],
        "location": meta.get("location") or fallback["location"],
        "linkedin": meta.get("linkedin") or fallback["linkedin"],
        "sections": sections,
        "skills_detected": meta.get("skills_detected", {"hard": [], "soft": []}),
        "years_of_experience": meta.get("years_of_experience"),
        "education": meta.get("education", []),
    }


def extract_links(file_path: str, file_type: str) -> list[str]:
    """Hyperlink targets from a PDF's link annotations or a DOCX's relationships.

    A CV usually shows the word 'LinkedIn' as clickable text — the URL lives in the
    link metadata, not in the paragraph text, so plain text extraction loses it.
    """
    links: list[str] = []
    try:
        if file_type == "pdf":
            with fitz.open(file_path) as doc:
                for page in doc:
                    for link in page.get_links() or []:
                        uri = (link or {}).get("uri")
                        if uri:
                            links.append(uri)
        elif file_type == "docx":
            doc = Document(file_path)
            for rel in doc.part.rels.values():
                try:
                    if rel.reltype.endswith("/hyperlink") and getattr(rel, "is_external", False):
                        links.append(rel.target_ref)
                except Exception:
                    continue
    except Exception as exc:  # noqa: BLE001
        logger.warning("link extraction failed (%s)", repr(exc)[:150])

    seen: set[str] = set()
    out: list[str] = []
    for link in links:
        link = (link or "").strip()
        if link and link.lower() not in seen:
            seen.add(link.lower())
            out.append(link)
    return out


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        text = extract_text_from_pdf(file_path)
    elif file_type == "docx":
        text = extract_text_from_docx(file_path)
    elif file_type == "txt":
        text = extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    # Surface hyperlink targets in the text so downstream parsing (and the stored
    # parsed_text) can recover e.g. linkedin.com/in/<handle>.
    links = [l for l in extract_links(file_path, file_type)
             if any(k in l.lower() for k in ("linkedin.com", "github.com", "http"))]
    if links:
        text = text.rstrip() + "\n\n" + "\n".join(links)
    return text
