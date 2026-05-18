"""Financial agent - run via cron on the LXC host.

Usage: docker compose exec backend python scripts/run_financial.py

Queries the FastAPI internal endpoint to trigger Stripe sync + MRR calculation.
"""
import httpx
import os

api_key = os.environ.get("INTERNAL_API_KEY", "")
base = os.environ.get("API_BASE", "http://backend:8000")

resp = httpx.post(
    f"{base}/api/v1/internal/agents/financial",
    headers={"Authorization": f"Bearer {api_key}"},
    timeout=30,
)
print(f"Financial agent: {resp.status_code}")
print(resp.json())
