from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

from .pipeline import Opportunity, Report
from .profile import HOME

STANCE = {"welcome": "AI help welcome", "conditions": "AI help allowed, with conditions",
          "discouraged": "AI help discouraged", "prohibited": "AI help not accepted",
          "unspecified": "no AI policy found"}


def _policy_lines(o: Opportunity) -> list[str]:
    p = o.policy
    lines = [STANCE[p.stance]]
    for flag, text in [("must_disclose", "say how you used AI"), ("human_testing_required", "test it yourself"),
                       ("own_words_only", "write the PR text and replies yourself"),
                       ("no_autonomous_agents", "no agents opening PRs or commenting"),
                       ("newcomer_issues_reserved", "beginner issues are for newcomers")]:
        if getattr(p, flag):
            lines.append(text)
    if p.dco:
        lines.append("sign off commits (DCO)")
    if p.cla:
        lines.append("sign the CLA")
    return lines


def markdown(report: Report) -> str:
    out = [f"# Your lazycontrib digest, {report.created_at[:10]}", "",
           f"Looked at {report.looked_at} open issues, read {report.assessed} closely, "
           f"kept {len(report.opportunities)}. Model: {report.model}. Ranking: {report.ranker}. "
           f"Took {report.seconds:.0f} s.", ""]
    for i, o in enumerate(report.opportunities, 1):
        c, d = o.candidate, o.verdict.draft
        out += [f"## {i}. {c.repo}#{c.number}: {c.title}", "", f"<{c.url}>", ""]
        odds = f"{o.merge_odds:.0%}" if o.merge_odds is not None else "unknown"
        facts = [f"**Status:** {o.verdict.status.replace('_', ' ')} ({o.verdict.status_reason})",
                 f"**Fit:** {d.fit}. {d.fit_reason}",
                 f"**Effort:** {d.effort} · **clarity:** {d.clarity.replace('_', ' ')}",
                 f"**Merge odds:** {odds}" + (f" · the repo merges {o.repo_merge_rate:.0%} of outside PRs"
                                              if o.repo_merge_rate is not None else "")
                 + (f" · maintainers reply in ~{o.reply_hours:.0f} h" if o.reply_hours is not None else ""),
                 f"**Policy:** {'; '.join(_policy_lines(o))}"]
        if c.welcomed_before:
            facts.insert(1, f"**They know you:** {c.welcomed_before} of your PRs merged here")
        out += [f"- {f}" for f in facts] + ["", f"**What it asks:** {d.summary}", ""]
        out += ["**A complete fix:**"] + [f"- {m}" for m in d.must_do] + [""]
        if d.open_questions:
            out += ["**Still open in the thread:**"] + [f"- {q}" for q in d.open_questions] + [""]
        if o.plan:
            pr = o.plan.proposal
            out += ["**Plan:**"] + [f"{n}. {step}" for n, step in enumerate(pr.approach, 1)] + [""]
            if o.plan.files_checked:
                out += ["Files: " + ", ".join(f"`{f}`" for f in o.plan.files_checked)]
            if o.plan.reuse_checked:
                out += ["Build on: " + ", ".join(f"`{r}`" for r in o.plan.reuse_checked)]
            if pr.tests:
                out += ["Tests: " + "; ".join(pr.tests)]
            if pr.risks:
                out += ["Risks: " + "; ".join(pr.risks)]
            out += [""]
        if o.policy.rules:
            out += ["<details><summary>Policy quotes</summary>", ""]
            out += [f"- `{r.flag}` ({r.source}): \"{r.quote}\"" for r in o.policy.rules] + ["", "</details>", ""]
        out += [f"Start: `lazycontrib start {c.repo}#{c.number}`", ""]
    if report.skipped:
        out += ["## Skipped, and why", ""] + [f"- [{s.title}]({s.url}): {s.reason}" for s in report.skipped]
    return "\n".join(out) + "\n"


