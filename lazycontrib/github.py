from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import httpx

API = "https://api.github.com"
CACHE = Path(os.environ.get("LAZYCONTRIB_CACHE", Path.home() / ".cache" / "lazycontrib"))
SEARCH_GAP_S = 2.2
DEBUG = bool(os.environ.get("LAZYCONTRIB_DEBUG"))


class GitHubError(RuntimeError):
    pass


def token() -> str:
    found = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if found:
        return found
    try:
        return subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        raise GitHubError("set GITHUB_TOKEN or log in with `gh auth login`")


class GitHub:
    """Read-only GitHub client with an on-disk cache. lazycontrib never writes to GitHub."""

    def __init__(self, ttl_s: float = 6 * 3600, client: httpx.Client | None = None):
        self.ttl_s = ttl_s
        self.http = client or httpx.Client(
            base_url=API, timeout=30,
            headers={"Authorization": f"Bearer {token()}", "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "lazycontrib"})
        self._last_search = 0.0

    def _cached(self, key: str, fetch) -> Any:
        path = CACHE / "http" / (hashlib.sha256(key.encode()).hexdigest() + ".json")
        if path.exists() and time.time() - path.stat().st_mtime < self.ttl_s:
            return json.loads(path.read_text())
        value = fetch()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        return value

    def get(self, path: str, params: dict | None = None, allow_404: bool = False) -> Any:
        key = f"GET {path} {json.dumps(params, sort_keys=True)}"

        def fetch():
            for attempt in range(7):
                if DEBUG:
                    print(f"  GET {path} {params or ''}", flush=True)
                try:
                    response = self.http.get(path, params=params)
                except httpx.TransportError:
                    time.sleep(2 * (attempt + 1))
                    continue
                if response.status_code == 404 and allow_404:
                    return None
                if response.status_code in (403, 429) and "rate limit" in response.text.lower():
                    retry = response.headers.get("retry-after")
                    reset = float(response.headers.get("x-ratelimit-reset", time.time() + 60))
                    wait = float(retry) if retry else min(65.0, max(3.0, reset - time.time() + 1))
                    if DEBUG:
                        print(f"  rate limited, waiting {wait:.0f}s", flush=True)
                    time.sleep(wait)
                    continue
                if response.status_code >= 500:
                    time.sleep(2 * (attempt + 1))
                    continue
                if response.status_code >= 400:
                    raise GitHubError(f"GET {path} -> {response.status_code}: {response.text[:200]}")
                return response.json()
            raise GitHubError(f"GET {path} kept failing")

        return self._cached(key, fetch)

    def pages(self, path: str, params: dict | None = None, limit: int = 300) -> list[Any]:
        items: list[Any] = []
        page = 1
        while len(items) < limit:
            batch = self.get(path, {**(params or {}), "per_page": 100, "page": page})
            items.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        return items[:limit]

    def search_issues(self, query: str, limit: int = 50) -> list[dict]:
        wait = SEARCH_GAP_S - (time.time() - self._last_search)
        if wait > 0:
            time.sleep(wait)
        self._last_search = time.time()
        result = self.get("/search/issues", {"q": query, "per_page": min(100, limit), "sort": "updated"})
        return result.get("items", [])[:limit]

    def graphql(self, query: str, variables: dict) -> dict:
        key = f"GRAPHQL {query} {json.dumps(variables, sort_keys=True)}"

        def fetch():
            for attempt in range(4):
                try:
                    response = self.http.post("/graphql", json={"query": query, "variables": variables})
                except httpx.TransportError:
                    time.sleep(2 * (attempt + 1))
                    continue
                if response.status_code >= 500:
                    time.sleep(2 * (attempt + 1))
                    continue
                try:
                    body = response.json()
                except ValueError:
                    time.sleep(2 * (attempt + 1))
                    continue
                if response.status_code >= 400 or body.get("errors"):
                    raise GitHubError(f"graphql: {str(body.get('errors') or response.text)[:300]}")
                return body["data"]
            raise GitHubError("graphql kept failing")

        return self._cached(key, fetch)

    def repo(self, full_name: str) -> dict:
        return self.get(f"/repos/{full_name}")

    def file(self, full_name: str, path: str) -> str | None:
        found = self.get(f"/repos/{full_name}/contents/{path}", allow_404=True)
        if not found or isinstance(found, list) or found.get("encoding") != "base64":
            return None
        return base64.b64decode(found["content"]).decode("utf-8", errors="replace")

    def issue(self, full_name: str, number: int) -> dict:
        return self.get(f"/repos/{full_name}/issues/{number}")

    def comments(self, full_name: str, number: int) -> list[dict]:
        return self.pages(f"/repos/{full_name}/issues/{number}/comments", limit=200)

    def timeline(self, full_name: str, number: int) -> list[dict]:
        return self.pages(f"/repos/{full_name}/issues/{number}/timeline", limit=300)
