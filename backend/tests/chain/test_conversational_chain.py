from unittest.mock import MagicMock
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.language_models.fake import FakeListLLM
from langchain_core.retrievers import BaseRetriever
from backend.app.chain.conversational_chain import (
    ChatAnswer,
    Citation,
    RepoConversationalChain,
)
from backend.app.chain.prompts import CONDENSE_QUESTION_PROMPT, QA_PROMPT


class DummyTestRetriever(BaseRetriever):

  def _get_relevant_documents(
      self, query: str, *, run_manager: CallbackManagerForRetrieverRun
  ) -> list[Document]:
    return []


def test_prompts_contain_required_rules():
  assert "Standalone question:" in CONDENSE_QUESTION_PROMPT.template
  assert (
      "I do not have sufficient context from this repository"
      in QA_PROMPT.template
  )
  assert "[file_path:Lstart-Lend]" in QA_PROMPT.template


def test_chain_returns_answer_and_citations(monkeypatch):
  dummy_retriever = DummyTestRetriever()
  fake_llm = FakeListLLM(
      responses=["Authentication is in [src/auth.py:L10-L20]."]
  )

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

  # Mock the underlying chain's invoke method using monkeypatch
  mock_chain = MagicMock()
  mock_chain.invoke.return_value = {
      "answer": "Authentication is in [src/auth.py:L10-L20].",
      "source_documents": [doc],
  }

  monkeypatch.setattr(
      RepoConversationalChain, "_build_chain", lambda self: mock_chain
  )

  repo_chain = RepoConversationalChain(retriever=dummy_retriever, llm=fake_llm)
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