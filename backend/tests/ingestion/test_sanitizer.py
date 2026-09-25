from pathlib import Path
from backend.app.ingestion.sanitizer import (
    DEFAULT_EXCLUDED_DIRS,
    DEFAULT_LOCKFILE_NAMES,
    Sanitizer,
    SkipReason,
)


def test_excluded_paths_vcs():
  sanitizer = Sanitizer()
  # VCS directories (.git) must be tagged with SkipReason.VCS_DIR
  assert (
      sanitizer.is_excluded_path(Path(".git/config")) == SkipReason.VCS_DIR
  )
  assert (
      sanitizer.is_excluded_path(Path("submodule/.git/HEAD"))
      == SkipReason.VCS_DIR
  )


def test_excluded_paths_dependencies():
  sanitizer = Sanitizer()
  # Dependency folders must be tagged with SkipReason.DEPENDENCY_DIR
  assert (
      sanitizer.is_excluded_path(Path("node_modules/express/index.js"))
      == SkipReason.DEPENDENCY_DIR
  )
  assert (
      sanitizer.is_excluded_path(Path(".venv/lib/site-packages/pytest.py"))
      == SkipReason.DEPENDENCY_DIR
  )
  assert (
      sanitizer.is_excluded_path(Path("__pycache__/main.cpython-311.pyc"))
      == SkipReason.DEPENDENCY_DIR
  )


def test_excluded_paths_lockfiles():
  sanitizer = Sanitizer()
  # Lockfiles must be tagged with SkipReason.LOCKFILE
  assert (
      sanitizer.is_excluded_path(Path("poetry.lock")) == SkipReason.LOCKFILE
  )
  assert (
      sanitizer.is_excluded_path(Path("nested/package-lock.json"))
      == SkipReason.LOCKFILE
  )
  assert (
      sanitizer.is_excluded_path(Path("yarn.lock")) == SkipReason.LOCKFILE
  )


def test_binary_detection(tmp_path: Path):
  sanitizer = Sanitizer()

  # Check extension-based binary
  assert sanitizer.is_binary(Path("logo.png")) is True
  assert sanitizer.is_binary(Path("binary.exe")) is True

  # Check null-byte binary file
  bin_file = tmp_path / "corrupt.txt"
  bin_file.write_bytes(b"hello\x00world")
  assert sanitizer.is_binary(bin_file) is True

  # Check normal text file
  text_file = tmp_path / "valid.py"
  text_file.write_text("print('hello')", encoding="utf-8")
  assert sanitizer.is_binary(text_file) is False


def test_secret_redaction():
  sanitizer = Sanitizer()

  dirty_content = """
    AWS_ACCESS_KEY = "AKIA1234567890ABCDEF"
    GITHUB_TOKEN = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    OPENAI_API_KEY = "sk-123456789012345678901234"
    PASSWORD = "SuperSecretPassword123"
    print("Clean code here")
    """

  clean_content = sanitizer.redact_secrets(dirty_content, Path("app/config.py"))

  # All sensitive values must be replaced
  assert "[REDACTED_SECRET]" in clean_content
  assert "AKIA1234567890ABCDEF" not in clean_content
  assert "ghp_1234567890abcdefghijklmnopqrstuvwxyz" not in clean_content
  assert "sk-123456789012345678901234" not in clean_content
  assert "SuperSecretPassword123" not in clean_content
  # Normal code must be preserved intact
  assert 'print("Clean code here")' in clean_content