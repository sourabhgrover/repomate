"""Orchestrates the full ingestion flow as a background job.

fetch -> sanitize -> walk -> chunk -> embed -> persist. Sanitization always
precedes chunking/embedding (CLAUDE.md mandatory ordering) — enforced by the
call order inside run(), not left to caller discipline.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.chunking.chunker_registry import ChunkerRegistry
    from backend.app.embedding.embedder import Embedder
    from backend.app.ingestion.file_walker import FileWalker
    from backend.app.ingestion.github_client import GitHubClient
    from backend.app.ingestion.job_manager import JobManager
    from backend.app.ingestion.sanitizer import Sanitizer
    from backend.app.storage.chunk_repository import ChunkRepository


@dataclass(frozen=True)
class IngestionRequest:
    owner: str
    name: str
    ref: str = "main"


class IngestionPipeline:
    def __init__(
        self,
        github_client: "GitHubClient",
        sanitizer: "Sanitizer",
        file_walker: "FileWalker",
        chunker_registry: "ChunkerRegistry",
        embedder: "Embedder",
        chunk_repository: "ChunkRepository",
        job_manager: "JobManager",
    ) -> None:
        ...

    async def run(self, job_id: str, request: IngestionRequest) -> None:
        """Executed as a FastAPI background task. Updates job status throughout
        via job_manager so GET /status reflects live progress."""
        ...
