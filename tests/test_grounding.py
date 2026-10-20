import json
from datetime import datetime, timezone

import pytest

from lazycontrib import assess, llm
from lazycontrib.discover import Candidate, RepoFacts
from lazycontrib.profile import Profile

NOW = datetime(2026, 10, 20, tzinfo=timezone.utc)


def fake_replies(monkeypatch, *replies):
    queue = [json.dumps(r) if isinstance(r, dict) else r for r in replies]
    monkeypatch.setattr(llm, "chat", lambda messages, schema=None, timeout=300: queue.pop(0))


@pytest.mark.parametrize("quote, source, expected", [
    ("You must test the change yourself", "**You must test the change yourself** and attach a screenshot.", True),
    ("discussions are for humans only", "Discussions on the OpenTelemetry repositories are for Users/Humans only.", False),
    ("Users/Humans only", "Discussions on the OpenTelemetry repositories are for Users/Humans only.", True),
    ("short", "short", False),
    ("I'll take this", "I’ll take this one if nobody minds", True),
])
def test_grounded(quote, source, expected):
    assert llm.grounded(quote, source) is expected


def test_policy_keeps_only_quoted_rules(monkeypatch):
    text = ("We welcome AI assistance. Contributors must disclose the use of AI tools in the PR description. "
            "Please test every change locally before opening a pull request.")
    facts = RepoFacts(repo="o/r", policy_text={"CONTRIBUTING.md": text}, ai_excerpts=[f"[CONTRIBUTING.md] {text}"])
    answers = {
        assess.QUESTIONS["must_disclose"]: {"applies": True, "quote": "must disclose the use of AI tools"},
        assess.QUESTIONS["no_autonomous_agents"]: {"applies": True, "quote": "agents may never open pull requests"},
    }

    def chat(messages, schema=None, timeout=300):
        if "Sentence:" in messages[-1]["content"]:
            return json.dumps({"says_it": True})
        question = messages[-1]["content"].split("\n", 1)[0].removeprefix("Question: ")
        return json.dumps(answers.get(question, {"applies": False, "quote": ""}))

    monkeypatch.setattr(llm, "chat", chat)
    policy = assess.assess_policy(facts)
    assert policy.must_disclose and not policy.no_autonomous_agents
    assert policy.stance == "conditions" and policy.dropped == 1


def test_policy_without_ai_text_skips_the_model(monkeypatch):
    monkeypatch.setattr(llm, "chat", lambda *a, **k: pytest.fail("model should not be called"))
    policy = assess.assess_policy(RepoFacts(repo="o/r", policy_text={"CONTRIBUTING.md": "Run the tests."}))
    assert policy.stance == "unspecified"


def candidate(**extra) -> Candidate:
    base = dict(repo="o/r", number=1, url="https://github.com/o/r/issues/1", title="Crash on empty input",
                created_at="2026-09-01T00:00:00Z", updated_at="2026-10-01T00:00:00Z",
                comments=[{"author": "alice", "association": "NONE", "created_at": "2026-10-10T00:00:00Z",
                           "body": "Hi! Can I work on this? I have an idea for the fix."},
                          {"author": "bob", "association": "MEMBER", "created_at": "2026-10-11T00:00:00Z",
                           "body": "The crash comes from parse_header returning None."}])
    return Candidate(**(base | extra))


DRAFT = {"summary": "Fix the crash", "must_do": ["handle empty input"], "maintainer_go_ahead": False,
         "clarity": "clear", "effort": "S", "fit": "ok", "fit_reason": "Python"}


def test_recent_grounded_claim_marks_the_issue_claimed(monkeypatch):
    fake_replies(monkeypatch, DRAFT | {"claims": [{"author": "@alice", "quote": "Can I work on this?"}]})
    verdict = assess.assess_issue(candidate(), Profile(github="me"), NOW)
    assert verdict.status == "claimed" and "alice" in verdict.status_reason


def test_invented_claim_is_dropped(monkeypatch):
    fake_replies(monkeypatch, DRAFT | {"claims": [{"author": "bob", "quote": "I will send a PR tomorrow"}]})
    verdict = assess.assess_issue(candidate(), Profile(github="me"), NOW)
    assert verdict.status == "free" and verdict.dropped_claims == 1


def test_old_claim_is_stale(monkeypatch):
    old = candidate(comments=[{"author": "alice", "association": "NONE", "created_at": "2025-01-01T00:00:00Z",
                               "body": "I'd like to work on this"}])
    fake_replies(monkeypatch, DRAFT | {"claims": [{"author": "alice", "quote": "I'd like to work on this"}]})
    assert assess.assess_issue(old, Profile(github="me"), NOW).status == "stale_claim"


def test_linked_open_pull_request_wins(monkeypatch):
    fake_replies(monkeypatch, DRAFT | {"claims": []})
    verdict = assess.assess_issue(candidate(open_prs=["https://github.com/o/r/pull/9"]), Profile(github="me"), NOW)
    assert verdict.status == "in_progress"


def test_repair_loop_recovers_from_bad_json(monkeypatch):
    fake_replies(monkeypatch, "not json at all", "```json\n" + json.dumps(DRAFT | {"claims": []}) + "\n```")
    draft, attempts = llm.structured("s", "u", assess.IssueDraft)
    assert attempts == 2 and draft.effort == "S"
