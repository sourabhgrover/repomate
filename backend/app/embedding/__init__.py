"""Embedding module: local, zero-cost 384-dimensional vector generation."""

from backend.app.embedding.embedder import DEFAULT_MODEL_NAME, Embedder

__all__ = ["Embedder", "DEFAULT_MODEL_NAME"]