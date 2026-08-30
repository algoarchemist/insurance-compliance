"""Sugamai — Unified Health Insurance Management Platform
FastAPI application entry point.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import settings
from app.core.database import init_db

# Import routers
from app.routers.auth import router as auth_router
from app.routers.identity import router as identity_router
from app.routers.policies import router as policies_router
from app.routers.hospitals import router as hospitals_router
from app.routers.claims import router as claims_router
from app.routers.caregiver import router as caregiver_router
from app.routers.ai import router as ai_router
from app.routers.admin import router as admin_router, bank_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown lifecycle."""
    # Startup
    if settings.APP_ENV == "development":
        await init_db()
    yield
    # Shutdown


# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    description="Unified Health Insurance Management Platform for Indian Citizens",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8081",
        settings.NEXT_PUBLIC_API_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api/v1
API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(identity_router, prefix=API_PREFIX)
app.include_router(policies_router, prefix=API_PREFIX)
app.include_router(hospitals_router, prefix=API_PREFIX)
app.include_router(claims_router, prefix=API_PREFIX)
app.include_router(caregiver_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(bank_router, prefix=API_PREFIX)


@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
