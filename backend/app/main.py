from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.routers import auth, resumes, jds, optimizations, billing, content, internal_agents


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Resume Optimizer API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(resumes.router)
app.include_router(jds.router)
app.include_router(optimizations.router)
app.include_router(billing.router)
app.include_router(content.router)
app.include_router(internal_agents.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return RedirectResponse(url="http://localhost:3000")
