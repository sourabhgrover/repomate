"""Thin wrapper around a MongoDB Atlas connection (free M0 cluster, 512MB cap).

MongoDB Atlas is used instead of Postgres/pgvector or Chroma for native hybrid
search (Vector Search + Atlas Search in one cluster) and to avoid vector-store
data loss on redeploy with ephemeral disks (CLAUDE.md).
"""

import logging
from pymongo import MongoClient
from pymongo.collection import Collection

logger = logging.getLogger(__name__)


class MongoDBClient:

  def __init__(self, uri: str, db_name: str) -> None:
    self.uri = uri
    self.db_name = db_name
    # serverSelectionTimeoutMS=5000 ensures quick timeout if Atlas is unreachable
    self._client: MongoClient = MongoClient(uri, serverSelectionTimeoutMS=5000)
    self._db = self._client[db_name]

  @property
  def chunks(self) -> Collection:
    """Collection storing AST code chunks with 384-dim embeddings."""
    return self._db["chunks"]

  @property
  def ingestion_jobs(self) -> Collection:
    """Collection tracking background ingestion job lifecycle state."""
    return self._db["ingestion_jobs"]

  @property
  def repos(self) -> Collection:
    """Collection storing repository metadata, branch info, and indexed stats."""
    return self._db["repos"]

  def ping(self) -> bool:
    """Checks if the MongoDB Atlas cluster is reachable."""
    try:
      self._client.admin.command("ping")
      return True
    except Exception as exc:
      logger.error(f"Failed to connect to MongoDB Atlas: {exc}")
      return False

  def close(self) -> None:
    """Closes all open sockets to MongoDB Atlas."""
    self._client.close()