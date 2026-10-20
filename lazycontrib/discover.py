from __future__ import annotations

import re
import statistics
from datetime import datetime, timedelta, timezone
from typing import Any

from pydantic import BaseModel, Field

from .github import GitHub, GitHubError
from .profile import Profile

POLICY_FILES = ["AI_POLICY.md", "AI.md", "AGENTS.md", "AGENT_POLICY.md", ".github/AI_POLICY.md",
                "CONTRIBUTING.md", ".github/CONTRIBUTING.md", "docs/CONTRIBUTING.md", "CONTRIBUTING.rst",
                ".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md"]
AI_WORDS = re.compile(r"\b(AI|A\.I\.|LLMs?|large language model|generative|GenAI|ChatGPT|Copilot|Claude|Codex|"
                      r"agentic|coding agents?|AI[- ]assisted|AI[- ]generated|machine[- ]generated)\b", re.I)
CLAIM = re.compile(r"(i(?:'| a)?m (?:currently )?working on (?:this|it)|i(?:'|\s+wi)ll (?:take|work on|pick up|"
                   r"handle) (?:this|it)|can i (?:take|work on|be assigned|pick)|could i (?:take|work on|be assigned)|"
                   r"(?:please )?assign (?:this|it|me)|i'?d (?:like|love) to (?:work on|take|tackle|contribute)|"
                   r"^/assign|^/take|i have a (?:fix|patch|pr)|opened (?:a )?pr|i(?:'| ha)ve started)", re.I | re.M)
SKIP_LABELS = {"wontfix", "won't fix", "duplicate", "invalid", "not planned", "stale"}
MAINTAINERS = {"OWNER", "MEMBER", "COLLABORATOR"}


class Candidate(BaseModel):
    repo: str
    number: int
    url: str
    title: str
    body: str = ""
    labels: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    comments_count: int = 0
    stars: int = 0
    language: str | None = None
    repo_description: str = ""
    watched: bool = False
    welcomed_before: int = 0
    signals: list[str] = Field(default_factory=list)
    comments: list[dict] = Field(default_factory=list)
    open_prs: list[str] = Field(default_factory=list)
    closed_prs: list[str] = Field(default_factory=list)
    heuristic: float = 0.0


class RepoFacts(BaseModel):
    repo: str
    policy_text: dict[str, str] = Field(default_factory=dict)
    ai_excerpts: list[str] = Field(default_factory=list)
    dco: bool = False
    cla: bool = False
    maintainer_reply_hours: float | None = None
    replied_share: float | None = None


def _age_days(stamp: str, now: datetime) -> float:
    return (now - datetime.fromisoformat(stamp.replace("Z", "+00:00"))).total_seconds() / 86400


