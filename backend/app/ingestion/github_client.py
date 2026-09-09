"""Fetches a GitHub repo's contents to a local working directory for ingestion."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RepoRef:
    """Identifies a GitHub repo + ref to ingest."""

    owner: str
    name: str
    ref: str = "main"

    @property
    def repo_id(self) -> str:
        ...


class GitHubClient:
    def __init__(self, github_token: str | None = None) -> None:
        ...

    def clone_or_update(self, repo_ref: RepoRef, dest_dir: Path) -> Path:
        """Clones (or pulls if already present) repo_ref into dest_dir.

        Returns the local path to the checked-out working tree.
        """
        ...

    def get_default_branch(self, repo_ref: RepoRef) -> str:
        ...
