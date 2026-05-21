from app.services.embedding import embed_resume, embed_jd, cosine_similarity, generate_embedding
from sqlalchemy.ext.asyncio import AsyncSession


async def calculate_pre_score(resume_id: str, jd_id: str, db: AsyncSession) -> float:
    resume_embedding = await embed_resume(resume_id, db)
    jd_embedding = await embed_jd(jd_id, db)
    similarity = cosine_similarity(resume_embedding, jd_embedding)
    return round(float(similarity * 100), 1)


async def calculate_post_score(resume_id: str, jd_id: str, db: AsyncSession) -> float:
    resume_embedding = await embed_resume(resume_id, db)
    jd_embedding = await embed_jd(jd_id, db)
    similarity = cosine_similarity(resume_embedding, jd_embedding)
    return round(float(similarity * 100), 1)


async def calculate_optimized_score(optimized_text: str, jd_id: str, db: AsyncSession) -> float:
    resume_embedding = await generate_embedding(optimized_text)
    jd_embedding = await embed_jd(jd_id, db)
    similarity = cosine_similarity(resume_embedding, jd_embedding)
    return round(float(similarity * 100), 1)


def _safe_str_from_kw(kw) -> str:
    if isinstance(kw, dict):
        return kw.get("name", kw.get("skill", kw.get("text", str(kw))))
    return str(kw)


def keyword_coverage_score(resume_text: str, jd_keywords: dict) -> float:
    if not jd_keywords:
        return 0.0

    resume_lower = resume_text.lower()
    all_keywords = set()
    found = set()

    for key in ("hard_skills", "soft_skills", "must_have", "ats_keywords"):
        for kw in jd_keywords.get(key, []):
            kw_str = _safe_str_from_kw(kw)
            all_keywords.add(kw_str.lower())
            if kw_str.lower() in resume_lower:
                found.add(kw_str.lower())

    if not all_keywords:
        return 0.0
    return round(len(found) / len(all_keywords) * 100, 1)