def _chunks(items: list[str], size: int) -> list[list[str]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def domain_repos(gh: GitHub, profile: Profile, now: datetime, limit: int = 30) -> list[str]:
    pushed = (now - timedelta(days=profile.max_days_since_push)).date().isoformat()
    found: dict[str, int] = {}
    for domain in profile.domains:
        query = f"topic:{domain} stars:>={profile.min_stars} pushed:>={pushed} archived:false"
        result = gh.get("/search/repositories", {"q": query, "sort": "stars", "per_page": 15})
        for repo in result.get("items", []):
            if not profile.languages or repo.get("language") in profile.languages:
                found[repo["full_name"]] = max(found.get(repo["full_name"], 0), repo["stargazers_count"])
    return [name for name, _ in sorted(found.items(), key=lambda kv: -kv[1])][:limit]


def discover(gh: GitHub, profile: Profile, history: list[dict], now: datetime | None = None,
             keep: int = 40) -> list[Candidate]:
    now = now or datetime.now(timezone.utc)
    welcomed = {}
    for pr in history:
        if pr["state"] == "merged":
            welcomed[pr["repo"]] = welcomed.get(pr["repo"], 0) + 1
    watch = [r for r in dict.fromkeys(profile.watch) if r not in profile.avoid]
    repos = watch + [r for r in domain_repos(gh, profile, now) if r not in watch and r not in profile.avoid]
    labels = ",".join(f'"{label}"' for label in profile.labels)

    seen: dict[str, Candidate] = {}
    for batch in _chunks(repos, 5):
        scope = " ".join(f"repo:{r}" for r in batch)
        for item in gh.search_issues(f"{scope} is:issue is:open no:assignee label:{labels}", limit=60):
            repo = item["repository_url"].split("/repos/", 1)[1]
            names = [label["name"] for label in item.get("labels", [])]
            if {n.lower() for n in names} & SKIP_LABELS:
                continue
            if _age_days(item["created_at"], now) > profile.max_issue_age_days:
                continue
            seen[item["html_url"]] = Candidate(
                repo=repo, number=item["number"], url=item["html_url"], title=item["title"],
                body=(item.get("body") or "")[:6000], labels=names, created_at=item["created_at"],
                updated_at=item["updated_at"], comments_count=item.get("comments", 0),
                watched=repo in watch, welcomed_before=welcomed.get(repo, 0))

    candidates = []
    for candidate in seen.values():
        meta = gh.repo(candidate.repo)
        if meta.get("archived") or _age_days(meta["pushed_at"], now) > profile.max_days_since_push:
            continue
        if not candidate.watched and meta.get("stargazers_count", 0) < profile.min_stars:
            continue
        candidate.stars = meta.get("stargazers_count", 0)
        candidate.language = meta.get("language")
        candidate.repo_description = meta.get("description") or ""
        candidate.heuristic = _heuristic(candidate, profile, now)
        candidates.append(candidate)
    candidates.sort(key=lambda c: -c.heuristic)
    return candidates[:keep]


def _heuristic(c: Candidate, profile: Profile, now: datetime) -> float:
    lower = {label.lower() for label in c.labels}
    score = 2.0 * min(c.welcomed_before, 3) + (1.0 if c.watched else 0.0)
    score += 1.0 if "help wanted" in lower else 0.0
    score += 0.6 if "bug" in lower else 0.0
    score += 0.8 if c.language in profile.languages else 0.0
    score -= 0.08 * min(c.comments_count, 20)
    score -= 0.6 * min(_age_days(c.created_at, now) / 365, 1.5)
    text = f"{c.title} {c.body} {c.repo_description}".lower()
    score += 0.4 * sum(1 for d in profile.domains if d.replace("-", " ") in text)
    return round(score, 3)


def enrich(gh: GitHub, candidate: Candidate) -> Candidate:
    comments = gh.comments(candidate.repo, candidate.number)
    candidate.comments = [{"author": c["user"]["login"], "association": c.get("author_association", "NONE"),
                           "created_at": c["created_at"], "body": (c.get("body") or "")[:1500]}
                          for c in comments]
    for event in gh.timeline(candidate.repo, candidate.number):
        source = (event.get("source") or {}).get("issue") or {}
        if event.get("event") == "cross-referenced" and source.get("pull_request"):
            ref = source["html_url"]
            merged = (source.get("pull_request") or {}).get("merged_at")
            (candidate.open_prs if source.get("state") == "open" else candidate.closed_prs).append(
                ref + (" (merged)" if merged else ""))
    signals = []
    if candidate.open_prs:
        signals.append(f"open pull request linked: {', '.join(candidate.open_prs[:3])}")
    for c in candidate.comments:
        if c["association"] not in MAINTAINERS and CLAIM.search(c["body"]):
            signals.append(f"possible claim by @{c['author']} on {c['created_at'][:10]}")
    candidate.signals = signals
    return candidate


def repo_facts(gh: GitHub, repo: str) -> RepoFacts:
    facts = RepoFacts(repo=repo)
    for path in POLICY_FILES:
        try:
            text = gh.file(repo, path)
        except GitHubError:
            text = None
        if text:
            facts.policy_text[path] = text[:20000]
    for path, text in facts.policy_text.items():
        for paragraph in re.split(r"\n\s*\n", text):
            if AI_WORDS.search(paragraph):
                facts.ai_excerpts.append(f"[{path}] {paragraph.strip()[:1200]}")
        facts.dco = facts.dco or bool(re.search(r"Developer Certificate of Origin|Signed-off-by|\bDCO\b", text))
        facts.cla = facts.cla or bool(re.search(r"Contributor License Agreement|\bCLA\b", text))
    facts.ai_excerpts = facts.ai_excerpts[:12]
    facts.maintainer_reply_hours, facts.replied_share = _responsiveness(gh, repo)
    return facts


RESPONSIVENESS = """
query($owner: String!, $name: String!) {
  repository(owner: $owner, name: $name) {
    issues(last: 30, orderBy: {field: CREATED_AT, direction: ASC}) {
      nodes {
        createdAt
        authorAssociation
        comments(first: 10) { nodes { createdAt authorAssociation } }
      }
    }
  }
}"""


def _responsiveness(gh: GitHub, repo: str) -> tuple[float | None, float | None]:
    owner, name = repo.split("/", 1)
    try:
        data = gh.graphql(RESPONSIVENESS, {"owner": owner, "name": name})
    except GitHubError:
        return None, None
    waits, outsider_issues = [], 0
    for issue in data["repository"]["issues"]["nodes"]:
        if issue["authorAssociation"] in MAINTAINERS:
            continue
        outsider_issues += 1
        opened = datetime.fromisoformat(issue["createdAt"].replace("Z", "+00:00"))
        for comment in issue["comments"]["nodes"]:
            if comment["authorAssociation"] in MAINTAINERS:
                replied = datetime.fromisoformat(comment["createdAt"].replace("Z", "+00:00"))
                waits.append((replied - opened).total_seconds() / 3600)
                break
    if not outsider_issues:
        return None, None
    median = round(statistics.median(waits), 1) if waits else None
    return median, round(len(waits) / outsider_issues, 2)


def issue_digest(candidate: Candidate, max_comments: int = 14) -> dict[str, Any]:
    comments = candidate.comments[-max_comments:]
    return {"repo": candidate.repo, "number": candidate.number, "title": candidate.title,
            "labels": candidate.labels, "opened": candidate.created_at[:10], "body": candidate.body[:4000],
            "comments": [f"@{c['author']} ({c['association'].lower()}, {c['created_at'][:10]}): {c['body'][:700]}"
                         for c in comments],
            "linked_pull_requests": {"open": candidate.open_prs, "closed": candidate.closed_prs}}
