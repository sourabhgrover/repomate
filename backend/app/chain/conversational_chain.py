"""Wraps LangChain's ConversationalRetrievalChain.

Single-pass retrieve-then-generate, NOT a multi-step agent (CLAUDE.md: "Single-
pass retrieval-and-generation... NOT an autonomous multi-tool agent"; do not
introduce LangGraph, ReAct loops, or multi-step tool-calling here). `ask()`
returns one ChatAnswer synchronously — no generator/streaming return type,
matching "No SSE streaming in MVP".
"""

from dataclasses import dataclass

from langchain.chains import ConversationalRetrievalChain
from langchain_core.retrievers import BaseRetriever


@dataclass(frozen=True)
class Citation:
    file_path: str
    line_start: int
    line_end: int
    chunk_type: str
    symbols: list[str]


@dataclass(frozen=True)
class ChatAnswer:
    """Synchronous /chat response payload: answer text plus citations."""

    answer: str
    citations: list[Citation]


class RepoConversationalChain:
    def __init__(self, retriever: BaseRetriever, llm) -> None:
        ...

    def _build_chain(self) -> ConversationalRetrievalChain:
        ...

    def ask(self, question: str, chat_history: list[tuple[str, str]]) -> ChatAnswer:
        """Runs the chain synchronously and maps source_documents into Citation
        objects. Returns a refusal-style answer when retrieval yields
        insufficient context."""
        ...
