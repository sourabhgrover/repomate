"""Owns the async ingestion job lifecycle.

Backs the exact async job model in CLAUDE.md: `POST /index` returns a job_id
immediately, and `GET /status` polls this manager for progress — there is no
synchronous long-running ingestion call.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
import uuid

if TYPE_CHECKING:
  from backend.app.storage.job_repository import JobRepository


class JobStatus(str, Enum):
  QUEUED = "queued"
  RUNNING = "running"
  COMPLETED = "completed"
  FAILED = "failed"


@dataclass
class IngestionJob:
  job_id: str
  repo_id: str
  status: JobStatus
  created_at: datetime
  updated_at: datetime
  error_message: str | None = None
  files_processed: int = 0
  chunks_created: int = 0


class JobNotFoundError(Exception):
  """Raised when attempting to access a non-existent job ID."""

  pass


class JobManager:

  def __init__(self, job_repository: "JobRepository") -> None:
    self.job_repository = job_repository

  def create_job(self, repo_id: str) -> IngestionJob:
    """Creates a new ingestion job in QUEUED status and persists it."""
    now = datetime.now(timezone.utc)
    job = IngestionJob(
        job_id=str(uuid.uuid4()),
        repo_id=repo_id,
        status=JobStatus.QUEUED,
        created_at=now,
        updated_at=now,
    )
    # Flexible persistence call (supports .save or .create on JobRepository)
    if hasattr(self.job_repository, "save"):
      self.job_repository.save(job)
    elif hasattr(self.job_repository, "create"):
      self.job_repository.create(job)
    return job

  def get_status(self, job_id: str) -> IngestionJob:
    """Fetches the current state of a job by ID."""
    job = None
    if hasattr(self.job_repository, "get"):
      job = self.job_repository.get(job_id)
    elif hasattr(self.job_repository, "find_by_id"):
      job = self.job_repository.find_by_id(job_id)

    if job is None:
      raise JobNotFoundError(f"Job with id '{job_id}' not found.")
    return job

  def _update_job(self, job_id: str, **kwargs) -> IngestionJob:
    """Helper to update job attributes, refresh updated_at, and save."""
    job = self.get_status(job_id)
    for key, value in kwargs.items():
      setattr(job, key, value)
    job.updated_at = datetime.now(timezone.utc)

    if hasattr(self.job_repository, "update"):
      self.job_repository.update(job)
    elif hasattr(self.job_repository, "save"):
      self.job_repository.save(job)
    return job

  def mark_running(self, job_id: str) -> None:
    """Transitions a job to RUNNING."""
    self._update_job(job_id, status=JobStatus.RUNNING)

  def mark_progress(
      self, job_id: str, files_processed: int, chunks_created: int
  ) -> None:
    """Updates counts of files processed and chunks created."""
    self._update_job(
        job_id, files_processed=files_processed, chunks_created=chunks_created
    )

  def mark_completed(self, job_id: str) -> None:
    """Marks a job as successfully COMPLETED."""
    self._update_job(job_id, status=JobStatus.COMPLETED)

  def mark_failed(self, job_id: str, error_message: str) -> None:
    """Marks a job as FAILED with an error message."""
    self._update_job(
        job_id, status=JobStatus.FAILED, error_message=error_message
    )