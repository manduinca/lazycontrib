from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

from . import llm
from .discover import Candidate, RepoFacts, issue_digest
from .profile import Profile

Flag = Literal["ai_welcome", "ai_discouraged", "ai_prohibited", "must_disclose", "human_testing_required",
               "own_words_only", "no_autonomous_agents", "newcomer_issues_reserved"]


class Rule(BaseModel):
    flag: Flag
    quote: str = Field(description="exact words copied from the policy text")
    source: str = Field(description="file name the quote comes from")


class PolicyDraft(BaseModel):
    rules: list[Rule] = Field(default_factory=list)


class Policy(BaseModel):
    stance: Literal["welcome", "conditions", "discouraged", "prohibited", "unspecified"] = "unspecified"
    must_disclose: bool = False
    human_testing_required: bool = False
    own_words_only: bool = False
    no_autonomous_agents: bool = False
    newcomer_issues_reserved: bool = False
    dco: bool = False
    cla: bool = False
    rules: list[Rule] = Field(default_factory=list)
    dropped: int = 0


POLICY_PROMPT = """You read a project's contribution guidelines and extract its rules about AI-assisted contributions.
Reply with JSON only: {"rules": [{"flag": ..., "quote": ..., "source": ...}]}.
Flags:
- ai_welcome: AI tools are explicitly allowed or welcome
- ai_discouraged: AI use is discouraged but not banned
- ai_prohibited: AI-generated contributions are not accepted
- must_disclose: contributors must say when and how AI was used
- human_testing_required: the contributor must run or test the change personally, or attach screenshots or video
- own_words_only: descriptions, comments or replies must be written by the contributor, not by AI
- no_autonomous_agents: agents must not open pull requests or comment on their own
- newcomer_issues_reserved: beginner issues are meant for new human contributors
"quote" must be copied word for word from the text, at most two sentences. Only include flags the text supports.
If the text says nothing about AI, return {"rules": []}."""


def assess_policy(facts: RepoFacts) -> Policy:
    policy = Policy(dco=facts.dco, cla=facts.cla)
    if not facts.ai_excerpts:
        return policy
    text = "\n\n".join(facts.ai_excerpts)
    draft, _ = llm.structured(POLICY_PROMPT, f"Repository: {facts.repo}\n\n{text}", PolicyDraft)
    sources = list(facts.policy_text.values())
    kept = [rule for rule in draft.rules if llm.grounded(rule.quote, *sources)]
    flags = {rule.flag for rule in kept}
    policy.rules, policy.dropped = kept, len(draft.rules) - len(kept)
    policy.must_disclose = "must_disclose" in flags
    policy.human_testing_required = "human_testing_required" in flags
    policy.own_words_only = "own_words_only" in flags
    policy.no_autonomous_agents = "no_autonomous_agents" in flags
    policy.newcomer_issues_reserved = "newcomer_issues_reserved" in flags
    if "ai_prohibited" in flags:
        policy.stance = "prohibited"
    elif "ai_discouraged" in flags:
        policy.stance = "discouraged"
    elif flags & {"must_disclose", "human_testing_required", "own_words_only", "no_autonomous_agents"}:
        policy.stance = "conditions"
    elif "ai_welcome" in flags:
        policy.stance = "welcome"
    return policy


class Claim(BaseModel):
    author: str
    quote: str = Field(description="exact words from that comment")


class IssueDraft(BaseModel):
    summary: str = Field(description="one or two sentences: what the issue asks for")
    must_do: list[str] = Field(description="every concrete thing a complete fix has to do, including parts the "
                                           "issue calls optional")
    claims: list[Claim] = Field(default_factory=list, description="people who said they are working on it or "
                                                                   "asked to take it")
    maintainer_go_ahead: bool = Field(description="a maintainer agreed with the proposed approach or asked for a PR")
    open_questions: list[str] = Field(default_factory=list, description="decisions still open in the thread")
    clarity: Literal["clear", "needs_discussion", "vague"]
    effort: Literal["S", "M", "L"]
    fit: Literal["strong", "ok", "weak"]
    fit_reason: str


class IssueVerdict(BaseModel):
    status: Literal["free", "claimed", "stale_claim", "in_progress"]
    status_reason: str
    draft: IssueDraft
    dropped_claims: int = 0


ISSUE_PROMPT = """You help one open source contributor decide whether an issue is worth their time.
Reply with JSON only, following the schema. Be concrete and short.
- "claims": everyone in the comments who said they are working on the issue, asked to be assigned, or said
  they will open a pull request. Copy their words exactly in "quote". Maintainers explaining the issue are not claims.
- "must_do": the full scope. If the thread adds requirements or safeguards, include them.
- "fit": compare the issue with the contributor profile."""


def assess_issue(candidate: Candidate, profile: Profile, now: datetime | None = None) -> IssueVerdict:
    now = now or datetime.now(timezone.utc)
    me = {"languages": profile.languages, "domains": profile.domains, "skills": profile.skills,
          "has_merged_here_before": candidate.welcomed_before}
    user = json.dumps({"contributor": me, "issue": issue_digest(candidate)}, ensure_ascii=False)
    draft, _ = llm.structured(ISSUE_PROMPT, user, IssueDraft)

    bodies = {c["author"]: [] for c in candidate.comments}
    for c in candidate.comments:
        bodies[c["author"]].append(c)
    real, dropped = [], 0
    for claim in draft.claims:
        author = claim.author.lstrip("@")
        matches = [c for c in bodies.get(author, []) if llm.grounded(claim.quote, c["body"])]
        if matches and author != profile.github:
            real.append((author, matches[-1]["created_at"]))
        else:
            dropped += 1

    if candidate.open_prs:
        status, reason = "in_progress", f"open pull request: {candidate.open_prs[0]}"
    elif real:
        author, when = max(real, key=lambda r: r[1])
        age = (now - datetime.fromisoformat(when.replace("Z", "+00:00"))).days
        status = "claimed" if age <= 45 else "stale_claim"
        reason = f"@{author} said they would take it {age} days ago"
    else:
        status, reason = "free", "nobody has claimed it and no pull request is linked"
    return IssueVerdict(status=status, status_reason=reason, draft=draft, dropped_claims=dropped)
