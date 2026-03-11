from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from git import GitCommandError, Repo

GITHUB_URL_PATTERN = re.compile(
    r"^(https://github\.com/|git@github\.com:)([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(\.git)?/?$"
)


class GitCloneError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def validate_github_url(repo_url: str) -> None:
    if not GITHUB_URL_PATTERN.match(repo_url.strip()):
        raise GitCloneError("INVALID_GITHUB_URL", "Invalid GitHub repository URL format.")


def _raise_clone_error(exc: Exception) -> None:
    message = str(exc).lower()
    if "authentication" in message or "access denied" in message:
        raise GitCloneError("REPO_ACCESS_DENIED", "Repository is private or access denied.") from exc
    if "could not resolve host" in message or "failed to connect" in message:
        raise GitCloneError("NETWORK_ERROR", "Network error while cloning repository.") from exc
    if "repository not found" in message:
        raise GitCloneError("REPO_NOT_FOUND", "Repository not found.") from exc
    raise GitCloneError("GIT_CLONE_FAILED", f"Failed to clone repository: {exc}") from exc


def clone_repository(repo_url: str, destination: Path, branch: Optional[str] = None) -> Path:
    validate_github_url(repo_url)

    clone_target = destination / "repo"
    clone_target.parent.mkdir(parents=True, exist_ok=True)

    kwargs = {"depth": 1, "single_branch": True}
    if branch:
        kwargs["branch"] = branch

    try:
        Repo.clone_from(repo_url, clone_target, **kwargs)
    except GitCommandError as exc:
        if branch:
            try:
                Repo.clone_from(repo_url, clone_target, depth=1, single_branch=True)
            except GitCommandError as branch_exc:
                _raise_clone_error(branch_exc)
        else:
            _raise_clone_error(exc)

    if not any(clone_target.rglob("*")):
        raise GitCloneError("EMPTY_REPOSITORY", "Repository appears to be empty.")

    return clone_target
