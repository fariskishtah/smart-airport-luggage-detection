from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import router
from backend.services.job_manager import job_manager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
LOG = logging.getLogger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    LOG.info("Initializing Smart Airport Luggage Detection API Backend…")
    job_manager.start_worker()
    yield
    LOG.info("Shutting down API Backend…")


app = FastAPI(
    title="Smart Airport Luggage Detection API",
    description="Production AI inference backend for automated luggage detection, tracking, counting, and analytics.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Configuration
raw_origins = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [orig.strip() for orig in raw_origins.split(",") if orig.strip()]
# In production, allow all vercel.app domains via regex
origin_regex = os.getenv("CORS_ORIGIN_REGEX", r"https://.*\.vercel\.app")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=False)
