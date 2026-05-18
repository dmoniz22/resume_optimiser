# Resume Optimizer

AI-powered resume optimization SaaS. Rewrites resume bullets to match job descriptions while guaranteeing zero fabrication of your experience. Self-hosted on Docker Compose.

## Architecture

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + TypeScript + TailwindCSS |
| Backend API | Python FastAPI |
| Database | PostgreSQL 16 with pgvector |
| Cache/Queue | Valkey 8 (FOSS Redis fork) |
| Background Jobs | ARQ (Python async job queue) |
| AI LLM | Ollama Cloud (OpenAI-compatible API) |
| Embeddings | nomic-embed-text (Docker-hosted Ollama) |
| PDF Generation | WeasyPrint (ATS-compliant output) |
| Auth | NextAuth.js + JWT |
| Payments | Stripe Checkout + Webhooks |
| Email | Resend API |

## Prerequisites

- **Docker** 28.4.0+
- **Docker Compose** 2.x+
- **Git**
- **Ollama Cloud account** (for AI LLM calls)
- **Stripe account** (for payments — optional for local dev)
- **Resend account** (for email magic links — optional for local dev)

## Quick Start (Local Development)

### 1. Clone the repository

```bash
git clone git@github.com:dmoniz22/resume_optimiser.git
cd resume_optimiser
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in at minimum:

| Variable | Required | Description |
|----------|----------|-------------|
| `OLLAMA_CLOUD_API_KEY` | **Yes** | Your Ollama Cloud API key |
| `JWT_SECRET` | **Yes** | Random string for JWT signing |
| `NEXTAUTH_SECRET` | **Yes** | Random string for NextAuth |
| `INTERNAL_API_KEY` | **Yes** | Random string for cron agents |
| `STRIPE_SECRET_KEY` | No | Stripe secret key (for payments) |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |
| `RESEND_API_KEY` | No | Resend API key (for magic links) |

Generate random secrets:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Start all services

```bash
docker compose up -d
```

Wait for all containers to be healthy (~30-60 seconds):

```bash
docker compose ps
```

Expected output: 6 services running (postgres, valkey, ollama, backend, worker, frontend)

### 4. Pull the embedding model

```bash
docker compose exec ollama ollama pull nomic-embed-text
```

### 5. Run database migrations

```bash
docker compose exec -e PYTHONPATH=/app backend alembic upgrade head
```

### 6. Seed subscription tiers

```bash
docker compose exec -e PYTHONPATH=/app backend python scripts/seed_tiers.py
```

### 7. Verify

```bash
# API health
curl http://localhost:8000/health
# → {"status":"ok"}

# Frontend
curl http://localhost:3000
# → HTML landing page

# Embeddings
docker compose exec backend python3 -c "
from app.services.llm_client import get_embed_client
c = get_embed_client()
r = c.embeddings.create(model='nomic-embed-text', input='test')
print(f'Embedding dims: {len(r.data[0].embedding)}')
"
# → Embedding dims: 768
```

## Port Map

| Service | Host Port | Container Port |
|---------|-----------|---------------|
| Frontend (Next.js) | 3000 | 3000 |
| Backend (FastAPI) | 8000 | 8000 |
| PostgreSQL | 5432 | 5432 |
| Valkey | 6379 | 6379 |
| Ollama (embeddings) | 11435 | 11434 |

> Port 11435 is used for Ollama to avoid conflicts with any local Ollama instance on 11434.

## API Endpoints

### Auth
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/auth/register` | No | Create account |
| POST | `/api/v1/auth/verify` | No | Login, returns JWT |
| GET | `/api/v1/auth/account` | JWT | User + tier + credits |

### Resumes
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/resumes` | JWT | List user's resumes |
| POST | `/api/v1/resumes` | JWT | Upload resume (multipart) |
| GET | `/api/v1/resumes/{id}` | JWT | Get resume details |
| PUT | `/api/v1/resumes/{id}` | JWT | Update resume data |
| DELETE | `/api/v1/resumes/{id}` | JWT | Archive resume |
| POST | `/api/v1/resumes/{id}/reparse` | JWT | Re-extract structured data |

### Job Descriptions
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/jds` | JWT | Create JD (auto-extracts keywords) |
| GET | `/api/v1/jds` | JWT | List JDs |
| GET | `/api/v1/jds/{id}` | JWT | Get JD details |
| DELETE | `/api/v1/jds/{id}` | JWT | Delete JD |

