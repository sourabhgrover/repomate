"""LangChain retriever backed by Atlas Vector Search (semantic/dense leg)."""

from typing import TYPE_CHECKING

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

if TYPE_CHECKING:
    from backend.app.embedding.embedder import Embedder
    from backend.app.storage.chunk_repository import ChunkRepository


class AtlasVectorRetriever(BaseRetriever):
    chunk_repository: "ChunkRepository"
    embedder: "Embedder"
    repo_id: str
    top_k: int = 8

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        ...
