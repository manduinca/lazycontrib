"""Do merge odds rank outside pull requests better than the repo's merge rate alone?

Main split, per repository and in time: the oldest 75% of each repo's outside pull requests train, its newest 25%
test. A global time split is reported too: its test set is the last week across all repos, which is mostly quick
merges (rejections take longer to close), so it rewards the repo's merge rate.

    python eval/run_ranking_eval.py --out eval/results/ranking.json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from sklearn.metrics import brier_score_loss, roc_auc_score

from lazycontrib.discover import domain_repos
from lazycontrib.github import GitHub
from lazycontrib.profile import Profile
from lazycontrib.score import FEATURES, Ranker, dataset, matrix, save_rows


def top_share_precision(y: np.ndarray, p: np.ndarray, share: float = 0.2) -> float:
    k = max(1, int(len(p) * share))
    return float(y[np.argsort(-p)[:k]].mean())


def per_repo_split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    by_repo: dict[str, list[dict]] = {}
    for row in rows:
        by_repo.setdefault(row["repo"], []).append(row)
    train, test = [], []
    for repo_rows in by_repo.values():
        repo_rows.sort(key=lambda r: r["created_at"])
        cut = int(len(repo_rows) * 0.75)
        train += repo_rows[:cut]
        test += repo_rows[cut:]
    return train, test


def global_split(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    ordered = sorted(rows, key=lambda r: r["created_at"])
    cut = int(len(ordered) * 0.75)
    return ordered[:cut], ordered[cut:]


def evaluate(train: list[dict], test: list[dict]) -> dict:
    X_test, y = matrix(test)
    out = {"train": len(train), "test": len(test), "merged_share_test": round(float(y.mean()), 3),
           "test_from": min(r["created_at"] for r in test)[:10], "models": {}}
    candidates = {"repo merge rate alone": X_test[:, FEATURES.index("repo_merge_rate")]}
    for kind in ("logistic", "tabpfn"):
        candidates[kind] = np.array(Ranker(kind).fit(train).predict(test))
    for name, p in candidates.items():
        out["models"][name] = {"roc_auc": round(roc_auc_score(y, p), 3),
                               "brier": round(brier_score_loss(y, np.clip(p, 0, 1)), 3),
                               "merged_share_in_top_20pct": round(top_share_precision(y, p), 3)}
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", help="reuse saved training rows instead of fetching them")
    parser.add_argument("--out")
    args = parser.parse_args()
    if args.rows:
        rows = json.loads(Path(args.rows).read_text())
    else:
        gh = GitHub()
        profile = Profile.load()
        repos = list(dict.fromkeys(profile.watch + domain_repos(gh, profile, datetime.now(timezone.utc), limit=25)))
        rows = dataset(gh, repos)
        print(f"saved {save_rows(rows)}")
    result = {"repos": len({r["repo"] for r in rows}), "pull_requests": len(rows), "features": FEATURES}
    for name, (train, test) in {"per_repo_time_split": per_repo_split(rows),
                                "global_time_split": global_split(rows)}.items():
        result[name] = evaluate(train, test)
    print(json.dumps(result, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
