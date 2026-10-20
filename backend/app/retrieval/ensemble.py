"""Combines vector + keyword retrievers into a single LangChain EnsembleRetriever.

This is the literal hybrid-search mechanism named in CLAUDE.md
("RAG framework: LangChain (EnsembleRetriever + ConversationalRetrievalChain)").
"""

# pyright: reportMissingImports=false
try:
  from langchain_classic.retrievers import EnsembleRetriever  # type: ignore
except ImportError:
  try:
    from langchain.retrievers import EnsembleRetriever  # type: ignore
  except ImportError:
    from langchain_community.retrievers import (  # type: ignore
        EnsembleRetriever,
    )

from langchain_core.retrievers import BaseRetriever


def build_ensemble_retriever(
    vector_retriever: BaseRetriever,
    keyword_retriever: BaseRetriever,
    weights: tuple[float, float] = (0.5, 0.5),
) -> EnsembleRetriever:
  """Builds a LangChain EnsembleRetriever combining dense + sparse retrieval.

  Uses Reciprocal Rank Fusion (RRF) internally to merge and re-rank
  results from both retrievers into a single deduplicated list.

  Args:
      vector_retriever: AtlasVectorRetriever (semantic/dense leg).
      keyword_retriever: AtlasKeywordRetriever (Lucene BM25/sparse leg).
      weights: Relative importance of (vector, keyword). Default is equal (0.5,
        0.5).

  Returns:
      EnsembleRetriever: A single unified retriever ready to plug into
      ConversationalRetrievalChain.
  """
  return EnsembleRetriever(
      retrievers=[vector_retriever, keyword_retriever],
      weights=list(weights),
  )