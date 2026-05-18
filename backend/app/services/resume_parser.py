import json
import re
import fitz
from docx import Document
from app.config import settings
from app.services.llm_client import get_llm_client

PARSE_PROMPT = """Extract structured data from this resume text. Output ONLY valid JSON, no other text.

RULES:
1. PRESERVE the EXACT original section titles (e.g., "Education", "Work Experience", "Employment", "Volunteer Experience", "Teaching", "Memberships", "Presentations", "Publications", "Licensure", "Certifications", "Awards", "Research", "Languages")
2. DO NOT invent new section titles or rename sections
3. Put all bullet points for each section under that section
4. For employment/volunteer roles, include the role title and organization in the bullet text if present (e.g., "Senior Physician, General Hospital — 2018-2023")
5. Group related content under the correct section — do not split one section's content across multiple headings

{{
  "full_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "sections": [
    {{
      "title": "EXACT original section heading",
      "bullets": [
        {{
          "text": "bullet content preserving original wording",
          "is_quantified": false
        }}
      ]
    }}
  ],
  "skills_detected": {{
    "hard": ["skill1", "skill2"],
    "soft": ["skill1", "skill2"]
  }},
  "years_of_experience": 5.0,
  "education": [{{"degree": "string", "school": "string", "year": 2020}}]
}}

Resume text:
{text}"""


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
    client = get_llm_client()
    response = client.chat.completions.create(
        model=settings.AI_MODEL_PARSE,
        messages=[
            {"role": "system", "content": "You are a resume parsing assistant. Output ONLY valid JSON. Preserve original section titles exactly."},
            {"role": "user", "content": PARSE_PROMPT.format(text=raw_text[:15000])},
        ],
        temperature=0.1,
        max_tokens=4096,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    result = json.loads(content)
    return clean_sections(result)


def clean_sections(parsed: dict) -> dict:
    """Merge misidentified sections and fix common AI parsing errors."""
    sections = parsed.get("sections", [])
    if not sections:
        return parsed

    cleaned = []
    known_titles = {
        "work experience", "experience", "employment", "professional experience",
        "education", "academic background",
        "skills", "technical skills", "core competencies", "clinical skills",
        "volunteer", "volunteer experience", "community service",
        "teaching", "teaching experience",
        "memberships", "professional memberships", "affiliations",
        "presentations", "publications", "research",
        "certifications", "licensure", "licenses", "board certification",
        "awards", "honors", "achievements",
        "languages", "interests",
        "summary", "profile", "objective",
    }

    for section in sections:
        title = section.get("title", "").strip()
        title_lower = title.lower()

        # Skip empty sections
        if not title:
            continue

        # Try to map unknown titles to known ones
        mapped = title
        for known in known_titles:
            if known in title_lower or title_lower in known:
                mapped = known.title() if len(known) > 5 else title
                break

        # If section has very few bullets and looks like a misidentified header, merge with previous
        bullets = section.get("bullets", [])
        if len(bullets) <= 1 and cleaned:
            # Check if this might be a role/position, not a section
            text = bullets[0].get("text", bullets[0]) if bullets else ""
            if any(marker in title_lower for marker in ("fellow", "resident", "physician", "doctor", "nurse", "manager", "director", "lead", "senior", "junior", "staff", "coordinator")):
                cleaned[-1]["bullets"].append({"text": f"{title} — {text}".rstrip(" —"), "is_quantified": False})
                continue

        section["title"] = mapped
        cleaned.append(section)

    parsed["sections"] = cleaned
    return parsed


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")
