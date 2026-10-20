"""How well does lazycontrib read AI policies? Compares the model + grounding against a keyword baseline.

    python eval/run_policy_eval.py --model gemma4:e4b --out eval/results-policies.json
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import yaml

from lazycontrib import llm
from lazycontrib.assess import Flag, assess_policy
from lazycontrib.discover import repo_facts
from lazycontrib.github import GitHub

FLAGS = list(Flag.__args__)
KEYWORDS = {
    "ai_welcome": r"welcome|we support using ai|may be used|not against|accept the use of ai",
    "ai_discouraged": r"discouraged",
    "ai_prohibited": r"no llms|forbidden|not accepted|prohibited|banned",
    "must_disclose": r"disclos|declare|indicate here how",
    "human_testing_required": r"tested by a human|proof of human testing|test it yourself|screenshots",
    "own_words_only": r"own words|by hand|written by humans|human voice|humans only|for communication",
    "no_autonomous_agents": r"autonomous agents|agents and bots|on your behalf",
    "newcomer_issues_reserved": r"reserved for (new|first)",
}


def keyword_flags(text: str) -> set[str]:
    lower = text.lower()
    return {flag for flag, pattern in KEYWORDS.items() if re.search(pattern, lower)}


def score(rows: list[dict], key: str) -> dict:
    tp = fp = fn = 0
    for row in rows:
        got, want = set(row[key]), set(row["expected"])
        tp += len(got & want)
        fp += len(got - want)
        fn += len(want - got)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    exact = sum(set(r[key]) == set(r["expected"]) for r in rows)
    return {"precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "repos_fully_right": f"{exact}/{len(rows)}"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=llm.MODEL)
    parser.add_argument("--set", choices=["dev", "test"], default="dev",
                        help="dev was used to write prompts and keywords; test was labelled and never tuned on")
    parser.add_argument("--out")
    args = parser.parse_args()
    llm.MODEL = args.model
    name = "policies.yaml" if args.set == "dev" else "policies_test.yaml"
    labels = yaml.safe_load(Path(__file__).with_name(name).read_text())
    gh = GitHub()
    rows = []
    for item in labels:
        facts = repo_facts(gh, item["repo"])
        started = time.time()
        policy = assess_policy(facts)
        model_flags = sorted({r.flag for r in policy.rules})
        rows.append({"repo": item["repo"], "expected": item["flags"], "stance_expected": item["stance"],
                     "model": model_flags, "stance": policy.stance, "dropped_quotes": policy.dropped,
                     "rejected_on_check": policy.rejected,
                     "kept_quotes": len(policy.rules), "seconds": round(time.time() - started, 1),
                     "keywords": sorted(keyword_flags("\n".join(facts.ai_excerpts)))})
        print(f"{item['repo']:45s} model={model_flags} expected={item['flags']} dropped={policy.dropped}", flush=True)
    summary = {
        "model": args.model, "set": args.set, "repos": len(rows),
        "model_with_grounding": score(rows, "model"),
        "keyword_baseline": score(rows, "keywords"),
        "stance_accuracy": f"{sum(r['stance'] == r['stance_expected'] for r in rows)}/{len(rows)}",
        "quotes_kept": sum(r["kept_quotes"] for r in rows),
        "quotes_dropped_as_ungrounded": sum(r["dropped_quotes"] for r in rows),
        "quotes_rejected_on_second_check": sum(r.get("rejected_on_check", 0) for r in rows),
    }
    print(json.dumps(summary, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps({"summary": summary, "rows": rows}, indent=2))


if __name__ == "__main__":
    main()
