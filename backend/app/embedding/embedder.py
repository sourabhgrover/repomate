"""Self-hosted sentence-transformers embedding wrapper.

Uses BAAI/bge-small-en-v1.5 (CLAUDE.md: "sentence-transformers... self-hosted,
no paid embedding APIs"). Always called after Sanitizer has run — sanitized,
chunked text only, never raw file content.
"""


class Embedder:
    def __init__(self, model_name: str) -> None:
        ...

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        ...

    def embed_query(self, query: str) -> list[float]:
        ...
