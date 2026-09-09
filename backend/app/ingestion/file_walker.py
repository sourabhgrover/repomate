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


class FileWalker:
    def __init__(self, max_files: int) -> None:
        ...

    def detect_language(self, path: Path) -> str | None:
        ...

    def walk(self, root_dir: Path, sanitizer_results: list[SanitizationResult]) -> list[WalkedFile]:
        """Combines sanitizer output with language detection; enforces max_files cap."""
        ...
