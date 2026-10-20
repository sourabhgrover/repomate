"""FastAPI dependency providers: mongo client, retrievers, chain, job manager.

Centralizing wiring here keeps routes thin and lets each singleton be built once
from Settings (config.py) rather than modules reaching into os.environ directly.
"""

from functools import lru_cache
import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

from backend.app.chain.conversational_chain import RepoConversationalChain
from backend.app.chunking.chunker_registry import ChunkerRegistry
from backend.app.chunking.python_chunker import PythonChunker
from backend.app.embedding.embedder import Embedder
from backend.app.ingestion.file_walker import FileWalker
from backend.app.ingestion.github_client import GitHubClient
from backend.app.ingestion.job_manager import JobManager
from backend.app.ingestion.pipeline import IngestionPipeline
from backend.app.ingestion.sanitizer import Sanitizer
from backend.app.retrieval.ensemble import build_ensemble_retriever
from backend.app.retrieval.keyword_retriever import AtlasKeywordRetriever
from backend.app.retrieval.vector_retriever import AtlasVectorRetriever
from backend.app.storage.chunk_repository import ChunkRepository
from backend.app.storage.job_repository import JobRepository
from backend.app.storage.mongo_client import MongoDBClient

# Fallback LLM loader (supports LLM_API_KEY / GROQ_API_KEY per .env)
try:
  from langchain_groq import ChatGroq

  def _create_llm():
    api_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or ""
    model_name = os.getenv("LLM_MODEL_NAME", "llama-3.3-70b-versatile")
    return ChatGroq(
        model_name=model_name,
        temperature=0.1,
        groq_api_key=api_key or None,
    )

except ImportError:

  def _create_llm():
    from langchain_core.language_models.fake import FakeListLLM

    return FakeListLLM(responses=["[test/app.py:L1-L10] Mocked response."])


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoDBClient:
  uri = os.getenv(
      "MONGODB_URI", "mongodb://localhost:27017/?retryWrites=true&w=majority"
  )
  db_name = os.getenv("MONGODB_DB_NAME", "repomate")
  return MongoDBClient(uri=uri, db_name=db_name)


@lru_cache(maxsize=1)
def get_job_repository() -> JobRepository:
  return JobRepository(mongo_client=get_mongo_client())


@lru_cache(maxsize=1)
def get_chunk_repository() -> ChunkRepository:
  return ChunkRepository(mongo_client=get_mongo_client())


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
  return Embedder()


@lru_cache(maxsize=1)
def get_job_manager() -> JobManager:
  return JobManager(job_repository=get_job_repository())


@lru_cache(maxsize=1)
def get_ingestion_pipeline() -> IngestionPipeline:
  github_token = os.getenv("GITHUB_TOKEN")
  max_files = int(os.getenv("MAX_REPO_FILES", "150"))
  return IngestionPipeline(
      github_client=GitHubClient(github_token=github_token),
      sanitizer=Sanitizer(),
      file_walker=FileWalker(max_files=max_files),
      chunker_registry=ChunkerRegistry(python_chunker=PythonChunker()),
      embedder=get_embedder(),
      chunk_repository=get_chunk_repository(),
      job_manager=get_job_manager(),
  )


def get_conversational_chain(repo_id: str) -> RepoConversationalChain:
  """Builds a repository-scoped hybrid retriever and returns the conversational chain."""
  chunk_repo = get_chunk_repository()
  embedder = get_embedder()

  vector_retriever = AtlasVectorRetriever(
      chunk_repository=chunk_repo,
      embedder=embedder,
      repo_id=repo_id,
      top_k=5,
  )

  keyword_retriever = AtlasKeywordRetriever(
      chunk_repository=chunk_repo,
      repo_id=repo_id,
      top_k=5,
  )

  ensemble_retriever = build_ensemble_retriever(
      vector_retriever=vector_retriever,
      keyword_retriever=keyword_retriever,
      weights=(0.5, 0.5),
  )

  llm = _create_llm()
  return RepoConversationalChain(retriever=ensemble_retriever, llm=llm)