from lazycontrib.assess import IssueDraft, IssueVerdict, Policy, Rule
from lazycontrib.digest import html_page, markdown, write
from lazycontrib.discover import Candidate
from lazycontrib.pipeline import Opportunity, Report, Skipped
from lazycontrib.recon import Plan, Proposal


def report() -> Report:
    c = Candidate(repo="o/r", number=7, url="https://github.com/o/r/issues/7", title="Crash <on> empty input",
                  labels=["bug", "help wanted"], created_at="2026-09-01T00:00:00Z",
                  updated_at="2026-10-01T00:00:00Z", welcomed_before=2)
    draft = IssueDraft(summary="Fix the crash", must_do=["handle empty input", "add a test"], clarity="clear",
                       effort="S", fit="strong", fit_reason="Python, and they merged two of your PRs")
    plan = Plan(proposal=Proposal(approach=["Guard parse_header"], files=["src/x.py"], reuse=["parse_header"],
                                  tests=["test_empty"]), files_checked=["src/x.py"], reuse_checked=["parse_header"],
                dropped=[], searched=["parse_header"])
    policy = Policy(stance="conditions", must_disclose=True, dco=True,
                    rules=[Rule(flag="must_disclose", quote="Please disclose AI use.")])
    o = Opportunity(candidate=c, verdict=IssueVerdict(status="free", status_reason="nobody", draft=draft),
                    policy=policy, merge_odds=0.81, repo_merge_rate=0.7, reply_hours=5.0, score=0.7, plan=plan)
    return Report(user="me", model="gemma4:e4b", ranker="tabpfn on 100", created_at="2026-10-20T06:00+00:00",
                  seconds=12.0, looked_at=40, assessed=20, opportunities=[o],
                  skipped=[Skipped(url="https://github.com/o/r/issues/8", title="Taken", reason="@alice took it")])


def test_markdown_and_html_render_everything(tmp_path):
    r = report()
    md = markdown(r)
    assert "o/r#7" in md and "81%" in md and "say how you used AI" in md and "sign off commits" in md
    assert "`src/x.py`" in md and "@alice took it" in md
    page = html_page(r)
    assert "Crash &lt;on&gt; empty input" in page and "lazycontrib start o/r#7" in page
    paths = write(r, tmp_path)
    assert all(p.exists() for p in paths.values())


def test_plan_keeps_only_real_files_and_identifiers(monkeypatch, tmp_path):
    import json
    import subprocess

    from lazycontrib import llm, recon
    from lazycontrib.assess import IssueDraft, IssueVerdict
    from lazycontrib.discover import Candidate

    root = tmp_path / "repo"
    (root / "src").mkdir(parents=True)
    (root / "src" / "parse.py").write_text("def parse_header(text):\n    return text\n")
    (root / "docs" / "zero-code" / "go").mkdir(parents=True)
    (root / "docs" / "zero-code" / "go" / "autosdk.md").write_text("# autosdk\n")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    monkeypatch.setattr(recon, "clone", lambda repo: root)
    reply = {"approach": ["Guard parse_header"], "files": ["src/parse.py", "src/missing.py"],
             "reuse": ["parse_header", "No helper exists for this", "made_up_helper"], "tests": [], "risks": []}
    monkeypatch.setattr(llm, "chat", lambda messages, schema=None, timeout=300: json.dumps(reply))
    c = Candidate(repo="o/r", number=1, url="u", title="Crash in `parse_header`", body="See `zero-code/go/`",
                  created_at="2026-09-01T00:00:00Z", updated_at="2026-09-01T00:00:00Z")
    draft = IssueDraft(summary="s", must_do=["fix it"])
    p = recon.plan(c, IssueVerdict(status="free", status_reason="", draft=draft))
    assert p.files_checked == ["src/parse.py"] and p.reuse_checked == ["parse_header"]
    assert set(p.dropped) == {"src/missing.py", "No helper exists for this", "made_up_helper"}
    assert recon.path_matches(root, c) == ["docs/zero-code/go/autosdk.md"]
