"""Async ingestion job routes: POST /index -> job_id, GET /status polls it.

Per CLAUDE.md: "Ingestion runs on the hosted backend as an async job
(POST /index -> job_id, poll GET /status)". start_index must never block on the
full ingestion pipeline.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel

from backend.app.dependencies import get_ingestion_pipeline, get_job_manager
from backend.app.ingestion.job_manager import JobManager, JobNotFoundError
from backend.app.ingestion.pipeline import IngestionPipeline, IngestionRequest

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
    request: IndexRequest,
    background_tasks: BackgroundTasks,
    pipeline: IngestionPipeline = Depends(get_ingestion_pipeline),
    job_manager: JobManager = Depends(get_job_manager),
) -> IndexResponse:
  """Kicks off ingestion as an async background job and immediately returns job_id."""
  repo_id = f"{request.owner}/{request.name}"

  # 1. Create a job in QUEUED status
  job = job_manager.create_job(repo_id=repo_id)

  # 2. Add pipeline.run to background tasks (does NOT block the HTTP response)
  pipeline_request = IngestionRequest(
      owner=request.owner, name=request.name, ref=request.ref
  )
  background_tasks.add_task(pipeline.run, job.job_id, pipeline_request)

  # 3. Immediately return job_id to client
  return IndexResponse(job_id=job.job_id)


@router.get("/status", response_model=StatusResponse)
def get_status(
    job_id: str,
    job_manager: JobManager = Depends(get_job_manager),
) -> StatusResponse:
  """Polled by the client to check ingestion progress/completion."""
  try:
    job = job_manager.get_status(job_id)
    return StatusResponse(
        job_id=job.job_id,
        repo_id=job.repo_id,
        status=job.status.value,
        files_processed=job.files_processed,
        chunks_created=job.chunks_created,
        error_message=job.error_message,
    )
  except JobNotFoundError as e:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(e),
    ) from e