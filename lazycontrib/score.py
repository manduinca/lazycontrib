"""How likely is a pull request from an outside contributor to be merged here?

Trained on the recent pull requests that outside contributors opened in the repositories lazycontrib looks at,
with features known before writing a line of code. TabPFN when it is available, logistic regression otherwise.
"""
from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path

import numpy as np

from .discover import Candidate
from .github import CACHE, GitHub, GitHubError
from .profile import HOME

OUTSIDE = {"CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}
FEATURES = ["stars_log", "repo_merge_rate", "author_merged_before", "first_time", "linked_issue",
            "issue_age_days_log", "issue_comments", "help_wanted", "good_first", "bug", "size_log"]
EFFORT_SIZE = {"S": 40, "M": 200, "L": 800}

PULLS = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    stargazerCount
    pullRequests(last: 100, states: [MERGED, CLOSED], orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        createdAt merged authorAssociation additions deletions
        author { login }
        closingIssuesReferences(first: 1) {
          nodes { createdAt comments { totalCount } labels(first: 10) { nodes { name } } }
        }
      }
    }
  }
}"""


def _days(a: str, b: str) -> float:
    parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
    return max(0.0, (parse(b) - parse(a)).total_seconds() / 86400)


def repo_rows(gh: GitHub, repo: str) -> list[dict]:
    owner, name = repo.split("/", 1)
    try:
        data = gh.graphql(PULLS, {"owner": owner, "name": name})["repository"]
    except (GitHubError, TypeError):
        return []
    stars_log = math.log10(1 + data["stargazerCount"])
    rows, merged_seen, total_seen, by_author = [], 0, 0, {}
    for pr in data["pullRequests"]["nodes"]:
        login = (pr.get("author") or {}).get("login") or "ghost"
        if pr["authorAssociation"] in OUTSIDE:
            issue = (pr["closingIssuesReferences"]["nodes"] or [None])[0]
            labels = {l["name"].lower() for l in issue["labels"]["nodes"]} if issue else set()
            rows.append({
                "repo": repo, "created_at": pr["createdAt"], "merged": int(pr["merged"]),
                "stars_log": stars_log,
                "repo_merge_rate": (merged_seen + 1) / (total_seen + 2),
                "author_merged_before": by_author.get(login, 0),
                "first_time": int(pr["authorAssociation"] in {"FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER"}),
                "linked_issue": int(issue is not None),
                "issue_age_days_log": math.log1p(_days(issue["createdAt"], pr["createdAt"])) if issue else 0.0,
                "issue_comments": issue["comments"]["totalCount"] if issue else 0,
                "help_wanted": int("help wanted" in labels), "good_first": int("good first issue" in labels),
                "bug": int(any("bug" in l for l in labels)),
                "size_log": math.log1p(pr["additions"] + pr["deletions"]),
            })
            total_seen += 1
            merged_seen += int(pr["merged"])
        if pr["merged"]:
            by_author[login] = by_author.get(login, 0) + 1
    return rows


def dataset(gh: GitHub, repos: list[str]) -> list[dict]:
    rows = []
    for repo in repos:
        rows += repo_rows(gh, repo)
    return rows


def matrix(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    return (np.array([[r[f] for f in FEATURES] for r in rows], dtype=float),
            np.array([r.get("merged", 0) for r in rows], dtype=int))


def tabpfn_token() -> str | None:
    if os.environ.get("TABPFN_TOKEN"):
        return os.environ["TABPFN_TOKEN"]
    path = HOME / "tabpfn_token"
    return path.read_text().strip() if path.exists() else None


def make_model(kind: str = "auto"):
    if kind in ("auto", "tabpfn") and tabpfn_token():
        os.environ["TABPFN_TOKEN"] = tabpfn_token()
        try:
            from tabpfn import TabPFNClassifier
            return "tabpfn", TabPFNClassifier(device="cpu")
        except ImportError:
            if kind == "tabpfn":
                raise
    if kind == "tabpfn":
        raise RuntimeError("TabPFN needs a token: accept the license at https://ux.priorlabs.ai and save the key "
                           f"in {HOME / 'tabpfn_token'} or TABPFN_TOKEN")
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    return "logistic", make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))


def candidate_row(c: Candidate, repo_rows_: list[dict], effort: str, now_iso: str) -> dict:
    rate = repo_rows_[-1]["repo_merge_rate"] if repo_rows_ else 0.5
    if repo_rows_:
        merged = sum(r["merged"] for r in repo_rows_)
        rate = (merged + 1) / (len(repo_rows_) + 2)
    labels = {l.lower() for l in c.labels}
    return {"stars_log": math.log10(1 + c.stars), "repo_merge_rate": rate,
            "author_merged_before": c.welcomed_before, "first_time": int(c.welcomed_before == 0),
            "linked_issue": 1, "issue_age_days_log": math.log1p(_days(c.created_at, now_iso)),
            "issue_comments": c.comments_count, "help_wanted": int("help wanted" in labels),
            "good_first": int("good first issue" in labels), "bug": int(any("bug" in l for l in labels)),
            "size_log": math.log1p(EFFORT_SIZE.get(effort, 200))}


class Ranker:
    def __init__(self, kind: str = "auto"):
        self.kind, self.model = make_model(kind)
        self.trained_on = 0

    def fit(self, rows: list[dict]) -> Ranker:
        X, y = matrix(rows)
        if len(set(y)) < 2:
            raise ValueError("need both merged and closed pull requests to train")
        self.model.fit(X, y)
        self.trained_on = len(rows)
        return self

    def predict(self, rows: list[dict]) -> list[float]:
        X, _ = matrix(rows)
        return [round(float(p), 3) for p in self.model.predict_proba(X)[:, 1]]


def save_rows(rows: list[dict], path: Path | None = None) -> Path:
    path = path or CACHE / "training_rows.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows))
    return path