def html_page(report: Report) -> str:
    cards = []
    for i, o in enumerate(report.opportunities, 1):
        c, d = o.candidate, o.verdict.draft
        e = html.escape
        odds = f"{o.merge_odds:.0%}" if o.merge_odds is not None else "–"
        plan = ""
        if o.plan:
            steps = "".join(f"<li>{e(s)}</li>" for s in o.plan.proposal.approach)
            files = " ".join(f"<code>{e(f)}</code>" for f in o.plan.files_checked)
            reuse = " ".join(f"<code>{e(r)}</code>" for r in o.plan.reuse_checked)
            plan = f"<h4>Plan</h4><ol>{steps}</ol>" + (f"<p>Files: {files}</p>" if files else "") + \
                   (f"<p>Build on: {reuse}</p>" if reuse else "")
        must = "".join(f"<li>{e(m)}</li>" for m in d.must_do)
        chips = "".join(f"<span class=chip>{e(x)}</span>" for x in _policy_lines(o))
        cards.append(f"""<article>
<header><span class=rank>{i}</span><div><a href="{e(c.url)}">{e(c.repo)}#{c.number}</a><h3>{e(c.title)}</h3></div>
<div class=odds><strong>{odds}</strong><span>merge odds</span></div></header>
<p class=meta>{e(o.verdict.status.replace('_', ' '))} · fit {e(d.fit)} · effort {e(d.effort)} · {e(d.clarity.replace('_', ' '))}
{f' · {c.welcomed_before} of your PRs merged here' if c.welcomed_before else ''}</p>
<p>{e(d.summary)}</p><p class=why>{e(d.fit_reason)}</p><div class=chips>{chips}</div>
<h4>A complete fix</h4><ul>{must}</ul>{plan}
<p class=start><code>lazycontrib start {e(c.repo)}#{c.number}</code></p></article>""")
    skipped = "".join(f"<li><a href='{html.escape(s.url)}'>{html.escape(s.title)}</a>: {html.escape(s.reason)}</li>"
                      for s in report.skipped)
    return f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>lazycontrib digest</title><style>
:root{{--bg:#f7f5ef;--card:#fff;--ink:#1d2321;--muted:#6b726f;--accent:#7a5c2e;--line:#e5e0d5}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121513;--card:#1b201d;--ink:#e7ece9;--muted:#9aa39f;--accent:#d8b072;--line:#2a312d}}}}
body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:860px;margin:0 auto;padding:24px 16px 48px}} h1{{margin:0 0 4px}} .lead{{color:var(--muted)}}
article{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:16px 0}}
article header{{display:flex;gap:12px;align-items:flex-start}} article h3{{margin:2px 0 0;font-size:17px}}
.rank{{font:700 20px ui-monospace,Menlo,monospace;color:var(--accent);min-width:28px}}
.odds{{margin-left:auto;text-align:right}} .odds strong{{display:block;font-size:22px}} .odds span{{font-size:11px;color:var(--muted)}}
.meta,.why{{color:var(--muted);font-size:13px}} .chips{{display:flex;flex-wrap:wrap;gap:6px}}
.chip{{border:1px solid var(--line);border-radius:999px;padding:2px 10px;font-size:12px}}
h4{{margin:14px 0 4px;font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}}
code{{font:12.5px ui-monospace,Menlo,monospace;background:rgba(127,127,127,.12);padding:1px 5px;border-radius:5px;word-break:break-all}}
a{{color:var(--accent)}} .start{{margin-top:12px}}
</style><main><h1>🦥 lazycontrib</h1>
<p class=lead>{report.created_at[:10]} · looked at {report.looked_at} issues, read {report.assessed}, kept {len(report.opportunities)} ·
model {html.escape(report.model)} · ranking {html.escape(report.ranker)}</p>
{''.join(cards)}<h2>Skipped, and why</h2><ul>{skipped or '<li>nothing</li>'}</ul></main></html>"""


def write(report: Report, folder: Path | None = None) -> dict[str, Path]:
    folder = folder or HOME / "digests"
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.fromisoformat(report.created_at).strftime("%Y-%m-%d-%H%M")
    paths = {"md": folder / f"{stamp}.md", "html": folder / f"{stamp}.html", "json": folder / f"{stamp}.json"}
    paths["md"].write_text(markdown(report))
    paths["html"].write_text(html_page(report))
    paths["json"].write_text(report.model_dump_json(indent=1))
    return paths
