"""LangChain retriever backed by Atlas Search (Lucene keyword leg)."""

from typing import TYPE_CHECKING

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

if TYPE_CHECKING:
    from backend.app.storage.chunk_repository import ChunkRepository


class AtlasKeywordRetriever(BaseRetriever):
    chunk_repository: "ChunkRepository"
    repo_id: str
    top_k: int = 8

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[Document]:
        ...
