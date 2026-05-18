import json
import fitz
from docx import Document
from app.config import settings
from app.services.llm_client import get_llm_client

PARSE_PROMPT = """Extract structured data from this resume text. Output ONLY valid JSON, no other text.

{
  "full_name": "string or null",
  "email": "string or null",
  "phone": "string or null",
  "location": "string or null",
  "sections": [
    {
      "title": "Work Experience | Education | Skills | Projects | Certifications | etc.",
      "bullets": [
        {
          "text": "bullet text",
          "is_quantified": false
        }
      ]
    }
  ],
  "skills_detected": {
    "hard": ["Python", "React", ...],
    "soft": ["Leadership", "Communication", ...]
  },
  "years_of_experience": 5.0,
  "education": [{"degree": "string", "school": "string", "year": 2020}]
}

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
            {"role": "system", "content": "You are a resume parsing assistant. Output ONLY valid JSON."},
            {"role": "user", "content": PARSE_PROMPT.format(text=raw_text[:12000])},
        ],
        temperature=0.1,
        max_tokens=4096,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    return json.loads(content)


def extract_text(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        return extract_text_from_pdf(file_path)
    elif file_type == "docx":
        return extract_text_from_docx(file_path)
    elif file_type == "txt":
        return extract_text_from_txt(file_path)
    raise ValueError(f"Unsupported file type: {file_type}")
