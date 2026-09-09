"""Owns the async ingestion job lifecycle.

Backs the exact async job model in CLAUDE.md: `POST /index` returns a job_id
immediately, and `GET /status` polls this manager for progress — there is no
synchronous long-running ingestion call.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

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


class JobManager:
    def __init__(self, job_repository: "JobRepository") -> None:
        ...

    def create_job(self, repo_id: str) -> IngestionJob:
        ...

    def mark_running(self, job_id: str) -> None:
        ...

    def mark_progress(self, job_id: str, files_processed: int, chunks_created: int) -> None:
        ...

    def mark_completed(self, job_id: str) -> None:
        ...

    def mark_failed(self, job_id: str, error_message: str) -> None:
        ...

    def get_status(self, job_id: str) -> IngestionJob:
        ...
