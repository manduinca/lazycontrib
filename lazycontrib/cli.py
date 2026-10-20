from __future__ import annotations

import argparse
import sys

from . import llm
from .github import GitHub


def cmd_init(args) -> None:
    from .profile import build
    profile, prs = build(GitHub(), args.github)
    path = profile.save()
    merged = sum(p["state"] == "merged" for p in prs)
    print(f"Built your profile from {len(prs)} public pull requests ({merged} merged).")
    print(f"Languages: {', '.join(profile.languages) or 'none found'}")
    print(f"Domains:   {', '.join(profile.domains) or 'none found, add a few'}")
    print(f"Edit it before the first scan: {path}")


def cmd_scan(args) -> None:
    from .digest import write
    from .pipeline import scan
    from .profile import Profile
    if args.model:
        llm.MODEL = args.model
    report = scan(Profile.load(), assess_limit=args.read, plans=args.plans)
    paths = write(report)
    print(f"\n{len(report.opportunities)} opportunities, {len(report.skipped)} skipped, {report.seconds:.0f} s")
    for i, o in enumerate(report.opportunities[:5], 1):
        odds = f"{o.merge_odds:.0%}" if o.merge_odds is not None else "  –"
        print(f"  {i}. {odds:>4}  {o.candidate.repo}#{o.candidate.number}  {o.candidate.title[:70]}")
    print(f"\nDigest: {paths['html']}\n        {paths['md']}")


def cmd_start(args) -> None:
    from .workspace import start
    path = start(args.ref)
    print(f"Workspace ready: {path}")
    print("Read .lazycontrib/BRIEF.md, write the change, and fork when you are ready to push:")
    print(f"  cd {path} && gh repo fork --remote")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="lazycontrib", description="Open source issues that fit you, read for you.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init", help="build your profile from your public pull requests")
    p.add_argument("--github", required=True)
    p.set_defaults(func=cmd_init)
    p = sub.add_parser("scan", help="find, read and rank issues, and write a digest")
    p.add_argument("--read", type=int, default=20, help="issues to read closely with the model")
    p.add_argument("--plans", type=int, default=5, help="top issues to draft a plan for")
    p.add_argument("--model", help="model name on your Ollama or OpenAI-compatible endpoint")
    p.set_defaults(func=cmd_scan)
    p = sub.add_parser("start", help="clone, branch and leave the briefing next to the code; never pushes")
    p.add_argument("ref", help="owner/repo#123 from your digest")
    p.set_defaults(func=cmd_start)
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except (FileNotFoundError, llm.LLMError) as error:
        sys.exit(str(error))


if __name__ == "__main__":
    main()
