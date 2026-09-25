# tests/chunking/test_chunker_registry.py
import pytest
from backend.app.chunking.chunker_registry import ChunkerRegistry, UnsupportedLanguageError


def test_supports_python():
  registry = ChunkerRegistry()
  assert registry.supports("python") is True


def test_does_not_support_javascript():
  registry = ChunkerRegistry()
  assert registry.supports("javascript") is False


def test_does_not_support_none():
  registry = ChunkerRegistry()
  assert registry.supports(None) is False


def test_chunk_python_file():
  registry = ChunkerRegistry()
  chunks = registry.chunk(
      repo_id="owner/repo",
      file_path="main.py",
      language="python",
      source_code="def hello():\n    pass\n",
  )
  assert len(chunks) >= 1
  assert chunks[0].language == "python"


def test_raises_for_unsupported_language():
  registry = ChunkerRegistry()
  with pytest.raises(UnsupportedLanguageError):
    registry.chunk(
        repo_id="owner/repo",
        file_path="app.js",
        language="javascript",
        source_code="function hello() {}",
    )


def test_raises_for_unknown_language():
  registry = ChunkerRegistry()
  with pytest.raises(UnsupportedLanguageError):
    registry.chunk(
        repo_id="owner/repo",
        file_path="data.xyz",
        language=None,
        source_code="some content",
    )