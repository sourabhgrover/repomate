"""Dispatches chunking by detected language.

Python-only for MVP (CLAUDE.md: "tree-sitter (AST-aware, Python only for MVP)").
Non-Python files raise UnsupportedLanguageError so callers explicitly skip/log
them rather than silently falling back to naive text splitting.
"""

from backend.app.chunking.python_chunker import PythonChunker
from backend.app.chunking.schema import Chunk


class UnsupportedLanguageError(Exception):
    """Raised for non-Python files in MVP scope."""


class ChunkerRegistry:
    def __init__(self, python_chunker: PythonChunker | None = None) -> None:
        ...

    def supports(self, language: str | None) -> bool:
        ...

    def chunk(
        self, repo_id: str, file_path: str, language: str | None, source_code: str
    ) -> list[Chunk]:
        """Raises UnsupportedLanguageError for non-Python languages."""
        ...
