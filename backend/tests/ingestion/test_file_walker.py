from pathlib import Path
from backend.app.ingestion.file_walker import FileWalker, RepoTooLargeError
from backend.app.ingestion.sanitizer import SanitizationResult
import pytest


def test_language_detection():
  walker = FileWalker(max_files=150)

  assert walker.detect_language(Path("main.py")) == "python"
  assert walker.detect_language(Path("README.md")) == "markdown"
  assert walker.detect_language(Path("app.tsx")) == "typescript"
  assert walker.detect_language(Path("script.sh")) == "bash"
  assert walker.detect_language(Path("unknown.xyz")) is None


def test_repo_too_large_enforcement(tmp_path: Path):
  # Set max_files to 3 for testing
  walker = FileWalker(max_files=3)

  # Create 4 fake approved file results (exceeding cap of 3)
  sanitizer_results = [
      SanitizationResult(
          original_path=tmp_path / f"file_{i}.py",
          included=True,
          skip_reason=None,
          redacted_content=f"# content {i}",
      )
      for i in range(4)
  ]

  # Must raise RepoTooLargeError per CLAUDE.md
  with pytest.raises(RepoTooLargeError):
    walker.walk(tmp_path, sanitizer_results)


def test_successful_walk(tmp_path: Path):
  walker = FileWalker(max_files=10)

  file1 = tmp_path / "main.py"
  sanitizer_results = [
      SanitizationResult(
          original_path=file1,
          included=True,
          skip_reason=None,
          redacted_content="print('ok')",
      )
  ]

  walked = walker.walk(tmp_path, sanitizer_results)

  assert len(walked) == 1
  assert walked[0].language == "python"
  assert walked[0].relative_path == "main.py"
  assert walked[0].content == "print('ok')"