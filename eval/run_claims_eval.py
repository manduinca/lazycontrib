"""Is the issue still free? lazycontrib (model + quote check) against the claim regex, on hand-labelled threads.

    python eval/run_claims_eval.py --snapshot eval/claims_threads.json --out eval/results/claims.json

The first run saves the threads to --snapshot; later runs read them from there, so results are reproducible.
"""
from __future__ import annotations

import argparse
import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

from lazycontrib import llm
from lazycontrib.assess import assess_issue
from lazycontrib.discover import CLAIM, MAINTAINERS, Candidate, enrich
from lazycontrib.github import GitHub
from lazycontrib.profile import Profile

ME = "manduinca"


def regex_status(c: Candidate, now: datetime) -> str:
    if c.open_prs:
        return "in_progress"
    claims = [x for x in c.comments
              if x["author"] != ME and x["association"] not in MAINTAINERS and CLAIM.search(x["body"])]
    if not claims:
        return "free"
    when = datetime.fromisoformat(claims[-1]["created_at"].replace("Z", "+00:00"))
    return "claimed" if (now - when).days <= 45 else "stale_claim"


def load_threads(gh: GitHub, refs: list[str], snapshot: Path) -> dict[str, Candidate]:
    if snapshot.exists():
        return {k: Candidate.model_validate(v) for k, v in json.loads(snapshot.read_text()).items()}
    threads = {}
    for ref in refs:
        repo, number = ref.split("#")
        item = gh.issue(repo, int(number))
        c = Candidate(repo=repo, number=int(number), url=item["html_url"], title=item["title"],
                      body=(item.get("body") or "")[:6000], labels=[l["name"] for l in item["labels"]],
                      created_at=item["created_at"], updated_at=item["updated_at"],
                      comments_count=item.get("comments", 0))
        threads[ref] = enrich(gh, c)
    snapshot.write_text(json.dumps({k: v.model_dump() for k, v in threads.items()}, indent=1, ensure_ascii=False))
    return threads


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=llm.MODEL)
    parser.add_argument("--set", choices=["dev", "test"], default="dev",
                        help="dev was used to write the prompts; test was labelled and never tuned on")
    parser.add_argument("--out")
    args = parser.parse_args()
    llm.MODEL = args.model
    here = Path(__file__).parent
    labels = yaml.safe_load((here / ("claims.yaml" if args.set == "dev" else "claims_test.yaml")).read_text())
    args.snapshot = here / ("claims_threads.json" if args.set == "dev" else "claims_threads_test.json")
    now = datetime.fromisoformat(labels["now"].replace("Z", "+00:00"))
    threads = load_threads(GitHub(), [i["ref"] for i in labels["issues"]], args.snapshot)
    profile = Profile(github=ME)
    rows = []
    for item in labels["issues"]:
        c = threads[item["ref"]]
        started = time.time()
        verdict = assess_issue(c, profile, now)
        rows.append({"ref": item["ref"], "expected": item["status"], "model": verdict.status,
                     "regex": regex_status(c, now), "reason": verdict.status_reason,
                     "dropped_claims": verdict.dropped_claims, "rejected_claims": verdict.rejected_claims,
                     "seconds": round(time.time() - started, 1)})
        print(f"{item['ref']:55s} expected={item['status']:12s} model={verdict.status:12s} "
              f"regex={rows[-1]['regex']}", flush=True)

    def summary(key: str) -> dict:
        hard = [r for r in rows if r["expected"] != "in_progress"]
        taken = lambda s: s in ("claimed", "stale_claim", "in_progress")
        return {"exact": f"{sum(r[key] == r['expected'] for r in rows)}/{len(rows)}",
                "exact_without_linked_pr": f"{sum(r[key] == r['expected'] for r in hard)}/{len(hard)}",
                "taken_vs_free_without_linked_pr": f"{sum(taken(r[key]) == taken(r['expected']) for r in hard)}/{len(hard)}",
                "said_free_but_taken": sum(r[key] == "free" and r["expected"] != "free" for r in rows)}

    result = {"model": args.model, "set": args.set, "issues": len(rows), "now": labels["now"],
              "lazycontrib": summary("model"), "regex_baseline": summary("regex"),
              "invented_claims_dropped": sum(r["dropped_claims"] for r in rows),
              "claims_rejected_on_second_check": sum(r["rejected_claims"] for r in rows),
              "confusion": Counter(f"{r['expected']}->{r['model']}" for r in rows if r["expected"] != r["model"])}
    print(json.dumps(result, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps({"summary": result, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
