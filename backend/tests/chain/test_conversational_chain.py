from unittest.mock import MagicMock
from langchain_core.documents import Document
from backend.app.chain.conversational_chain import (
    ChatAnswer,
    Citation,
    RepoConversationalChain,
)
from backend.app.chain.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT


def test_prompts_contain_required_rules():
  assert "Standalone question:" in CONDENSE_QUESTION_PROMPT.template
  # Must contain refusal instruction per CLAUDE.md evaluation requirement
  assert (
      "I do not have sufficient context from this repository"
      in QA_PROMPT.template
  )
  assert "[file_path:Lstart-Lend]" in QA_PROMPT.template


def test_chain_returns_answer_and_citations():
  mock_retriever = MagicMock()
  mock_llm = MagicMock()

  # Instantiate chain
  repo_chain = RepoConversationalChain(retriever=mock_retriever, llm=mock_llm)

  # Mock chain.invoke output
  doc = Document(
      page_content="def auth(): pass",
      metadata={
          "file_path": "src/auth.py",
          "line_start": 10,
          "line_end": 20,
          "chunk_type": "function",
          "symbols": ["auth"],
          "content_hash": "abc",
      },
  )
  repo_chain.chain.invoke = MagicMock(
      return_value={
          "answer": "Authentication is in [src/auth.py:L10-L20].",
          "source_documents": [doc],
      }
  )

  res = repo_chain.ask("How does authentication work?")

  assert isinstance(res, ChatAnswer)
  assert "Authentication is in [src/auth.py:L10-L20]." in res.answer
  assert len(res.citations) == 1
  assert res.citations[0] == Citation(
      file_path="src/auth.py",
      line_start=10,
      line_end=20,
      chunk_type="function",
      symbols=["auth"],
  )