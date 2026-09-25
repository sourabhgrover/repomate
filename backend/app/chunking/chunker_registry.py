"""Dispatches chunking by detected language.

Python-only for MVP (CLAUDE.md: "tree-sitter (AST-aware, Python only for MVP)").
Non-Python files raise UnsupportedLanguageError so callers explicitly skip/log
them rather than silently falling back to naive text splitting.
"""

from typing import TYPE_CHECKING
from backend.app.chunking.python_chunker import PythonChunker
from backend.app.chunking.schema import Chunk

if TYPE_CHECKING:
  from backend.app.ingestion.file_walker import WalkedFile


class UnsupportedLanguageError(Exception):
  """Raised for non-Python files in MVP scope."""

  pass


class ChunkerRegistry:

  def __init__(self, python_chunker: PythonChunker | None = None) -> None:
    self.python_chunker = python_chunker or PythonChunker()

  def supports(self, language: str | None) -> bool:
    """Returns True if the language has a dedicated AST chunker implemented."""
    return language is not None and language.lower() == "python"

  def chunk(
      self, repo_id: str, file_path: str, language: str | None, source_code: str
  ) -> list[Chunk]:
    """Raises UnsupportedLanguageError for non-Python languages."""
    if not self.supports(language):
      raise UnsupportedLanguageError(
          f"Language '{language}' is not supported in MVP scope (Python only"
          f" per CLAUDE.md)."
      )

    return self.python_chunker.chunk_file(
        repo_id=repo_id, file_path=file_path, source_code=source_code
    )

  def chunk_walked_file(
      self, walked_file: "WalkedFile", repo_id: str
  ) -> list[Chunk]:
    """Helper method to directly chunk a WalkedFile object from the ingestion pipeline."""
    return self.chunk(
        repo_id=repo_id,
        file_path=walked_file.relative_path,
        language=walked_file.language,
        source_code=walked_file.content,
    )