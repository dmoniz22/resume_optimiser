import httpx
from app.config import settings


async def send_email(to: str, subject: str, html: str) -> bool:
    if not settings.RESEND_API_KEY or settings.RESEND_API_KEY.startswith("re_"):
        print(f"Resend not configured, skipping email to {to}: {subject}")
        return False

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.EMAIL_FROM,
                "to": [to],
                "subject": subject,
                "html": html,
            },
        )
        return resp.status_code == 200
