"""Walks a sanitized repo tree, detects language, and enforces the demo repo size cap."""

from dataclasses import dataclass
from pathlib import Path

from backend.app.ingestion.sanitizer import SanitizationResult


@dataclass(frozen=True)
class WalkedFile:
  """A sanitized file ready for language detection + chunking."""

  path: Path
  relative_path: str
  language: str | None  # None if unsupported/unknown
  content: str


class RepoTooLargeError(Exception):
  """Raised when a repo exceeds CLAUDE.md's documented ~100-150 file demo cap.

  Larger repos are a documented limitation, not a bug — this must be surfaced as
  an explicit error rather than silently truncating the file list.
  """


# Mapping of common file extensions to language identifiers
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".md": "markdown",
    ".markdown": "markdown",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sh": "bash",
    ".bash": "bash",
    ".sql": "sql",
    ".html": "html",
    ".css": "css",
}


class FileWalker:

  def __init__(self, max_files: int = 150) -> None:
    self.max_files = max_files

  def detect_language(self, path: Path) -> str | None:
    """Detects programming language from file extension.

    Returns language name or None if unknown/unsupported.
    """
    ext = path.suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, None)

  def walk(
      self, root_dir: Path, sanitizer_results: list[SanitizationResult]
  ) -> list[WalkedFile]:
    """Combines sanitizer output with language detection; enforces max_files cap."""
    root_dir = Path(root_dir).resolve()

    # 1. Filter only files accepted by Sanitizer
    included_results = [
        res
        for res in sanitizer_results
        if res.included and res.redacted_content is not None
    ]

    # 2. Enforce the hard cap documented in CLAUDE.md
    if len(included_results) > self.max_files:
      raise RepoTooLargeError(
          f"Repository contains {len(included_results)} eligible files, "
          f"which exceeds the documented demo cap of {self.max_files} files. "
          f"This is a documented limitation of the free-tier demo environment."
      )

    # 3. Build WalkedFile objects with normalized relative paths
    walked_files: list[WalkedFile] = []
    for res in included_results:
      try:
        # Use forward slashes for clean, platform-independent relative paths
        relative_path = res.original_path.relative_to(root_dir).as_posix()
      except ValueError:
        relative_path = res.original_path.name

      language = self.detect_language(res.original_path)

      walked_files.append(
          WalkedFile(
              path=res.original_path,
              relative_path=relative_path,
              language=language,
              content=res.redacted_content,
          )
      )

    return walked_files