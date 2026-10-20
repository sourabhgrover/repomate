"""LangChain retriever backed by Atlas Search (Lucene keyword leg)."""

from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

if TYPE_CHECKING:
  from backend.app.storage.chunk_repository import ChunkRepository


class AtlasKeywordRetriever(BaseRetriever):
  """Keyword retriever using Atlas Search (Lucene BM25).

  Searches across chunk content, symbol names, and file paths for exact
  identifier matches — essential for code where exact names matter
  (e.g. 'create_access_token', 'MongoClient', '/api/v1/login').
  """

  chunk_repository: Any  # ChunkRepository
  repo_id: str
  top_k: int = 8

  def _get_relevant_documents(
      self, query: str, *, run_manager: CallbackManagerForRetrieverRun
  ) -> list[Document]:
    """Runs Atlas Search $search (Lucene BM25) against content, symbols, and file_path."""

    # 1. Run Lucene keyword search filtered to this specific repository
    raw_results = self.chunk_repository.keyword_search(
        repo_id=self.repo_id,
        query_text=query,
        top_k=self.top_k,
    )

    # 2. Convert raw MongoDB dicts into LangChain Document objects
    documents = []
    for result in raw_results:
      doc = Document(
          page_content=result.get("content", ""),
          metadata={
              "repo_id": result.get("repo_id", ""),
              "file_path": result.get("file_path", ""),
              "language": result.get("language", ""),
              "chunk_type": result.get("chunk_type", ""),
              "symbols": result.get("symbols", []),
              "line_start": result.get("line_start", 0),
              "line_end": result.get("line_end", 0),
              "content_hash": result.get("content_hash", ""),
              "search_score": result.get("search_score", 0.0),
              "retrieval_source": "keyword",  # Tag for ensemble merging
          },
      )
      documents.append(doc)

    return documents