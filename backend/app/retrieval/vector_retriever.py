"""LangChain retriever backed by Atlas Vector Search (semantic/dense leg)."""

from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

if TYPE_CHECKING:
  from backend.app.embedding.embedder import Embedder
  from backend.app.storage.chunk_repository import ChunkRepository


class AtlasVectorRetriever(BaseRetriever):
  """Semantic retriever using Atlas Vector Search.

  Converts the query into a dense 384-dim embedding (bge-small-en-v1.5)
  and retrieves the closest chunks by cosine similarity, filtered by repo_id.
  """

  chunk_repository: Any  # ChunkRepository
  embedder: Any  # Embedder
  repo_id: str
  top_k: int = 8

  def _get_relevant_documents(
      self, query: str, *, run_manager: CallbackManagerForRetrieverRun
  ) -> list[Document]:
    """Embeds query and runs $vectorSearch against the chunks collection."""

    # 1. Convert user query into a 384-dim dense vector
    query_embedding = self.embedder.embed_query(query)

    # 2. Run Atlas Vector Search filtered to this specific repository
    raw_results = self.chunk_repository.vector_search(
        repo_id=self.repo_id,
        query_embedding=query_embedding,
        top_k=self.top_k,
    )

    # 3. Convert raw MongoDB dicts into LangChain Document objects
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
              "retrieval_source": "vector",  # Tag for ensemble merging
          },
      )
      documents.append(doc)

    return documents