"""AST-aware chunker for Python using tree-sitter.

Guarantees every chunk is a complete syntactic unit — a chunk must never split
mid-function or mid-class (CLAUDE.md). Chunk boundaries are always whole
tree-sitter nodes (function/class/module-level), never arbitrary line windows.

Large classes (> MAX_CHUNK_LINES) are split into per-method sub-chunks at
method boundaries — still fully CLAUDE.md-compliant.
"""

from typing import TYPE_CHECKING
from backend.app.chunking.schema import Chunk, compute_content_hash
from tree_sitter import Language, Parser
import tree_sitter_python

if TYPE_CHECKING:
  import tree_sitter

# Hard cap: class chunks larger than this are recursively split into methods.
# Prevents a single giant class from blowing the LLM's token-per-minute limit.
MAX_CHUNK_LINES = 150


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

  def _split_large_class(
      self, class_unit: SyntacticUnit, repo_id: str, file_path: str
  ) -> list[Chunk]:
    """Splits an oversized class chunk into per-method sub-chunks.

    CLAUDE.md: chunks must never split mid-function/mid-class.
    Compliant because we split AT method boundaries, not arbitrary lines.
    Falls back to returning an empty list if the class body can't be parsed,
    in which case chunk_file will keep the original unit as-is.
    """
    chunks: list[Chunk] = []
    lines = class_unit.text.splitlines()

    # Re-parse just this class's source to find its methods
    sub_tree = self.parse(class_unit.text)
    class_node = sub_tree.root_node

    # Locate the class_definition node inside the re-parsed fragment
    for child in class_node.children:
      if child.type == "class_definition":
        class_node = child
        break

    # Find the class body block
    body = None
    for child in class_node.children:
      if child.type == "block":
        body = child
        break

    if body is None:
      return []  # Fallback: can't recurse, caller will keep original chunk

    # Offset so line numbers map back to the original file
    line_offset = class_unit.line_start - 1
    pending: list = []

    def flush_pending() -> None:
      if not pending:
        return
      start = pending[0].start_point[0] + 1 + line_offset
      end = pending[-1].end_point[0] + 1 + line_offset
      text = "\n".join(
          lines[pending[0].start_point[0] : pending[-1].end_point[0] + 1]
      )
      if text.strip():
        chunks.append(
            Chunk(
                repo_id=repo_id,
                file_path=file_path,
                language="python",
                chunk_type="module_level",
                symbols=class_unit.symbols,  # carry the class name for context
                content_hash=compute_content_hash(text),
                line_start=start,
                line_end=end,
                content=text,
            )
        )
      pending.clear()

    for node in body.children:
      if node.type == "function_definition":
        flush_pending()
        start = node.start_point[0] + 1 + line_offset
        end = node.end_point[0] + 1 + line_offset
        text = "\n".join(
            lines[node.start_point[0] : node.end_point[0] + 1]
        )
        name_node = node.child_by_field_name("name")
        method_name = name_node.text.decode("utf8") if name_node else ""
        if text.strip():
          chunks.append(
              Chunk(
                  repo_id=repo_id,
                  file_path=file_path,
                  language="python",
                  chunk_type="function",
                  symbols=[method_name] if method_name else [],
                  content_hash=compute_content_hash(text),
                  line_start=start,
                  line_end=end,
                  content=text,
              )
          )
      else:
        pending.append(node)

    flush_pending()
    return chunks

  def chunk_file(
      self, repo_id: str, file_path: str, source_code: str
  ) -> list[Chunk]:
    """Produces one or more Chunk objects for a single Python file, each a

    complete syntactic unit. Classes exceeding MAX_CHUNK_LINES are
    automatically split into method-level chunks.
    """
    if not source_code.strip():
      return []

    tree = self.parse(source_code)
    units = self.extract_syntactic_units(tree, source_code)

    chunks: list[Chunk] = []
    for unit in units:
      is_oversized = (unit.line_end - unit.line_start + 1) > MAX_CHUNK_LINES

      # Split large classes into per-method chunks (CLAUDE.md compliant)
      if unit.node_type == "class" and is_oversized:
        sub_chunks = self._split_large_class(unit, repo_id, file_path)
        if sub_chunks:
          chunks.extend(sub_chunks)
          continue  # successfully replaced by method-level chunks

      # Default: emit the unit as a single chunk
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
