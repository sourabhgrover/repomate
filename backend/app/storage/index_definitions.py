"""Conceptual Atlas index specs (field names + index type), not full Atlas JSON.

Two named indexes on `chunks` — one Vector Search, one Atlas Search — are the
literal implementation of "native hybrid search... in one cluster", the stated
reason Atlas was chosen over Chroma/pgvector.
"""

from dataclasses import dataclass
from enum import Enum


class IndexKind(str, Enum):
    VECTOR_SEARCH = "vector_search"  # Atlas Vector Search index
    ATLAS_SEARCH = "atlas_search"  # Atlas Search (Lucene) index
    STANDARD = "standard"  # regular MongoDB index


@dataclass(frozen=True)
class IndexSpec:
    collection: str
    name: str
    kind: IndexKind
    fields: list[str]
    notes: str


# chunks.embedding -> knnVector, dims = 384 (bge-small-en-v1.5 output dim), similarity = cosine
CHUNKS_VECTOR_INDEX = IndexSpec(
    collection="chunks",
    name="chunks_vector_index",
    kind=IndexKind.VECTOR_SEARCH,
    fields=["embedding"],
    notes="knnVector, numDimensions=384, similarity=cosine; filterable on repo_id, language",
)

# Atlas Search full-text index over chunk content + symbols for the keyword retrieval leg
CHUNKS_KEYWORD_INDEX = IndexSpec(
    collection="chunks",
    name="chunks_keyword_index",
    kind=IndexKind.ATLAS_SEARCH,
    fields=["content", "symbols", "file_path"],
    notes="standard Lucene analyzer on content; keyword analyzer on symbols/file_path",
)

# Supporting standard indexes to keep queries cheap on a 512MB free tier
CHUNKS_REPO_ID_INDEX = IndexSpec(
    collection="chunks",
    name="repo_id_idx",
    kind=IndexKind.STANDARD,
    fields=["repo_id"],
    notes="scopes retrieval + deletes to a single repo without full collection scans",
)

CHUNKS_CONTENT_HASH_INDEX = IndexSpec(
    collection="chunks",
    name="content_hash_idx",
    kind=IndexKind.STANDARD,
    fields=["repo_id", "content_hash"],
    notes="used to skip re-embedding unchanged chunks on re-index",
)

JOBS_JOB_ID_INDEX = IndexSpec(
    collection="ingestion_jobs",
    name="job_id_idx",
    kind=IndexKind.STANDARD,
    fields=["job_id"],
    notes="unique index; primary lookup key for GET /status polling",
)

ALL_INDEX_SPECS: list[IndexSpec] = [
    CHUNKS_VECTOR_INDEX,
    CHUNKS_KEYWORD_INDEX,
    CHUNKS_REPO_ID_INDEX,
    CHUNKS_CONTENT_HASH_INDEX,
    JOBS_JOB_ID_INDEX,
]
