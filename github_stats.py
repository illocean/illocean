"""Fail-closed GitHub statistics for the terminal generators."""

from dataclasses import dataclass
import os
from typing import Any
from urllib.parse import quote

import requests


_API = "https://api.github.com"
_TIMEOUT = 15
_PAGE_SIZE = 100


class StatsFetchError(RuntimeError):
    """Raised when GitHub stats cannot be fetched and fully verified."""


@dataclass(frozen=True)
class GithubStats:
    """Only values that can be displayed from a complete, valid read."""

    name: str
    repos: int
    followers: int
    stars: int
    commits: int
    prs: int
    issues: int
    top_languages: tuple[str, ...]


def _count(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise StatsFetchError(f"GitHub {field} must be a non-negative integer")
    return value


def _request_json(
    session: Any,
    url: str,
    headers: dict[str, str],
    params: dict[str, Any],
    label: str,
) -> Any:
    try:
        response = session.get(url, headers=headers, params=params, timeout=_TIMEOUT)
        status = getattr(response, "status_code", None)
        if not isinstance(status, int) or not 200 <= status < 300:
            raise StatsFetchError(f"GitHub {label} request returned HTTP {status}")
        raise_for_status = getattr(response, "raise_for_status", None)
        if callable(raise_for_status):
            raise_for_status()
        return response.json()
    except StatsFetchError:
        raise
    except Exception as exc:
        raise StatsFetchError(f"GitHub {label} request failed: {exc}") from exc


def _user(
    session: Any,
    username: str,
    headers: dict[str, str],
) -> tuple[str, int, int]:
    data = _request_json(
        session,
        f"{_API}/users/{username}",
        headers,
        {},
        "user",
    )
    if not isinstance(data, dict):
        raise StatsFetchError("GitHub user response was not a JSON object")
    if "name" not in data:
        raise StatsFetchError("GitHub user response omitted name")
    name = data["name"]
    if name is not None and not isinstance(name, str):
        raise StatsFetchError("GitHub user name was not a string or null")
    if "public_repos" not in data or "followers" not in data:
        raise StatsFetchError("GitHub user response omitted repository/follower counts")
    return name or username, _count(data["public_repos"], "public_repos"), _count(
        data["followers"], "followers"
    )


def _repositories(
    session: Any,
    username: str,
    headers: dict[str, str],
    expected_count: int,
) -> list[dict[str, Any]]:
    repositories: list[dict[str, Any]] = []
    page = 1
    while True:
        data = _request_json(
            session,
            f"{_API}/users/{username}/repos",
            headers,
            {"per_page": _PAGE_SIZE, "page": page, "type": "owner", "sort": "updated"},
            f"repositories page {page}",
        )
        if not isinstance(data, list):
            raise StatsFetchError(f"GitHub repositories page {page} was not a JSON array")
        if len(data) > _PAGE_SIZE:
            raise StatsFetchError(f"GitHub repositories page {page} exceeded the page size")
        for repository in data:
            if not isinstance(repository, dict):
                raise StatsFetchError(f"GitHub repositories page {page} contained a non-object")
            if "stargazers_count" not in repository or "language" not in repository:
                raise StatsFetchError(f"GitHub repository page {page} omitted required fields")
            _count(repository["stargazers_count"], "repository stargazers_count")
            language = repository["language"]
            if language is not None and not isinstance(language, str):
                raise StatsFetchError("GitHub repository language was not a string or null")
        repositories.extend(data)
        if len(repositories) == expected_count:
            return repositories
        if len(repositories) > expected_count:
            raise StatsFetchError("GitHub repository pagination exceeded public_repos")
        if not data:
            raise StatsFetchError("GitHub repository pagination ended before public_repos")
        page += 1


def _search_count(
    session: Any,
    kind: str,
    query: str,
    headers: dict[str, str],
) -> int:
    data = _request_json(
        session,
        f"{_API}/search/{kind}",
        headers,
        {"q": query, "per_page": 1},
        f"{kind} search",
    )
    if not isinstance(data, dict) or "total_count" not in data:
        raise StatsFetchError(f"GitHub {kind} search response omitted total_count")
    if "incomplete_results" in data:
        if not isinstance(data["incomplete_results"], bool):
            raise StatsFetchError(f"GitHub {kind} search response had invalid incomplete_results")
        if data["incomplete_results"]:
            raise StatsFetchError(f"GitHub {kind} search reported incomplete results")
    return _count(data["total_count"], f"{kind} search total_count")


def fetch_github_stats(
    username: str,
    token: str | None = None,
    session: Any | None = None,
) -> GithubStats:
    """Fetch all displayed stats, failing if any required read is incomplete."""
    if token is None:
        token = os.environ.get("GITHUB_TOKEN", "")
    if not isinstance(token, str) or not token.strip():
        raise StatsFetchError("GITHUB_TOKEN is required for reliable GitHub stats reads")
    if not isinstance(username, str) or not username.strip():
        raise StatsFetchError("GitHub username must not be empty")

    token = token.strip()
    username = username.strip()
    url_username = quote(username, safe="")
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if session is None:
        try:
            session = requests.Session()
        except Exception as exc:
            raise StatsFetchError(f"GitHub requests session could not be created: {exc}") from exc

    name, repos, followers = _user(session, url_username, headers)
    repositories = _repositories(session, url_username, headers, repos)
    language_counts: dict[str, int] = {}
    stars = 0
    for repository in repositories:
        stars += _count(repository["stargazers_count"], "repository stargazers_count")
        language = repository["language"]
        if language:
            language_counts[language] = language_counts.get(language, 0) + 1
    top_languages = tuple(
        language
        for language, _ in sorted(
            language_counts.items(), key=lambda item: (-item[1], item[0])
        )[:4]
    )

    commits = _search_count(session, "commits", f"author:{username}", headers)
    prs = _search_count(
        session,
        "issues",
        f"is:pr author:{username} is:merged",
        headers,
    )
    issues = _search_count(
        session,
        "issues",
        f"is:issue author:{username}",
        headers,
    )
    return GithubStats(
        name=name,
        repos=repos,
        followers=followers,
        stars=stars,
        commits=commits,
        prs=prs,
        issues=issues,
        top_languages=top_languages,
    )
