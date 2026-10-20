"""Prompt templates for the conversational chain.

Design ownership: per CLAUDE.md, "Lead owns: architecture, retrieval chain/prompt
design" — even though this module lives in the Retrieval & API code tree (that
role owns "conversational chain" implementation/routing per CLAUDE.md).
"""

from langchain_core.prompts import PromptTemplate

# Rephrases a follow-up question into a standalone question using chat history.
_CONDENSE_QUESTION_TEMPLATE = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question, in its original language.

Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""

CONDENSE_QUESTION_PROMPT = PromptTemplate.from_template(
    _CONDENSE_QUESTION_TEMPLATE
)


# Answers using only retrieved context; instructed to refuse when context is
# insufficient rather than guess (supports the eval suite's required
# "insufficient context, correctly refuses" test case).
_QA_TEMPLATE = """You are RepoMate, an expert AI assistant that answers technical questions about GitHub codebases.
Your task is to answer the user's question using ONLY the provided code and documentation context.

Guidelines:
1. Grounded Answers: Every claim, explanation, or code reference must be backed strictly by the provided context.
2. File Citations: Always cite the exact file path and line numbers when referencing code, formatted as `[file_path:Lstart-Lend]` (e.g., `[src/auth.py:L24-L45]`).
3. Hallucination Control / Strict Refusal: If the provided context does not contain enough information to answer the question accurately, explicitly state:
   "I do not have sufficient context from this repository to answer this question."
   Do NOT attempt to guess, extrapolate, or assume implementation details not present in the context.

Context:
{context}

Question: {question}
Helpful Answer:"""

QA_PROMPT = PromptTemplate(
    template=_QA_TEMPLATE,
    input_variables=["context", "question"],
)