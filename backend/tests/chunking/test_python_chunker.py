# tests/chunking/test_python_chunker.py
from backend.app.chunking.python_chunker import PythonChunker


def test_chunks_simple_function():
  chunker = PythonChunker()
  code = """\
def greet(name: str) -> str:
    return f"Hello, {name}"
"""
  chunks = chunker.chunk_file("owner/repo", "utils.py", code)
  assert len(chunks) == 1
  assert chunks[0].chunk_type == "function"
  assert "greet" in chunks[0].symbols
  assert chunks[0].line_start == 1
  assert chunks[0].line_end == 2


def test_chunks_class():
  chunker = PythonChunker()
  code = """\
class AuthService:
    def login(self, user):
        pass
"""
  chunks = chunker.chunk_file("owner/repo", "auth.py", code)
  assert any(c.chunk_type == "class" for c in chunks)
  assert any("AuthService" in c.symbols for c in chunks)


def test_never_splits_mid_function():
  chunker = PythonChunker()
  # A function with many lines — must come out as ONE single chunk
  code = """\
def long_function():
    x = 1
    y = 2
    z = 3
    a = 4
    b = 5
    return x + y + z + a + b
"""
  chunks = chunker.chunk_file("owner/repo", "long.py", code)
  function_chunks = [c for c in chunks if c.chunk_type == "function"]
  assert len(function_chunks) == 1
  assert function_chunks[0].line_start == 1
  assert function_chunks[0].line_end == 7


def test_decorator_kept_with_function():
  chunker = PythonChunker()
  code = """\
@app.get("/login")
def login_route():
    return {"status": "ok"}
"""
  chunks = chunker.chunk_file("owner/repo", "routes.py", code)
  function_chunks = [c for c in chunks if c.chunk_type == "function"]
  assert len(function_chunks) == 1
  # Decorator line must be inside the chunk
  assert "@app.get" in function_chunks[0].content


def test_module_level_imports_chunked():
  chunker = PythonChunker()
  code = """\
import os
import sys
SECRET = "xyz"
"""
  chunks = chunker.chunk_file("owner/repo", "config.py", code)
  assert any(c.chunk_type == "module_level" for c in chunks)


def test_empty_file_returns_no_chunks():
  chunker = PythonChunker()
  chunks = chunker.chunk_file("owner/repo", "empty.py", "")
  assert chunks == []


def test_content_hash_is_stable():
  chunker = PythonChunker()
  code = "def foo():\n    pass\n"
  chunks1 = chunker.chunk_file("owner/repo", "foo.py", code)
  chunks2 = chunker.chunk_file("owner/repo", "foo.py", code)
  # Same code must always produce identical content_hash
  assert chunks1[0].content_hash == chunks2[0].content_hash