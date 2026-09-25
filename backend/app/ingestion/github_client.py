"""Fetches a GitHub repo's contents to a local working directory for ingestion."""

from dataclasses import dataclass
import os
from pathlib import Path
import re
import git


@dataclass(frozen=True)
class RepoRef:
  """Identifies a GitHub repo + ref to ingest."""

  owner: str
  name: str
  ref: str = "main"

  @property
  def repo_id(self) -> str:
    """Returns canonical 'owner/name' identifier (e.g., 'fastapi/fastapi')."""
    return f"{self.owner}/{self.name}"

  @property
  def clone_url(self) -> str:
    """Returns standard public https clone URL."""
    return f"https://github.com/{self.owner}/{self.name}.git"


class GitHubClient:

  def __init__(self, github_token: str | None = None) -> None:
    self.github_token = github_token

  def _get_auth_url(self, repo_ref: RepoRef) -> str:
    """Appends github_token if present to avoid rate-limiting on clones."""
    if self.github_token:
      return f"https://{self.github_token}@github.com/{repo_ref.owner}/{repo_ref.name}.git"
    return repo_ref.clone_url

  def get_default_branch(self, repo_ref: RepoRef) -> str:
    """Queries the remote repo to detect the default branch (e.g., 'main' or 'master')."""
    url = self._get_auth_url(repo_ref)
    try:
      # ls-remote --symref queries HEAD without downloading the repo
      g = git.cmd.Git()
      output = g.ls_remote("--symref", url, "HEAD")
      # Output format: "ref: refs/heads/main  HEAD"
      match = re.search(r"ref:\s+refs/heads/(\S+)\s+HEAD", output)
      if match:
        return match.group(1)
    except Exception:
      pass
    return "main"  # Safe default fallback

  def clone_or_update(self, repo_ref: RepoRef, dest_dir: Path) -> Path:
    """Clones (or pulls if already present) repo_ref into dest_dir.

    Returns the local path to the checked-out working tree.
    """
    dest_dir = Path(dest_dir).resolve()
    clone_url = self._get_auth_url(repo_ref)

    # 1. If repo already exists locally, update it
    if (dest_dir / ".git").exists():
      try:
        repo = git.Repo(dest_dir)
        origin = repo.remotes.origin
        origin.fetch(depth=1)
        repo.git.checkout(repo_ref.ref)
        origin.pull()
        return dest_dir
      except Exception as e:
        raise RuntimeError(
            f"Failed to update existing repository at {dest_dir}: {e}"
        ) from e

    # 2. Fresh clone (shallow clone: depth=1 for speed & minimal disk use)
    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
      git.Repo.clone_from(
          url=clone_url,
          to_path=dest_dir,
          branch=repo_ref.ref,
          depth=1,
          single_branch=True,
      )
      return dest_dir
    except git.GitCommandError as e:
      raise RuntimeError(
          f"Failed to clone {repo_ref.repo_id} at ref '{repo_ref.ref}':"
          f" {e.stderr or str(e)}"
      ) from e