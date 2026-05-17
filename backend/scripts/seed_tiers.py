"""Seed subscription tiers into the database."""
import asyncio
import uuid
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.subscription import SubscriptionTier


async def seed_tiers():
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(SubscriptionTier))
        if existing.scalars().first():
            print("Tiers already seeded, skipping.")
            return

        tiers = [
            SubscriptionTier(
                id=uuid.uuid4(),
                name="free",
                stripe_price_id=None,
                monthly_price_cents=0,
                credits_per_month=3,
                features={
                    "optimizations_per_month": 3,
                    "resume_storage": 1,
                    "jd_keyword_extraction": True,
                    "bullet_rewriting": True,
                    "ats_score": "basic",
                    "cover_letter": False,
                    "multi_version": False,
                    "priority_processing": False,
                    "export_formats": ["pdf"],
                    "email_support": False,
                },
                is_active=True,
            ),
            SubscriptionTier(
                id=uuid.uuid4(),
                name="pro",
                stripe_price_id=None,
                monthly_price_cents=1900,
                credits_per_month=None,
                features={
                    "optimizations_per_month": "unlimited",
                    "resume_storage": 10,
                    "jd_keyword_extraction": True,
                    "bullet_rewriting": True,
                    "ats_score": "detailed",
                    "cover_letter": True,
                    "multi_version": True,
                    "priority_processing": False,
                    "export_formats": ["pdf", "docx"],
                    "email_support": "standard",
                },
                is_active=True,
            ),
            SubscriptionTier(
                id=uuid.uuid4(),
                name="career",
                stripe_price_id=None,
                monthly_price_cents=3900,
                credits_per_month=None,
                features={
                    "optimizations_per_month": "unlimited",
                    "resume_storage": "unlimited",
                    "jd_keyword_extraction": True,
                    "bullet_rewriting": True,
                    "ats_score": "detailed_tips",
                    "cover_letter": True,
                    "multi_version": True,
                    "priority_processing": True,
                    "export_formats": ["pdf", "docx", "txt"],
                    "email_support": "priority",
                },
                is_active=True,
            ),
        ]

        for tier in tiers:
            session.add(tier)
        await session.commit()
        print(f"Seeded {len(tiers)} subscription tiers.")


if __name__ == "__main__":
    asyncio.run(seed_tiers())
