"""Async ingestion job routes: POST /index -> job_id, GET /status polls it.

Per CLAUDE.md: "Ingestion runs on the hosted backend as an async job
(POST /index -> job_id, poll GET /status)". start_index must never block on the
full ingestion pipeline.
"""

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

router = APIRouter()


class IndexRequest(BaseModel):
    owner: str
    name: str
    ref: str = "main"


class IndexResponse(BaseModel):
    job_id: str


class StatusResponse(BaseModel):
    job_id: str
    repo_id: str
    status: str
    files_processed: int
    chunks_created: int
    error_message: str | None = None


@router.post("/index", response_model=IndexResponse)
def start_index(
    request: IndexRequest, background_tasks: BackgroundTasks, pipeline_deps=Depends(...)
) -> IndexResponse:
    """Kicks off ingestion as an async background job and immediately returns job_id."""
    ...


@router.get("/status", response_model=StatusResponse)
def get_status(job_id: str, job_manager=Depends(...)) -> StatusResponse:
    """Polled by the client to check ingestion progress/completion."""
    ...
