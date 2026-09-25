"""Self-hosted sentence-transformers embedding wrapper.

Uses BAAI/bge-small-en-v1.5 (CLAUDE.md: "sentence-transformers... self-hosted,
no paid embedding APIs"). Always called after Sanitizer has run — sanitized,
chunked text only, never raw file content.
"""

from typing import TYPE_CHECKING
from sentence_transformers import SentenceTransformer

if TYPE_CHECKING:
  from backend.app.chunking.schema import Chunk

DEFAULT_MODEL_NAME: str = "BAAI/bge-small-en-v1.5"


class Embedder:

  def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
    """Initializes the local SentenceTransformer model.

    Downloads weights once on the first run; subsequent runs load from cache.
    """
    self.model_name = model_name
    self.model = SentenceTransformer(model_name)

  def embed_texts(
      self, texts: list[str], batch_size: int = 32
  ) -> list[list[float]]:
    """Generates normalized 384-dimensional dense embeddings for a list of texts."""
    if not texts:
      return []

    # normalize_embeddings=True enables fast, accurate cosine similarity
    embeddings = self.model.encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=False,
        normalize_embeddings=True,
    )
    return embeddings.tolist()

  def embed_query(self, query: str) -> list[float]:
    """Generates a single normalized 384-dimensional dense embedding for a search query."""
    embedding = self.model.encode(query, normalize_embeddings=True)
    return embedding.tolist()

  def embed_chunks(self, chunks: list["Chunk"]) -> list["Chunk"]:
    """Helper method to embed a list of Chunk objects and attach vectors to chunk.embedding."""
    if not chunks:
      return []

    texts = [chunk.content for chunk in chunks]
    embeddings = self.embed_texts(texts)

    for chunk, emb in zip(chunks, embeddings):
      chunk.embedding = emb

    return chunks