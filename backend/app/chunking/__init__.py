"""Chunking module: produces syntax-aware, non-fragmented AST code chunks."""

from backend.app.chunking.chunker_registry import (
    ChunkerRegistry,
    UnsupportedLanguageError,
)
from backend.app.chunking.python_chunker import PythonChunker, SyntacticUnit
from backend.app.chunking.schema import Chunk, compute_content_hash

__all__ = [
    "Chunk",
    "compute_content_hash",
    "SyntacticUnit",
    "PythonChunker",
    "ChunkerRegistry",
    "UnsupportedLanguageError",
]