"""Strips VCS/dependency dirs, lockfiles, and binaries, and redacts secrets.

This MUST run before any embedding step, never after (CLAUDE.md: "Secret/binary
sanitization is mandatory before chunking... This runs BEFORE any embedding step,
never after"). IngestionPipeline enforces the ordering by calling this module
before chunker_registry / embedder.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class SkipReason(str, Enum):
    VCS_DIR = "vcs_dir"
    DEPENDENCY_DIR = "dependency_dir"
    LOCKFILE = "lockfile"
    BINARY = "binary"
    OVER_SIZE_LIMIT = "over_size_limit"


@dataclass(frozen=True)
class SanitizationResult:
    """Outcome of sanitizing a single file before it is allowed downstream."""

    original_path: Path
    included: bool
    skip_reason: SkipReason | None
    redacted_content: str | None  # None if excluded; secret-redacted text if included


DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset({".git", "node_modules", "__pycache__", ".venv"})
DEFAULT_LOCKFILE_NAMES: frozenset[str] = frozenset(
    {"package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"}
)


class Sanitizer:
    def __init__(
        self,
        excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
        lockfile_names: frozenset[str] = DEFAULT_LOCKFILE_NAMES,
    ) -> None:
        ...

    def is_excluded_path(self, path: Path) -> SkipReason | None:
        """Returns a SkipReason if the path matches an excluded dir/lockfile pattern, else None."""
        ...

    def is_binary(self, path: Path) -> bool:
        ...

    def redact_secrets(self, content: str, file_path: Path) -> str:
        """Redacts API keys, tokens, and .env-style contents from file content."""
        ...

    def sanitize_file(self, path: Path) -> SanitizationResult:
        ...

    def sanitize_tree(self, root_dir: Path) -> list[SanitizationResult]:
        ...
