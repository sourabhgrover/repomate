"""FastAPI dependency providers: mongo client, retrievers, chain, job manager.

Centralizing wiring here keeps routes thin and lets each singleton be built once
from Settings (config.py) rather than modules reaching into os.environ directly.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.chain.conversational_chain import RepoConversationalChain
    from backend.app.ingestion.job_manager import JobManager
    from backend.app.ingestion.pipeline import IngestionPipeline
    from backend.app.storage.mongo_client import MongoDBClient


def get_mongo_client() -> "MongoDBClient":
    ...


def get_job_manager() -> "JobManager":
    ...


def get_ingestion_pipeline() -> "IngestionPipeline":
    ...


def get_conversational_chain(repo_id: str) -> "RepoConversationalChain":
    ...
