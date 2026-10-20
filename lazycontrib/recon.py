from __future__ import annotations

import json
import re
import subprocess
from collections import Counter
from pathlib import Path

from pydantic import BaseModel, Field

from . import llm
from .assess import IssueVerdict
from .discover import Candidate
from .github import CACHE

CODE_SPAN = re.compile(r"`([^`\n]{3,80})`")
PATH = re.compile(r"\b[\w./-]+\.(?:py|java|go|rs|ts|tsx|js|kt|scala|rb|cpp|cc|c|h|hpp|cs|md|rst|yaml|yml|toml)\b")
IDENT = re.compile(r"\b(?:[A-Z][a-z0-9]+){2,}[A-Za-z0-9]*\b|\b[a-z]+(?:_[a-z0-9]+)+\b|\b[a-z]+[A-Z]\w+\b")
STOP = {"pull_request", "good_first_issue", "help_wanted", "GitHub", "JavaScript", "TypeScript", "PyPI", "README"}


class Proposal(BaseModel):
    approach: list[str] = Field(description="3 to 6 concrete steps")
    files: list[str] = Field(description="repository paths to change, copied from the snippets")
    reuse: list[str] = Field(default_factory=list, description="existing functions, classes or helpers to build on, "
                                                               "as they are named in the snippets")
    tests: list[str] = Field(default_factory=list, description="tests to add or extend")
    risks: list[str] = Field(default_factory=list)


class Plan(BaseModel):
    proposal: Proposal
    files_checked: list[str]
    reuse_checked: list[str]
    dropped: list[str]
    searched: list[str]


def clone(repo: str) -> Path:
    target = CACHE / "repos" / repo.replace("/", "__")
    if (target / ".git").exists():
        subprocess.run(["git", "-C", str(target), "pull", "--quiet", "--depth", "1"], capture_output=True)
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--quiet", "--depth", "1", "--filter=blob:limit=2m",
                    f"https://github.com/{repo}.git", str(target)], check=True, capture_output=True, timeout=600)
    return target


def terms(candidate: Candidate, verdict: IssueVerdict) -> list[str]:
    text = "\n".join([candidate.title, candidate.body, *verdict.draft.must_do,
                      *(c["body"] for c in candidate.comments[-6:])])
    found: Counter = Counter()
    for span in CODE_SPAN.findall(text):
        for token in re.findall(r"[A-Za-z_][\w.]{2,}", span):
            found[token.split(".")[-1]] += 3
    for path in PATH.findall(text):
        found[path] += 4
    for ident in IDENT.findall(text):
        found[ident] += 1
    return [t for t, _ in found.most_common(30) if t not in STOP and len(t) > 3][:12]


def grep(root: Path, needles: list[str], max_files: int = 6, budget: int = 7000) -> tuple[str, Counter]:
    hits: Counter = Counter()
    lines_by_file: dict[str, list[int]] = {}
    for needle in needles:
        out = subprocess.run(["git", "-C", str(root), "grep", "-n", "-I", "-F", "-e", needle, "--", "."],
                             capture_output=True, text=True).stdout
        for line in out.splitlines()[:200]:
            path, number, _ = line.split(":", 2)
            hits[path] += 1
            lines_by_file.setdefault(path, []).append(int(number))
    snippets, used = [], 0
    for path, _ in hits.most_common(max_files):
        source = (root / path).read_text(errors="replace").splitlines()
        shown = set()
        for number in sorted(set(lines_by_file[path]))[:4]:
            window = range(max(1, number - 6), min(len(source), number + 6) + 1)
            if shown & set(window):
                continue
            shown |= set(window)
            block = "\n".join(f"{i}: {source[i - 1]}" for i in window)
            piece = f"--- {path}\n{block}\n"
            if used + len(piece) > budget:
                break
            snippets.append(piece)
            used += len(piece)
    return "".join(snippets), hits


PLAN_PROMPT = """You draft an implementation plan for an open source issue. The contributor will review it, write the
code and open the pull request themselves.
Use only files and names that appear in the snippets. Prefer extending an existing helper over repeating a fix
in several places. Cover everything in "must_do". Reply with JSON only."""


def plan(candidate: Candidate, verdict: IssueVerdict) -> Plan:
    root = clone(candidate.repo)
    searched = terms(candidate, verdict)
    snippets, _ = grep(root, searched)
    user = json.dumps({"issue": {"repo": candidate.repo, "title": candidate.title,
                                 "summary": verdict.draft.summary, "must_do": verdict.draft.must_do}},
                      ensure_ascii=False) + "\n\nCode snippets (path, line numbers):\n" + (snippets or "(no matches)")
    proposal, _ = llm.structured(PLAN_PROMPT, user, Proposal)
    files_ok, reuse_ok, dropped = [], [], []
    for path in proposal.files:
        clean = path.strip().lstrip("./")
        (files_ok if clean and (root / clean).is_file() else dropped).append(clean)
    for name in proposal.reuse:
        symbol = re.split(r"[\s(]", name.strip("` "), maxsplit=1)[0].split(".")[-1]
        found = symbol and subprocess.run(["git", "-C", str(root), "grep", "-q", "-F", "-e", symbol, "--", "."],
                                          capture_output=True).returncode == 0
        (reuse_ok if found else dropped).append(name)
    return Plan(proposal=proposal, files_checked=files_ok, reuse_checked=reuse_ok, dropped=dropped, searched=searched)
