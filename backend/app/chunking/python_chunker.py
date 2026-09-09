"""AST-aware chunker for Python using tree-sitter.

Guarantees every chunk is a complete syntactic unit — a chunk must never split
mid-function or mid-class (CLAUDE.md). Chunk boundaries are always whole
tree-sitter nodes (function/class/module-level), never arbitrary line windows.
"""

from typing import TYPE_CHECKING

from backend.app.chunking.schema import Chunk

if TYPE_CHECKING:
    import tree_sitter


class SyntacticUnit:
    """Internal representation of one AST node selected as a chunk boundary."""

    def __init__(
        self,
        node_type: str,
        symbols: list[str],
        line_start: int,
        line_end: int,
        text: str,
    ) -> None:
        ...


class PythonChunker:
    def __init__(self) -> None:
        ...  # loads tree-sitter Python grammar/parser

    def parse(self, source_code: str) -> "tree_sitter.Tree":
        ...

    def extract_syntactic_units(
        self, tree: "tree_sitter.Tree", source_code: str
    ) -> list[SyntacticUnit]:
        """Walks the AST, returning top-level function/class/module-level nodes
        with their line ranges. Boundaries always align to complete nodes."""
        ...

    def chunk_file(self, repo_id: str, file_path: str, source_code: str) -> list[Chunk]:
        """Produces one or more Chunk objects for a single Python file, each a
        complete syntactic unit."""
        ...
