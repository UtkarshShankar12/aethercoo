import sys
import os
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Ensure the 'backend' directory is on PYTHONPATH for Vercel serverless imports
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

app = FastAPI(
    title="AetherCOO Backend API",
    description="Live sequential multi-agent AI execution engine.",
    version="1.0.0"
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(runs_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AetherCOO API"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
