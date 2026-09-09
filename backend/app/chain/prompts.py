"""Prompt templates for the conversational chain.

Design ownership: per CLAUDE.md, "Lead owns: architecture, retrieval chain/prompt
design" — even though this module lives in the Retrieval & API code tree (that
role owns "conversational chain" implementation/routing per CLAUDE.md).
"""

from langchain_core.prompts import PromptTemplate

# Rephrases a follow-up question into a standalone question using chat history.
CONDENSE_QUESTION_PROMPT: PromptTemplate

# Answers using only retrieved context; instructed to refuse when context is
# insufficient rather than guess (supports the eval suite's required
# "insufficient context, correctly refuses" test case).
QA_PROMPT: PromptTemplate
