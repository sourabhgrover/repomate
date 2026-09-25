"""Strips VCS/dependency dirs, lockfiles, and binaries, and redacts secrets.

This MUST run before any embedding step, never after (CLAUDE.md: "Secret/binary
sanitization is mandatory before chunking... This runs BEFORE any embedding step,
never after"). IngestionPipeline enforces the ordering by calling this module
before chunker_registry / embedder.
"""

from dataclasses import dataclass
from enum import Enum
import os
from pathlib import Path
import re


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
  redacted_content: (
      str | None
  )  # None if excluded; secret-redacted text if included


DEFAULT_EXCLUDED_DIRS: frozenset[str] = frozenset(
    {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build"}
)
DEFAULT_LOCKFILE_NAMES: frozenset[str] = frozenset(
    {"package-lock.json", "yarn.lock", "poetry.lock", "Pipfile.lock"}
)

# Known binary extensions
BINARY_EXTENSIONS: frozenset[str] = frozenset({
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".zip",
    ".tar",
    ".gz",
    ".pyc",
    ".pyo",
    ".pyd",
    ".bin",
    ".woff",
    ".woff2",
    ".ttf",
})

# High-confidence secret detection patterns
SECRET_PATTERNS: list[re.Pattern] = [
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),  # GitHub Personal Access Token
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),  # OpenAI/Generic Secret Key
    re.compile(
        r"Bearer\s+[A-Za-z0-9_\-\.]{25,}"
    ),  # Bearer / JWT Tokens (auth headers)
]

# Pattern for assignment of sensitive variables (e.g. API_KEY="xyz", PASSWORD="xyz")
ENV_ASSIGNMENT_PATTERN: re.Pattern = re.compile(
    r'(?i)^(\s*(?:SECRET|PASSWORD|PASSWD|TOKEN|API_KEY|PRIVATE_KEY|DATABASE_URL|AUTH_KEY)[^\s=:]*[\s=:]+)(["\']?[^\s"\']+["\']?)',
    re.MULTILINE,
)


class Sanitizer:

  def __init__(
      self,
      excluded_dirs: frozenset[str] = DEFAULT_EXCLUDED_DIRS,
      lockfile_names: frozenset[str] = DEFAULT_LOCKFILE_NAMES,
      max_file_size_bytes: int = 1_000_000,  # 1 MB per file limit
  ) -> None:
    self.excluded_dirs = excluded_dirs
    self.lockfile_names = lockfile_names
    self.max_file_size_bytes = max_file_size_bytes

  def is_excluded_path(self, path: Path) -> SkipReason | None:
    """Returns a SkipReason if the path matches an excluded dir/lockfile pattern, else None."""
    # Check directory components
    for part in path.parts:
      if part == ".git":
        return SkipReason.VCS_DIR
      if part in self.excluded_dirs:
        return SkipReason.DEPENDENCY_DIR

    # Check lockfile names
    if path.name in self.lockfile_names:
      return SkipReason.LOCKFILE

    return None

  def is_binary(self, path: Path) -> bool:
    """Determines if a file is binary using extension and byte inspection."""
    if path.suffix.lower() in BINARY_EXTENSIONS:
      return True

    try:
      with open(path, "rb") as f:
        chunk = f.read(1024)
        # Null bytes indicate binary content
        if b"\x00" in chunk:
          return True
        # Try decoding as UTF-8
        chunk.decode("utf-8")
        return False
    except (UnicodeDecodeError, OSError):
      return True

  def redact_secrets(self, content: str, file_path: Path) -> str:
    """Redacts API keys, tokens, and .env-style contents from file content."""
    # 1. Aggressively redact all values if it's an .env file
    if file_path.name.startswith(".env"):
      content = re.sub(
          r'(?m)^(\s*[^#\s=:]+\s*[=:]\s*)(["\']?.*["\']?)',
          r"\1[REDACTED_SECRET]",
          content,
      )

    # 2. Redact known token signatures
    for pattern in SECRET_PATTERNS:
      content = pattern.sub("[REDACTED_SECRET]", content)

    # 3. Redact inline key/password assignments
    content = ENV_ASSIGNMENT_PATTERN.sub(r"\1[REDACTED_SECRET]", content)

    return content

  def sanitize_file(self, path: Path) -> SanitizationResult:
    """Performs full sanitization check and secret redaction on a single file."""
    # 1. Check path exclusions
    skip_reason = self.is_excluded_path(path)
    if skip_reason:
      return SanitizationResult(
          original_path=path,
          included=False,
          skip_reason=skip_reason,
          redacted_content=None,
      )

    # 2. Check file size limit
    try:
      if path.stat().st_size > self.max_file_size_bytes:
        return SanitizationResult(
            original_path=path,
            included=False,
            skip_reason=SkipReason.OVER_SIZE_LIMIT,
            redacted_content=None,
        )
    except OSError:
      return SanitizationResult(
          original_path=path,
          included=False,
          skip_reason=SkipReason.BINARY,
          redacted_content=None,
      )

    # 3. Check binary file
    if self.is_binary(path):
      return SanitizationResult(
          original_path=path,
          included=False,
          skip_reason=SkipReason.BINARY,
          redacted_content=None,
      )

    # 4. Read content and redact secrets
    try:
      with open(path, "r", encoding="utf-8", errors="replace") as f:
        raw_content = f.read()

      clean_content = self.redact_secrets(raw_content, path)
      return SanitizationResult(
          original_path=path,
          included=True,
          skip_reason=None,
          redacted_content=clean_content,
      )
    except Exception:
      return SanitizationResult(
          original_path=path,
          included=False,
          skip_reason=SkipReason.BINARY,
          redacted_content=None,
      )

  def sanitize_tree(self, root_dir: Path) -> list[SanitizationResult]:
    """Recursively traverses root_dir, sanitizing all discoverable files."""
    root_dir = Path(root_dir)
    results: list[SanitizationResult] = []

    for file_path in root_dir.rglob("*"):
      if file_path.is_file():
        results.append(self.sanitize_file(file_path))

    return results