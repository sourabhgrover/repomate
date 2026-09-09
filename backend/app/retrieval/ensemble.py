"""Combines vector + keyword retrievers into a single LangChain EnsembleRetriever.

This is the literal hybrid-search mechanism named in CLAUDE.md
("RAG framework: LangChain (EnsembleRetriever + ConversationalRetrievalChain)").
"""

from langchain.retrievers import EnsembleRetriever
from langchain_core.retrievers import BaseRetriever


def build_ensemble_retriever(
    vector_retriever: BaseRetriever,
    keyword_retriever: BaseRetriever,
    weights: tuple[float, float] = (0.5, 0.5),
) -> EnsembleRetriever:
    ...
