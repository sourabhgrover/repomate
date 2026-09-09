"""Runs the eval question set against a live RepoConversationalChain.

Must be re-run after any retrieval or prompt change before claiming an
improvement (CLAUDE.md). README metrics must be copied verbatim from a real
run's output, never estimated.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.app.chain.conversational_chain import RepoConversationalChain


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    repo_id: str
    question: str
    category: str  # "architecture" | "api_usage" | "debugging" | "insufficient_context"
    expects_refusal: bool = False
    reference_notes: str | None = None


def load_questions(path: str) -> list[EvalQuestion]:
    ...


@dataclass(frozen=True)
class EvalResult:
    question_id: str
    answer: str
    citations: list[dict]
    is_refusal: bool
    latency_seconds: float


def run_question(question: EvalQuestion, chain: "RepoConversationalChain") -> EvalResult:
    ...


def run_eval_suite(questions_path: str, chain: "RepoConversationalChain", output_dir: str) -> str:
    """Runs all questions, writes a timestamped results file, returns its path."""
    ...
