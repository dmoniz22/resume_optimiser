import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.services.llm_client import get_embed_client
from app.config import settings


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a)
    vb = np.array(b)
    return float(np.dot(va, vb) / (np.linalg.norm(va) * np.linalg.norm(vb)))


async def generate_embedding(text: str) -> list[float]:
    client = get_embed_client()
    response = client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=text[:8000],
    )
    return response.data[0].embedding


async def embed_resume(resume_id: str, db: AsyncSession) -> list[float]:
    result = await db.execute(select(Resume).where(Resume.id == resume_id))
    resume = result.scalar_one_or_none()
    if not resume:
        raise ValueError("Resume not found")

    text = resume.parsed_text or ""
    embedding = await generate_embedding(text)
    resume.embedding = embedding
    await db.commit()
    return embedding


async def embed_jd(jd_id: str, db: AsyncSession) -> list[float]:
    result = await db.execute(select(JobDescription).where(JobDescription.id == jd_id))
    jd = result.scalar_one_or_none()
    if not jd:
        raise ValueError("JD not found")

    text = jd.raw_text or ""
    embedding = await generate_embedding(text)
    jd.embedding = embedding
    await db.commit()
    return embedding
