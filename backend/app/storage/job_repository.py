"""Persists IngestionJob documents in the `ingestion_jobs` collection."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from backend.app.ingestion.job_manager import IngestionJob, JobStatus

if TYPE_CHECKING:
  from backend.app.storage.mongo_client import MongoDBClient


class JobRepository:

  def __init__(self, mongo_client: "MongoDBClient") -> None:
    self.collection = mongo_client.ingestion_jobs

  def insert(self, job: IngestionJob) -> None:
    """Inserts a new IngestionJob document into the ingestion_jobs collection."""
    self.collection.insert_one(self._to_doc(job))

  def update(self, job: IngestionJob) -> None:
    """Updates an existing IngestionJob document by job_id."""
    self.collection.update_one(
        {"job_id": job.job_id},
        {"$set": self._to_doc(job)},
    )

  def get(self, job_id: str) -> IngestionJob | None:
    """Fetches a single IngestionJob from the collection by job_id.

    Returns None if not found.
    """
    doc = self.collection.find_one({"job_id": job_id})
    if doc is None:
      return None
    return self._from_doc(doc)

  @staticmethod
  def _to_doc(job: IngestionJob) -> dict:
    """Converts an IngestionJob dataclass into a MongoDB-compatible dict."""
    return {
        "job_id": job.job_id,
        "repo_id": job.repo_id,
        "status": job.status.value,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "error_message": job.error_message,
        "files_processed": job.files_processed,
        "chunks_created": job.chunks_created,
    }

  @staticmethod
  def _from_doc(doc: dict) -> IngestionJob:
    """Converts a raw MongoDB document dict back into an IngestionJob dataclass."""
    return IngestionJob(
        job_id=doc["job_id"],
        repo_id=doc["repo_id"],
        status=JobStatus(doc["status"]),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
        error_message=doc.get("error_message"),
        files_processed=doc.get("files_processed", 0),
        chunks_created=doc.get("chunks_created", 0),
    )