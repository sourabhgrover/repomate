"""Persists and queries Chunk documents in the `chunks` collection."""

import logging
from typing import TYPE_CHECKING

from pymongo import UpdateOne

from backend.app.chunking.schema import Chunk

if TYPE_CHECKING:
  from backend.app.storage.mongo_client import MongoDBClient

logger = logging.getLogger(__name__)

# Must match exactly the index names configured in MongoDB Atlas
VECTOR_INDEX_NAME = "vector_index"
KEYWORD_INDEX_NAME = "keyword_index"


class ChunkRepository:

  def __init__(self, mongo_client: "MongoDBClient") -> None:
    self.collection = mongo_client.chunks

  def upsert_chunks(
      self, chunks: list[Chunk], embeddings: list[list[float]]
  ) -> int:
    """Upserts by (repo_id, content_hash) so unchanged chunks are skipped on re-index.

    Returns the number of chunks actually written/modified.
    """
    if not chunks or not embeddings:
      return 0

    if len(chunks) != len(embeddings):
      raise ValueError(
          f"Chunks ({len(chunks)}) and embeddings ({len(embeddings)}) length mismatch."
      )

    operations = []
    for chunk, embedding in zip(chunks, embeddings):
      doc = {
          **chunk.model_dump(exclude={"embedding"}),
          "embedding": embedding,
      }
      operations.append(
          UpdateOne(
              # Upsert key: unique per (repo_id, content_hash)
              # If content is unchanged, this is a no-op (skipping re-embedding)
              filter={"repo_id": chunk.repo_id, "content_hash": chunk.content_hash},
              update={"$set": doc},
              upsert=True,
          )
      )

    result = self.collection.bulk_write(operations, ordered=False)
    written = result.upserted_count + result.modified_count
    logger.info(
        f"Upserted {result.upserted_count} new, modified {result.modified_count} existing chunks."
    )
    return written

  def delete_repo_chunks(self, repo_id: str) -> int:
    """Deletes all chunks for a given repo_id (e.g. before a full re-index).

    Returns the number of deleted documents.
    """
    result = self.collection.delete_many({"repo_id": repo_id})
    logger.info(
        f"Deleted {result.deleted_count} chunks for repo_id='{repo_id}'."
    )
    return result.deleted_count

  def vector_search(
      self, repo_id: str, query_embedding: list[float], top_k: int = 5
  ) -> list[dict]:
    """Runs an Atlas Vector Search $vectorSearch aggregation stage, filtered by repo_id."""
    pipeline = [
        {
            "$vectorSearch": {
                "index": VECTOR_INDEX_NAME,
                "path": "embedding",
                "queryVector": query_embedding,
                "numCandidates": top_k * 10,  # Search 10x candidates for accuracy
                "limit": top_k,
                "filter": {"repo_id": {"$eq": repo_id}},
            }
        },
        # Attach similarity score to each result
        {
            "$addFields": {
                "search_score": {"$meta": "vectorSearchScore"}
            }
        },
        # Return all chunk fields except the raw embedding vector
        {
            "$project": {
                "embedding": 0,
                "_id": 0,
            }
        },
    ]
    results = list(self.collection.aggregate(pipeline))
    logger.info(
        f"Vector search returned {len(results)} results for repo_id='{repo_id}'."
    )
    return results

  def keyword_search(
      self, repo_id: str, query_text: str, top_k: int = 5
  ) -> list[dict]:
    """Runs an Atlas Search $search aggregation stage against the keyword index."""
    pipeline = [
        {
            "$search": {
                "index": KEYWORD_INDEX_NAME,
                "text": {
                    "query": query_text,
                    # Searches across code content, symbol names, and file paths
                    "path": ["content", "symbols", "file_path"],
                },
            }
        },
        # Filter to only this repository's chunks after the search
        {"$match": {"repo_id": repo_id}},
        {"$limit": top_k},
        # Attach BM25 relevance score
        {
            "$addFields": {
                "search_score": {"$meta": "searchScore"}
            }
        },
        {
            "$project": {
                "embedding": 0,
                "_id": 0,
            }
        },
    ]
    results = list(self.collection.aggregate(pipeline))
    logger.info(
        f"Keyword search returned {len(results)} results for repo_id='{repo_id}'."
    )
    return results