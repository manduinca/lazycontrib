"""Do merge odds rank outside pull requests better than the repo's merge rate alone?

Temporal split: train on the oldest 75% of outside-contributor pull requests, test on the newest 25%.

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
    rows.sort(key=lambda r: r["created_at"])
    cut = int(len(rows) * 0.75)
    train, test = rows[:cut], rows[cut:]
    _, y = matrix(test)
    result = {"repos": len({r["repo"] for r in rows}), "pull_requests": len(rows), "train": len(train),
              "test": len(test), "merged_share_test": round(float(y.mean()), 3),
              "test_from": test[0]["created_at"][:10], "features": FEATURES, "models": {}}
    X_test, _ = matrix(test)
    candidates = {"repo merge rate alone": X_test[:, FEATURES.index("repo_merge_rate")]}
    for kind in ("logistic", "tabpfn"):
        ranker = Ranker(kind).fit(train)
        candidates[f"{kind} ({ranker.kind})"] = np.array(ranker.predict(test))
    for name, p in candidates.items():
        result["models"][name] = {"roc_auc": round(roc_auc_score(y, p), 3),
                                  "brier": round(brier_score_loss(y, np.clip(p, 0, 1)), 3),
                                  "merged_share_in_top_20pct": round(top_share_precision(y, p), 3)}
    print(json.dumps(result, indent=2))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