### Optimization
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/optimize` | JWT | Start optimization (async) |
| GET | `/api/v1/optimizations` | JWT | List optimizations |
| GET | `/api/v1/optimizations/{id}` | JWT | Get optimization results |
| POST | `/api/v1/optimizations/{id}/process` | JWT | Run optimization pipeline |
| POST | `/api/v1/optimizations/{id}/regenerate` | JWT | Regenerate bullets |
| GET | `/api/v1/optimizations/{id}/download` | JWT | Download optimized PDF |

### Billing
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/stripe/checkout` | JWT | Create Stripe checkout session |
| GET | `/api/v1/stripe/portal` | JWT | Stripe customer portal |
| POST | `/api/v1/webhooks/stripe` | Stripe sig | Stripe webhook handler |

### Content (Public)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/content/blog` | No | List published blog posts |
| GET | `/api/v1/content/blog/{slug}` | No | Get single post |
| POST | `/api/v1/content/tools/keyword-extractor` | No | Free JD keyword extractor |
| POST | `/api/v1/content/tools/resume-score` | No | Free resume scoring tool |

### Internal Agents
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/v1/internal/agents/content` | API Key | Ingest blog post from Paperclip Publisher |
| POST | `/api/v1/internal/agents/financial` | API Key | Run daily Stripe sync + MRR calc |
| POST | `/api/v1/internal/agents/research` | API Key | Ingest Reddit research data |
| GET | `/api/v1/internal/agents/research` | API Key | Get latest research trends |

## Frontend Pages

| Path | Auth | Description |
|------|------|-------------|
| `/` | No | Landing page |
| `/login` | No | Sign in (credentials + magic link) |
| `/signup` | No | Create account |
| `/pricing` | No | Pricing page with Stripe checkout |
| `/blog` | No | Blog listing |
| `/blog/{slug}` | No | Single blog post |
| `/dashboard` | NextAuth | Resume list |
| `/dashboard/upload` | NextAuth | Upload resume |
| `/dashboard/resumes/{id}` | NextAuth | Resume detail + optimize |
| `/dashboard/optimize/{id}` | NextAuth | Optimization results |
| `/admin` | API Key | MRR, research trends, system health |

## Testing the Full Flow

```bash
# 1. Create account
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass123","full_name":"Test User"}'

# 2. Login and save token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/verify \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"testpass123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# 3. Upload a resume
echo "John Doe\njohn@example.com\n\nExperience\nSenior Engineer, Acme Corp\n- Led team of 5 engineers\n- Reduced latency by 40%\n\nSkills\nPython, Docker, Kubernetes, React" > /tmp/resume.txt

curl -X POST http://localhost:8000/api/v1/resumes \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/tmp/resume.txt;type=text/plain" \
  -F "title=My Resume"

# 4. Create a job description
curl -X POST http://localhost:8000/api/v1/jds \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"raw_text":"Senior Backend Engineer. 5+ years Python, AWS, Kubernetes. Nice to have Docker, CI/CD."}'

# 5. Start optimization (replace IDs from previous responses)
curl -X POST http://localhost:8000/api/v1/optimize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"resume_id":"RESUME_ID","jd_id":"JD_ID"}'

# 6. Process the optimization
curl -X POST http://localhost:8000/api/v1/optimizations/OPTIMIZATION_ID/process \
  -H "Authorization: Bearer $TOKEN"

# 7. Download the optimized PDF
curl http://localhost:8000/api/v1/optimizations/OPTIMIZATION_ID/download \
  -H "Authorization: Bearer $TOKEN" \
  -o optimized_resume.pdf
