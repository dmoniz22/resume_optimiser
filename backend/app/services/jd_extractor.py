import json
from app.config import settings
from app.services.llm_client import get_llm_client

EXTRACT_PROMPT = """Extract keywords and requirements from this job description. Output ONLY valid JSON.

{{
  "job_title": "string",
  "company_name": "string or null",
  "hard_skills": ["skill1", "skill2"],
  "soft_skills": ["skill1", "skill2"],
  "must_have": ["requirement1", "requirement2"],
  "nice_to_have": ["requirement1"],
  "keywords_priority": ["keyword1", "keyword2"],
  "ats_keywords": ["keyword1", "keyword2"]
}}

keywords_priority: Most important keywords ordered by importance for ATS matching.
ats_keywords: All keywords that ATS systems commonly scan for.

Job Description:
{text}"""


async def extract_jd_keywords(raw_text: str) -> dict:
    client = get_llm_client()
    response = client.chat.completions.create(
        model=settings.AI_MODEL_EXTRACT,
        messages=[
            {"role": "system", "content": "You are a job description analysis assistant. Output ONLY valid JSON."},
            {"role": "user", "content": EXTRACT_PROMPT.format(text=raw_text[:10000])},
        ],
        temperature=0.1,
        max_tokens=2048,
    )
    content = response.choices[0].message.content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
    return json.loads(content)
