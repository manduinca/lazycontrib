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