```

## Pricing Tiers

| Tier | Price | Optimizations | Key Features |
|------|-------|--------------|--------------|
| Free | $0 | 3/month | Basic ATS score, bullet rewriting, PDF export |
| Pro | $19/mo | Unlimited | Cover letters, 10 resumes, DOCX export, multi-version |
| Career | $39/mo | Unlimited | Priority processing, unlimited storage, LinkedIn sync |

## AI Models

| Task | Model | Service |
|------|-------|---------|
| Resume parsing | `deepseek-v4-flash` | Ollama Cloud |
| JD extraction | `ministral-3:14b` | Ollama Cloud |
| Bullet rewriting | `gemma4:31b` | Ollama Cloud |
| Cover letters | `gemma4:31b` | Ollama Cloud |
| Embeddings | `nomic-embed-text` | Docker Ollama (local) |

## Development

### Hot reload
Files in `backend/` and `frontend/` are volume-mounted. Changes are picked up automatically by Uvicorn (`--reload`) and Next.js dev mode.

### Running migrations

```bash
# Apply pending migrations
docker compose exec -e PYTHONPATH=/app backend alembic upgrade head

# Create a new migration
docker compose exec -e PYTHONPATH=/app backend alembic revision --autogenerate -m "description"
```

### Rebuilding after Dockerfile changes

```bash
docker compose build backend worker frontend
docker compose up -d backend worker frontend
```

### Viewing logs

```bash
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f worker
```

## Deployment (to server LXC)

```bash
# On the server (192.168.68.12)
git clone git@github.com:dmoniz22/resume_optimiser.git /opt/resume-optimizer
cd /opt/resume-optimizer

# Create .env with production values
cp .env.example .env
# Edit .env with real Stripe keys, production URLs, etc.

# Build and start
docker compose build
docker compose up -d

# Run migrations
docker compose exec -e PYTHONPATH=/app backend alembic upgrade head

# Seed tiers
docker compose exec -e PYTHONPATH=/app backend python scripts/seed_tiers.py

# Verify
curl http://localhost:8000/health
```

### Traefik config (on reverse proxy at 192.168.68.4)

```yaml
# resume-optimizer.yml
http:
  routers:
    resume-optimizer:
      rule: "Host(`resume.monizhealth.com`)"
      entryPoints:
        - websecure
      service: resume-optimizer
      tls:
        certResolver: cloudflare
  services:
    resume-optimizer:
      loadBalancer:
        servers:
          - url: "http://192.168.68.12:3000"
```

Reload Traefik: `docker exec traefik kill -HUP 1`

### Cron jobs (on LXC host)

```bash
# Daily financial sync
0 6 * * * cd /opt/resume-optimizer && docker compose exec backend python scripts/run_financial.py

# Monthly report
0 5 1 * * cd /opt/resume-optimizer && docker compose exec backend python scripts/run_financial.py
```

## Project Structure

```
resume_optimiser/
├── docker-compose.yml              # Production services
├── docker-compose.override.yml     # Development overrides
├── .env.example                    # Environment template
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Pydantic settings
│   │   ├── database.py             # SQLAlchemy engine
│   │   ├── auth.py                 # JWT middleware
│   │   ├── models/                 # SQLAlchemy models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── routers/                # API route handlers
│   │   ├── services/               # Business logic
│   │   └── workers/                # ARQ background jobs
│   └── scripts/
│       ├── seed_tiers.py           # Seed subscription data
│       └── run_financial.py        # Cron-triggered financial agent
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.ts
│   ├── app/                        # Next.js App Router pages
│   ├── components/                 # React components
│   ├── lib/                        # API client, auth config
│   └── middleware.ts               # Route protection
└── data/
    └── resumes/                    # Uploaded resume files
```

## Key Design Decisions

1. **Anti-fabrication guard**: After AI rewrites bullets, a deterministic validation layer scans for fabricated skills/tools and auto-reverts them to original text.
2. **Zero AI inference costs**: All LLM calls use Ollama Cloud flat-rate subscription. Embeddings use local Docker-hosted Ollama.
3. **Stateless JWT auth**: NextAuth handles sessions on frontend; FastAPI validates JWT statelessly using shared secret.
4. **No cloud dependencies**: Everything runs in Docker Compose — no Vercel, no Supabase, no managed services.
5. **Single-column ATS PDFs**: Generated resumes follow ATS best practices (no images, tables, columns, or graphics).
