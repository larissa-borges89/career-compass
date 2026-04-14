import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from src.logger import get_logger

logger = get_logger("api_server")

app = FastAPI(
    title="Career Compass API",
    description="AI-powered job application tracker",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"status": "ok", "version": "3.1.0"}
