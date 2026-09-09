"""Aggregate metrics computed from an eval run's results."""

from eval.run_eval import EvalQuestion, EvalResult


def compute_refusal_accuracy(results: list[EvalResult], questions: list[EvalQuestion]) -> float:
    """Checks that expects_refusal questions actually produced a refusal-style answer."""
    ...


def compute_average_latency(results: list[EvalResult]) -> float:
    ...


def summarize(results: list[EvalResult], questions: list[EvalQuestion]) -> dict:
    """Returns the metrics dict that the README's eval numbers must be copied from verbatim."""
    ...
