"""Ingestion module: handles cloning, secret/binary sanitization, and async job lifecycle."""

from backend.app.ingestion.file_walker import FileWalker, RepoTooLargeError, WalkedFile
from backend.app.ingestion.github_client import GitHubClient, RepoRef
from backend.app.ingestion.job_manager import IngestionJob, JobManager, JobNotFoundError, JobStatus
from backend.app.ingestion.pipeline import IngestionPipeline, IngestionRequest
from backend.app.ingestion.sanitizer import (
    DEFAULT_EXCLUDED_DIRS,
    DEFAULT_LOCKFILE_NAMES,
    SanitizationResult,
    Sanitizer,
    SkipReason,
)

__all__ = [
    "GitHubClient",
    "RepoRef",
    "Sanitizer",
    "SanitizationResult",
    "SkipReason",
    "DEFAULT_EXCLUDED_DIRS",
    "DEFAULT_LOCKFILE_NAMES",
    "FileWalker",
    "WalkedFile",
    "RepoTooLargeError",
    "JobManager",
    "IngestionJob",
    "JobStatus",
    "JobNotFoundError",
    "IngestionPipeline",
    "IngestionRequest",
]