"""Persists and queries Chunk documents in the `chunks` collection."""

from typing import TYPE_CHECKING

from backend.app.chunking.schema import Chunk

if TYPE_CHECKING:
    from backend.app.storage.mongo_client import MongoDBClient


class ChunkRepository:
    def __init__(self, mongo_client: "MongoDBClient") -> None:
        ...

    def upsert_chunks(self, chunks: list[Chunk], embeddings: list[list[float]]) -> int:
        """Upserts by (repo_id, content_hash) so unchanged chunks are skipped on re-index."""
        ...

    def delete_repo_chunks(self, repo_id: str) -> int:
        ...

    def vector_search(self, repo_id: str, query_embedding: list[float], top_k: int) -> list[dict]:
        """Runs an Atlas Vector Search $vectorSearch aggregation stage, filtered by repo_id."""
        ...

    def keyword_search(self, repo_id: str, query_text: str, top_k: int) -> list[dict]:
        """Runs an Atlas Search $search aggregation stage against the keyword index."""
        ...
