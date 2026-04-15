import os
import time
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from api.routes import router
from api.database import engine, Base
from api import models  # noqa: F401 — ensures models are registered before create_all
from src.logger import get_logger

logger = get_logger("api_server")

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key() -> str:
    """Load API key from environment. Falls back to 'dev' in local mode."""
    key = os.getenv("API_KEY", "")
    if not key:
        logger.warning("API_KEY not set — running in open mode (local dev only)")
    return key

app = FastAPI(
    title="Career Compass API",
    description="AI-powered job application tracker",
    version="3.2.0"
)

# Create database tables on startup if they don't exist
Base.metadata.create_all(bind=engine)
logger.info("Database tables verified/created")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def authenticate(request: Request, call_next):
    """API Key authentication middleware. Skips /health for monitoring."""
    server_key = os.getenv("API_KEY", "")

    # Skip auth if no key configured (local dev) or for health check
    if not server_key or request.url.path == "/health":
        return await call_next(request)

    client_key = request.headers.get("X-API-Key", "")
    if client_key != server_key:
        logger.warning(f"Unauthorized request to {request.url.path}")
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key."})

    return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000)
    level = "INFO" if response.status_code < 400 else "WARNING" if response.status_code < 500 else "ERROR"
    getattr(logger, level.lower())(
        f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)"
    )
    return response


app.include_router(router, prefix="/api")


@app.get("/health")
def health():
    logger.info("Health check OK")
    return {"status": "ok", "version": "3.2.0"}
