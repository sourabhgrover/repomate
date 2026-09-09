"""Thin wrapper around a MongoDB Atlas connection (free M0 cluster, 512MB cap).

MongoDB Atlas is used instead of Postgres/pgvector or Chroma for native hybrid
search (Vector Search + Atlas Search in one cluster) and to avoid vector-store
data loss on redeploy with ephemeral disks (CLAUDE.md).
"""

from pymongo import MongoClient
from pymongo.collection import Collection


class MongoDBClient:
    def __init__(self, uri: str, db_name: str) -> None:
        ...

    @property
    def chunks(self) -> Collection:
        ...

    @property
    def ingestion_jobs(self) -> Collection:
        ...

    @property
    def repos(self) -> Collection:
        ...

    def ping(self) -> bool:
        ...
