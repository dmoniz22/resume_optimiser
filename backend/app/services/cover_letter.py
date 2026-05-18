from app.config import settings
from app.services.llm_client import get_llm_client

COVER_LETTER_PROMPT = """Write a professional cover letter for the following job description.
Use the candidate's background to tailor the letter. Keep it concise (3-4 paragraphs).
Do NOT fabricate any experience or skills the candidate doesn't have.

Candidate Resume Summary: {resume_summary}

Job Description: {jd_text}

Output ONLY the cover letter body text, no subject line, no salutation, no signature."""


async def generate_cover_letter_text(resume_summary: str, jd_text: str) -> str:
    client = get_llm_client()
    response = client.chat.completions.create(
        model=settings.AI_MODEL_COVER_LETTER,
        messages=[
            {"role": "system", "content": "You are a professional cover letter writer. Never fabricate experience."},
            {"role": "user", "content": COVER_LETTER_PROMPT.format(resume_summary=resume_summary[:3000], jd_text=jd_text[:3000])},
        ],
        temperature=0.4,
        max_tokens=2048,
    )
    return response.choices[0].message.content.strip()
