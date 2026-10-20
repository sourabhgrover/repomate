from unittest.mock import MagicMock
from langchain_core.documents import Document
from backend.app.retrieval.ensemble import build_ensemble_retriever
from backend.app.retrieval.keyword_retriever import AtlasKeywordRetriever
from backend.app.retrieval.vector_retriever import AtlasVectorRetriever


def test_vector_retriever_maps_documents():
  mock_repo = MagicMock()
  mock_embedder = MagicMock()

  mock_embedder.embed_query.return_value = [0.1] * 384
  mock_repo.vector_search.return_value = [{
      "content": "def test(): pass",
      "repo_id": "test/repo",
      "file_path": "app/test.py",
      "language": "python",
      "chunk_type": "function",
      "symbols": ["test"],
      "line_start": 1,
      "line_end": 2,
      "content_hash": "hash123",
      "search_score": 0.95,
  }]

  retriever = AtlasVectorRetriever(
      chunk_repository=mock_repo,
      embedder=mock_embedder,
      repo_id="test/repo",
      top_k=5,
  )

  docs = retriever.invoke("How does test work?")

  assert len(docs) == 1
  assert docs[0].page_content == "def test(): pass"
  assert docs[0].metadata["file_path"] == "app/test.py"
  assert docs[0].metadata["retrieval_source"] == "vector"
  mock_repo.vector_search.assert_called_once()


def test_keyword_retriever_maps_documents():
  mock_repo = MagicMock()
  mock_repo.keyword_search.return_value = [{
      "content": "API_KEY = 'test'",
      "repo_id": "test/repo",
      "file_path": "app/config.py",
      "language": "python",
      "chunk_type": "module_level",
      "symbols": ["API_KEY"],
      "line_start": 1,
      "line_end": 1,
      "content_hash": "hash456",
      "search_score": 5.4,
  }]

  retriever = AtlasKeywordRetriever(
      chunk_repository=mock_repo,
      repo_id="test/repo",
      top_k=5,
  )

  docs = retriever.invoke("API_KEY")

  assert len(docs) == 1
  assert docs[0].page_content == "API_KEY = 'test'"
  assert docs[0].metadata["retrieval_source"] == "keyword"
  mock_repo.keyword_search.assert_called_once_with(
      repo_id="test/repo",
      query_text="API_KEY",
      top_k=5,
  )


def test_build_ensemble_retriever():
  mock_v = MagicMock(spec=AtlasVectorRetriever)
  mock_k = MagicMock(spec=AtlasKeywordRetriever)

  ensemble = build_ensemble_retriever(mock_v, mock_k, weights=(0.6, 0.4))
  assert len(ensemble.retrievers) == 2
  assert ensemble.weights == [0.6, 0.4]