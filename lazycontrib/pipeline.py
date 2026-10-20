from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Callable

from pydantic import BaseModel, Field

from . import llm
from .assess import IssueVerdict, Policy, assess_issue, assess_policy
from .discover import Candidate, discover, enrich, repo_facts
from .github import GitHub
from .profile import Profile, history
from .recon import Plan, plan
from .score import Ranker, candidate_row, dataset

FIT = {"strong": 1.0, "ok": 0.6, "weak": 0.2}
CLARITY = {"clear": 1.0, "needs_discussion": 0.6, "vague": 0.3}
EFFORT = {"S": 1.0, "M": 0.8, "L": 0.5}


class Opportunity(BaseModel):
    candidate: Candidate
    verdict: IssueVerdict
    policy: Policy
    merge_odds: float | None = None
    repo_merge_rate: float | None = None
    reply_hours: float | None = None
    score: float = 0.0
    plan: Plan | None = None
    plan_error: str | None = None


class Skipped(BaseModel):
    url: str
    title: str
    reason: str


class Report(BaseModel):
    user: str
    model: str
    ranker: str
    created_at: str
    seconds: float
    looked_at: int
    assessed: int
    opportunities: list[Opportunity] = Field(default_factory=list)
    skipped: list[Skipped] = Field(default_factory=list)


def scan(profile: Profile, gh: GitHub | None = None, assess_limit: int = 20, plans: int = 5,
         log: Callable[[str], None] = print) -> Report:
    started = time.time()
    gh = gh or GitHub()
    now = datetime.now(timezone.utc)
    past = history(gh, profile.github)
    log(f"Profile: {profile.github}, {sum(p['state'] == 'merged' for p in past)} merged pull requests to learn from")
    candidates = discover(gh, profile, past, now)
    log(f"Found {len(candidates)} open, unassigned issues in active repositories")

    policies: dict[str, Policy] = {}
    facts_by_repo = {}
    opportunities, skipped = [], []
    for candidate in candidates[:assess_limit]:
        try:
            enrich(gh, candidate)
            if candidate.repo not in policies:
                facts_by_repo[candidate.repo] = repo_facts(gh, candidate.repo)
                policies[candidate.repo] = assess_policy(facts_by_repo[candidate.repo])
        except Exception as error:
            skipped.append(Skipped(url=candidate.url, title=candidate.title, reason=f"could not read it: {error}"[:160]))
            continue
        policy = policies[candidate.repo]
        if policy.stance == "prohibited":
            skipped.append(Skipped(url=candidate.url, title=candidate.title,
                                   reason="the project does not accept AI-assisted contributions"))
            continue
        lower = {label.lower() for label in candidate.labels}
        if (profile.leave_newcomer_issues and "good first issue" in lower and candidate.welcomed_before
                and not lower & {"help wanted", "bug"}):
            skipped.append(Skipped(url=candidate.url, title=candidate.title,
                                   reason="left for newcomers: you already contribute here"))
            continue
        try:
            verdict = assess_issue(candidate, profile, now)
        except Exception as error:
            skipped.append(Skipped(url=candidate.url, title=candidate.title, reason=f"could not read it: {error}"[:160]))
            continue
        log(f"  {candidate.repo}#{candidate.number}: {verdict.status}, fit {verdict.draft.fit}, "
            f"effort {verdict.draft.effort}")
        if verdict.status in ("claimed", "in_progress"):
            skipped.append(Skipped(url=candidate.url, title=candidate.title, reason=verdict.status_reason))
            continue
        if verdict.draft.effort not in profile.effort:
            skipped.append(Skipped(url=candidate.url, title=candidate.title,
                                   reason=f"effort {verdict.draft.effort} is outside your profile"))
            continue
        opportunities.append(Opportunity(candidate=candidate, verdict=verdict, policy=policy,
                                         reply_hours=facts_by_repo[candidate.repo].maintainer_reply_hours))

    ranker_name = "none"
    if opportunities:
        repos = sorted({o.candidate.repo for o in opportunities} | set(profile.watch[:10]))
        rows = dataset(gh, repos)
        by_repo: dict[str, list[dict]] = {}
        for row in rows:
            by_repo.setdefault(row["repo"], []).append(row)
        try:
            ranker = Ranker().fit(rows)
            ranker_name = f"{ranker.kind} on {ranker.trained_on} outside pull requests"
            features = [candidate_row(o.candidate, by_repo.get(o.candidate.repo, []), o.verdict.draft.effort,
                                      now.isoformat()) for o in opportunities]
            for o, odds, row in zip(opportunities, ranker.predict(features), features):
                o.merge_odds, o.repo_merge_rate = odds, round(row["repo_merge_rate"], 2)
        except ValueError as error:
            log(f"Ranking skipped: {error}")
        for o in opportunities:
            odds = o.merge_odds if o.merge_odds is not None else 0.5
            o.score = round(odds * FIT[o.verdict.draft.fit] * CLARITY[o.verdict.draft.clarity]
                            * EFFORT[o.verdict.draft.effort] * (0.7 if o.verdict.status == "stale_claim" else 1.0)
                            * (0.8 if o.policy.stance == "discouraged" else 1.0), 3)
        opportunities.sort(key=lambda o: -o.score)
        for o in opportunities[:plans]:
            log(f"Planning {o.candidate.repo}#{o.candidate.number}")
            try:
                o.plan = plan(o.candidate, o.verdict)
            except Exception as error:
                o.plan_error = str(error)[:200]
    opportunities = opportunities[:profile.per_run]
    return Report(user=profile.github, model=llm.MODEL, ranker=ranker_name, created_at=now.isoformat(timespec="minutes"),
                  seconds=round(time.time() - started, 1), looked_at=len(candidates),
                  assessed=min(assess_limit, len(candidates)), opportunities=opportunities, skipped=skipped)
