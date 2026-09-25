"""Orchestrates the full ingestion flow as a background job.

fetch -> sanitize -> walk -> chunk -> embed -> persist. Sanitization always
precedes chunking/embedding (CLAUDE.md mandatory ordering) — enforced by the
call order inside run(), not left to caller discipline.
"""

from dataclasses import dataclass
import logging
from pathlib import Path
import tempfile
from typing import TYPE_CHECKING
from backend.app.ingestion.github_client import RepoRef

if TYPE_CHECKING:
  from backend.app.chunking.chunker_registry import ChunkerRegistry
  from backend.app.embedding.embedder import Embedder
  from backend.app.ingestion.file_walker import FileWalker
  from backend.app.ingestion.github_client import GitHubClient
  from backend.app.ingestion.job_manager import JobManager
  from backend.app.ingestion.sanitizer import Sanitizer
  from backend.app.storage.chunk_repository import ChunkRepository

logger = logging.getLogger(__name__)


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
    self.github_client = github_client
    self.sanitizer = sanitizer
    self.file_walker = file_walker
    self.chunker_registry = chunker_registry
    self.embedder = embedder
    self.chunk_repository = chunk_repository
    self.job_manager = job_manager

  async def run(self, job_id: str, request: IngestionRequest) -> None:
    """Executed as a FastAPI background task. Updates job status throughout

    via job_manager so GET /status reflects live progress.
    """
    repo_ref = RepoRef(owner=request.owner, name=request.name, ref=request.ref)
    self.job_manager.mark_running(job_id)

    # Use a temporary directory so cloned files are cleaned up automatically after run()
    with tempfile.TemporaryDirectory(prefix="repomate_") as temp_dir:
      dest_dir = Path(temp_dir)
      try:
        # 1. FETCH (Shallow clone latest commit)
        logger.info(f"Cloning {repo_ref.repo_id} at ref {repo_ref.ref}...")
        cloned_path = self.github_client.clone_or_update(repo_ref, dest_dir)

        # 2. SANITIZE (Strip binaries/lockfiles, redact secrets BEFORE chunking)
        logger.info(f"Sanitizing repository tree at {cloned_path}...")
        sanitization_results = self.sanitizer.sanitize_tree(cloned_path)

        # 3. WALK & ENFORCE CAP (Check 100-150 demo cap, detect languages)
        logger.info("Walking sanitized files and detecting languages...")
        walked_files = self.file_walker.walk(cloned_path, sanitization_results)

        # 4. CHUNK (Tree-sitter AST syntax chunking - Week 2)
        all_chunks = []
        if self.chunker_registry is not None:
          logger.info(f"Chunking {len(walked_files)} walked files...")
          for file in walked_files:
            if hasattr(self.chunker_registry, "chunk_file"):
              chunks = self.chunker_registry.chunk_file(
                  file, repo_id=repo_ref.repo_id
              )
            elif hasattr(self.chunker_registry, "chunk"):
              chunks = self.chunker_registry.chunk(
                  file, repo_id=repo_ref.repo_id
              )
            else:
              chunks = []
            all_chunks.extend(chunks)

        # Update progress so GET /status reflects file and chunk counts
        self.job_manager.mark_progress(
            job_id,
            files_processed=len(walked_files),
            chunks_created=len(all_chunks),
        )

        # 5. EMBED (Sentence-transformers bge-small-en-v1.5 - Week 2)
        if self.embedder is not None and all_chunks:
          logger.info(f"Embedding {len(all_chunks)} chunks locally...")
          if hasattr(self.embedder, "embed_chunks"):
            all_chunks = self.embedder.embed_chunks(all_chunks)

        # 6. PERSIST (MongoDB Atlas bulk insert - Week 2)
        if self.chunk_repository is not None and all_chunks:
          logger.info("Persisting chunks to MongoDB Atlas...")
          if hasattr(self.chunk_repository, "save_chunks"):
            self.chunk_repository.save_chunks(all_chunks)
          elif hasattr(self.chunk_repository, "save"):
            self.chunk_repository.save(all_chunks)

        # 7. COMPLETED
        self.job_manager.mark_completed(job_id)
        logger.info(
            f"Successfully completed ingestion job {job_id} for"
            f" {repo_ref.repo_id}."
        )

      except Exception as exc:
        logger.error(f"Ingestion job {job_id} failed: {exc}", exc_info=True)
        self.job_manager.mark_failed(job_id, error_message=str(exc))
        raise exc