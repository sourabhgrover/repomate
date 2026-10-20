"""Wraps LangChain's ConversationalRetrievalChain.

Single-pass retrieve-then-generate, NOT a multi-step agent (CLAUDE.md: "Single-
pass retrieval-and-generation... NOT an autonomous multi-tool agent"; do not
introduce LangGraph, ReAct loops, or multi-step tool-calling here). `ask()`
returns one ChatAnswer synchronously — no generator/streaming return type,
matching "No SSE streaming in MVP".
"""

from dataclasses import dataclass
from typing import Any

from langchain_community.chains import ConversationalRetrievalChain
from langchain_core.retrievers import BaseRetriever

from backend.app.chain.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT


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

  def __init__(self, retriever: BaseRetriever, llm: Any) -> None:
    self.retriever = retriever
    self.llm = llm
    self.chain = self._build_chain()

  def _build_chain(self) -> ConversationalRetrievalChain:
    """Assembles a ConversationalRetrievalChain with custom question-condensing

    and QA prompts, returning source documents for citation extraction.
    """
    return ConversationalRetrievalChain.from_llm(
        llm=self.llm,
        retriever=self.retriever,
        condense_question_prompt=CONDENSE_QUESTION_PROMPT,
        combine_docs_chain_kwargs={"prompt": QA_PROMPT},
        return_source_documents=True,
        verbose=False,
    )

  def ask(
      self, question: str, chat_history: list[tuple[str, str]] | None = None
  ) -> ChatAnswer:
    """Runs the chain synchronously and maps source_documents into Citation

    objects. Returns a refusal-style answer when retrieval yields
    insufficient context.
    """
    if chat_history is None:
      chat_history = []

    # Execute chain execution synchronously
    result = self.chain.invoke(
        {"question": question, "chat_history": chat_history}
    )

    answer_text = result.get("answer", "")
    source_docs = result.get("source_documents", [])

    # Map retrieved Document metadata into typed Citation objects
    citations: list[Citation] = []
    seen_chunks = set()

    for doc in source_docs:
      meta = doc.metadata
      content_hash = meta.get("content_hash")

      # Deduplicate citations by content_hash or file_path + line_start
      chunk_key = content_hash or (
          meta.get("file_path"),
          meta.get("line_start"),
      )
      if chunk_key in seen_chunks:
        continue
      seen_chunks.add(chunk_key)

      citations.append(
          Citation(
              file_path=meta.get("file_path", ""),
              line_start=meta.get("line_start", 0),
              line_end=meta.get("line_end", 0),
              chunk_type=meta.get("chunk_type", ""),
              symbols=meta.get("symbols", []),
          )
      )

    return ChatAnswer(answer=answer_text, citations=citations)