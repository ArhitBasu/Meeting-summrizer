from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.meeting import router as meeting_router
from app.database.session import engine
from app.database.base import Base

# Setup logging immediately
setup_logging()
logger.info("Starting AI Meeting Summarizer Backend")

if not settings.OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY is not set — AI pipeline will fail at runtime.")

# Auto-create tables on startup (acceptable for MVP; use Alembic for schema migrations)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-powered meeting transcription and summarization API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(meeting_router, prefix="/api/meetings", tags=["meetings"])

@app.get("/health", tags=["health"])
def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}
