"""FastAPI app factory and route registration.

Single-pass retrieval-and-generation service (CLAUDE.md: NOT an autonomous
multi-tool agent) — only /index, /status, and /chat are exposed.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routes.chat_routes import router as chat_router
from backend.app.routes.index_routes import router as index_router


def create_app() -> FastAPI:
  """Creates and configures the FastAPI application."""
  app = FastAPI(
      title="RepoMate-Lite API",
      description=(
          "A RAG-based system that answers natural-language questions about"
          " GitHub repositories."
      ),
      version="1.0.0",
  )

  # Enable CORS for React frontend (Week 5)
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],  # Allows all origins for local dev
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Register routers under /api or root
  app.include_router(index_router, tags=["Ingestion"])
  app.include_router(chat_router, tags=["Chat"])

  @app.get("/health", tags=["Health"])
  def health_check():
    return {"status": "ok", "service": "RepoMate-Lite API"}

  return app


app = create_app()