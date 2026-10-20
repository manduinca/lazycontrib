from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

from .profile import HOME

WORK = Path(os.environ.get("LAZYCONTRIB_WORK", Path.home() / "lazycontrib-work"))


def find_opportunity(ref: str) -> dict | None:
    """Look up owner/repo#123 in the most recent digest."""
    digests = sorted((HOME / "digests").glob("*.json"))
    for path in reversed(digests):
        for o in json.loads(path.read_text())["opportunities"]:
            c = o["candidate"]
            if f"{c['repo']}#{c['number']}" == ref:
                return o
    return None


def branch_name(o: dict) -> str:
    c = o["candidate"]
    labels = " ".join(c["labels"]).lower()
    kind = "docs" if "doc" in labels else "fix" if "bug" in labels else "feat"
    slug = re.sub(r"[^a-z0-9]+", "-", c["title"].lower()).strip("-")[:40].rstrip("-")
    return f"{kind}/{c['number']}-{slug}"


def start(ref: str) -> Path:
    """Clone the project, create a branch and leave the briefing next to the code. Nothing is pushed."""
    o = find_opportunity(ref)
    if o is None:
        raise SystemExit(f"{ref} is not in your digests; run `lazycontrib scan` first")
    repo = o["candidate"]["repo"]
    target = WORK / repo.replace("/", "__")
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "--quiet", f"https://github.com/{repo}.git", str(target)], check=True)
    branch = branch_name(o)
    subprocess.run(["git", "-C", str(target), "switch", "--quiet", "-c", branch], check=False)
    brief = target / ".lazycontrib" / "BRIEF.md"
    brief.parent.mkdir(exist_ok=True)
    brief.write_text(_brief(o))
    exclude = target / ".git" / "info" / "exclude"
    if ".lazycontrib/" not in exclude.read_text():
        exclude.write_text(exclude.read_text() + "\n.lazycontrib/\n")
    return target


def _brief(o: dict) -> str:
    c, d = o["candidate"], o["verdict"]["draft"]
    lines = [f"# {c['repo']}#{c['number']}: {c['title']}", "", c["url"], "", d["summary"], "", "## A complete fix"]
    lines += [f"- [ ] {m}" for m in d["must_do"]]
    if o.get("plan"):
        p = o["plan"]
        lines += ["", "## Draft plan (check it against the code)"]
        lines += [f"{i}. {s}" for i, s in enumerate(p["proposal"]["approach"], 1)]
        lines += [""]
        if p["files_checked"]:
            lines.append("Files: " + ", ".join(p["files_checked"]))
        if p["reuse_checked"]:
            lines.append("Build on: " + ", ".join(p["reuse_checked"]))
    policy = o["policy"]
    lines += ["", "## Before you open the pull request", "- [ ] I ran the tests and tried the change myself",
              "- [ ] The description and any replies are in my own words"]
    if policy.get("must_disclose"):
        lines.append("- [ ] I said how AI helped, as the project asks")
    if policy.get("human_testing_required"):
        lines.append("- [ ] I attached the evidence the project asks for (screenshots, logs, video)")
    if policy.get("dco"):
        lines.append("- [ ] Every commit is signed off (git commit -s)")
    lines += ["", "This file lives in .lazycontrib/, which git ignores in this clone."]
    return "\n".join(lines) + "\n"
