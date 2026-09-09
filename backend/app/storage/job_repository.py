"""Persists IngestionJob documents in the `ingestion_jobs` collection."""

from typing import TYPE_CHECKING

from backend.app.ingestion.job_manager import IngestionJob

if TYPE_CHECKING:
    from backend.app.storage.mongo_client import MongoDBClient


class JobRepository:
    def __init__(self, mongo_client: "MongoDBClient") -> None:
        ...

    def insert(self, job: IngestionJob) -> None:
        ...

    def update(self, job: IngestionJob) -> None:
        ...

    def get(self, job_id: str) -> IngestionJob | None:
        ...
