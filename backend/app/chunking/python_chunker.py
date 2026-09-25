"""AST-aware chunker for Python using tree-sitter.

Guarantees every chunk is a complete syntactic unit — a chunk must never split
mid-function or mid-class (CLAUDE.md). Chunk boundaries are always whole
tree-sitter nodes (function/class/module-level), never arbitrary line windows.
"""

from typing import TYPE_CHECKING
from backend.app.chunking.schema import Chunk, compute_content_hash
from tree_sitter import Language, Parser
import tree_sitter_python

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
    self.node_type = node_type
    self.symbols = symbols
    self.line_start = line_start
    self.line_end = line_end
    self.text = text


class PythonChunker:

  def __init__(self) -> None:
    """Loads tree-sitter Python grammar and initializes the parser."""
    py_language = Language(tree_sitter_python.language())
    try:
      self.parser = Parser(py_language)
    except TypeError:
      # Backward compatibility for older tree-sitter API versions
      self.parser = Parser()
      self.parser.set_language(py_language)

  def parse(self, source_code: str) -> "tree_sitter.Tree":
    """Parses raw Python source code into a tree-sitter AST."""
    return self.parser.parse(bytes(source_code, "utf8"))

  def extract_syntactic_units(
      self, tree: "tree_sitter.Tree", source_code: str
  ) -> list[SyntacticUnit]:
    """Walks the AST, returning top-level function/class/module-level nodes

    with their line ranges. Boundaries always align to complete nodes.
    """
    units: list[SyntacticUnit] = []
    lines = source_code.splitlines()
    pending_module_nodes = []

    def flush_module_nodes():
      """Groups module-level statements (imports, constants) into a single module_level chunk."""
      if not pending_module_nodes:
        return
      start_line = pending_module_nodes[0].start_point[0] + 1
      end_line = pending_module_nodes[-1].end_point[0] + 1
      chunk_text = "\n".join(lines[start_line - 1 : end_line])
      if chunk_text.strip():
        units.append(
            SyntacticUnit(
                node_type="module_level",
                symbols=[],
                line_start=start_line,
                line_end=end_line,
                text=chunk_text,
            )
        )
      pending_module_nodes.clear()

    # Iterate over top-level statements in the file
    for child in tree.root_node.children:
      target_node = child

      # 1. Handle decorated functions/classes (keep decorator attached to the chunk!)
      if child.type == "decorated_definition":
        for sub in child.children:
          if sub.type in ("function_definition", "class_definition"):
            target_node = sub
            break

      # 2. Extract function or class
      if target_node.type in ("function_definition", "class_definition"):
        flush_module_nodes()

        chunk_type = (
            "function"
            if target_node.type == "function_definition"
            else "class"
        )
        name_node = target_node.child_by_field_name("name")
        symbol_name = name_node.text.decode("utf8") if name_node else ""
        symbols = [symbol_name] if symbol_name else []

        # Use child's start_point so decorators are included in the chunk
        start_line = child.start_point[0] + 1
        end_line = child.end_point[0] + 1
        chunk_text = "\n".join(lines[start_line - 1 : end_line])

        units.append(
            SyntacticUnit(
                node_type=chunk_type,
                symbols=symbols,
                line_start=start_line,
                line_end=end_line,
                text=chunk_text,
            )
        )
      else:
        # Accumulate imports, module-level variables, and scripts
        pending_module_nodes.append(child)

    flush_module_nodes()
    return units

  def chunk_file(
      self, repo_id: str, file_path: str, source_code: str
  ) -> list[Chunk]:
    """Produces one or more Chunk objects for a single Python file, each a

    complete syntactic unit.
    """
    if not source_code.strip():
      return []

    tree = self.parse(source_code)
    units = self.extract_syntactic_units(tree, source_code)

    chunks: list[Chunk] = []
    for unit in units:
      chunks.append(
          Chunk(
              repo_id=repo_id,
              file_path=file_path,
              language="python",
              chunk_type=unit.node_type,
              symbols=unit.symbols,
              content_hash=compute_content_hash(unit.text),
              line_start=unit.line_start,
              line_end=unit.line_end,
              content=unit.text,
          )
      )

    return chunks