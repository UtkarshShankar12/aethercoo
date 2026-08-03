import sys
import os
import logging
import uvicorn
from fastapi import FastAPI, Request, Response
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

# Setup Dynamic CORS Middleware
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    origin = request.headers.get("origin")
    
    if request.method == "OPTIONS":
        response = Response()
        if origin:
            allowed = False
            if origin in settings.cors_origins_list:
                allowed = True
            elif origin.endswith(".amplifyapp.com") or origin.endswith(".vercel.app"):
                allowed = True
            elif "localhost" in origin or "127.0.0.1" in origin:
                allowed = True
                
            if allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
                response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        return response

    response = await call_next(request)
    
    if origin:
        allowed = False
        if origin in settings.cors_origins_list:
            allowed = True
        elif origin.endswith(".amplifyapp.com") or origin.endswith(".vercel.app"):
            allowed = True
        elif "localhost" in origin or "127.0.0.1" in origin:
            allowed = True
            
        if allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            
    return response

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
