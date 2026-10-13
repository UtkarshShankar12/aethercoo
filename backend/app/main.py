import sys
import os
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

# Ensure the 'backend' directory is on PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load local environment variables from .env if present
load_dotenv()

from app.config import settings
from app.routes.runs import router as runs_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds HTTP security headers to every response (Helmet.js equivalent)."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # HSTS: enforce HTTPS for 1 year (only meaningful behind TLS)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app = FastAPI(
    title="AetherCOO Backend API",
    description="Live sequential multi-agent AI execution engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

# CORS: restrict to configured origins only (set via CORS_ORIGINS env var)
cors_origins = settings.cors_origins_list
logger.info(f"CORS allowed origins: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Accept", "Authorization"],
)

# Security headers on every response
app.add_middleware(SecurityHeadersMiddleware)

# Include API routers
app.include_router(runs_router)


@app.get("/", tags=["meta"])
async def root():
    """Root route — confirms the API is live. Useful for quick Render health checks."""
    return {
        "status": "online",
        "service": "AetherCOO API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["meta"])
async def health_check():
    """Liveness probe for Render / container orchestrator health checks."""
    return {"status": "healthy", "service": "AetherCOO API", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", 8000)),
        reload=True
    )
