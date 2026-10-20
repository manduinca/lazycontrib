from __future__ import annotations

import os
from collections import Counter
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

from .github import GitHub

HOME = Path(os.environ.get("LAZYCONTRIB_HOME", Path.home() / ".lazycontrib"))
OUTSIDER = {"CONTRIBUTOR", "FIRST_TIME_CONTRIBUTOR", "FIRST_TIMER", "NONE"}
GENERIC_TOPICS = {"hacktoberfest", "hacktoberfest2020", "hacktoberfest2021", "hacktoberfest2022", "hacktoberfest2023",
                  "open-source", "opensource", "library", "framework", "api", "awesome", "good-first-issue"}
NOT_LANGUAGES = {"Jupyter Notebook", "HTML", "CSS", "Makefile", "Dockerfile", "Shell", "TeX", "Markdown"}


class Profile(BaseModel):
    github: str
    languages: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list, description="keywords for what you care about")
    skills: list[str] = Field(default_factory=list, description="what you are good at, in your own words")
    labels: list[str] = Field(default_factory=lambda: ["good first issue", "help wanted", "bug"])
    watch: list[str] = Field(default_factory=list, description="owner/repo you want checked every run")
    avoid: list[str] = Field(default_factory=list, description="owner/repo to skip")
    min_stars: int = 50
    max_days_since_push: int = 45
    max_issue_age_days: int = 540
    effort: list[str] = Field(default_factory=lambda: ["S", "M"])
    leave_newcomer_issues: bool = True
    per_run: int = 12

    def save(self, path: Path | None = None) -> Path:
        path = path or HOME / "profile.yaml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(self.model_dump(), sort_keys=False, allow_unicode=True))
        return path

    @classmethod
    def load(cls, path: Path | None = None) -> Profile:
        path = path or HOME / "profile.yaml"
        if not path.exists():
            raise FileNotFoundError(f"no profile at {path}; run `lazycontrib init --github <you>` first")
        return cls.model_validate(yaml.safe_load(path.read_text()))


def history(gh: GitHub, user: str, limit: int = 200) -> list[dict]:
    """Public pull requests the user opened as an outside contributor."""
    found = gh.get("/search/issues", {"q": f"is:pr author:{user} -user:{user} is:public", "per_page": 100})
    items = found.get("items", [])
    if found.get("total_count", 0) > 100:
        more = gh.get("/search/issues", {"q": f"is:pr author:{user} -user:{user} is:public", "per_page": 100, "page": 2})
        items += more.get("items", [])
    rows = []
    for item in items[:limit]:
        if item.get("author_association") not in OUTSIDER:
            continue
        repo = item["repository_url"].split("/repos/", 1)[1]
        merged = (item.get("pull_request") or {}).get("merged_at")
        state = "merged" if merged else item["state"]
        rows.append({"repo": repo, "number": item["number"], "title": item["title"], "state": state,
                     "created_at": item["created_at"], "closed_at": item.get("closed_at")})
    return rows


def build(gh: GitHub, user: str) -> tuple[Profile, list[dict]]:
    prs = history(gh, user)
    welcomed = Counter(p["repo"] for p in prs if p["state"] == "merged")
    languages: Counter = Counter()
    topics: Counter = Counter()
    for repo_name in {p["repo"] for p in prs}:
        repo = gh.repo(repo_name)
        weight = 1 + welcomed[repo_name]
        if repo.get("language") and repo["language"] not in NOT_LANGUAGES:
            languages[repo["language"]] += weight
        for topic in repo.get("topics", []):
            if topic not in GENERIC_TOPICS and topic.lower() not in {l.lower() for l in languages} | {"python", "java", "go", "js", "javascript", "typescript", "golang", "docker"}:
                topics[topic] += weight
    profile = Profile(
        github=user,
        languages=[lang for lang, _ in languages.most_common(4)],
        domains=[t for t, n in topics.most_common(12) if n >= 2][:8],
        watch=[repo for repo, _ in welcomed.most_common(15)],
    )
    return profile, prs
