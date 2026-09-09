"""Canonical chunk schema.

Field names (repo_id, file_path, language, chunk_type, symbols, content_hash,
line_start, line_end) are fixed by CLAUDE.md's "Chunk schema fields" convention
and must not change without an explicit decision.
"""

from pydantic import BaseModel


class Chunk(BaseModel):
    repo_id: str
    file_path: str
    language: str
    chunk_type: str  # e.g. "function", "class", "module_level"
    symbols: list[str]  # names of functions/classes/identifiers in this chunk
    content_hash: str  # stable hash of chunk content; used for de-dup/re-index skip
    line_start: int
    line_end: int
    content: str  # chunk text itself; not one of the required metadata fields
