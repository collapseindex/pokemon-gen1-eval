"""W2 from REVIEW2.md: how much of a table-format score is memory.

For each model, join the pinned table run (logs/pinned) with the recall run
(logs/recall: no chart, no typing list) by item, majority vote over epochs on
each side, and report on the 329 items where the Generation I and modern
charts agree:

  table hits        items the table run gets right (majority over epochs)
  also-recall       of those, the share the recall run also gets right
                    ("would have gotten it anyway")
  recall accuracy   recall majority accuracy on the same 329, and on all 400

The 71 "differs" items are excluded from the share because recall of the
modern chart is scored wrong there by construction.

    python -m src.recall_join
Writes data/results/<stamp>_recalljoin.json and prints the table.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

from .key import ROOT

RESULTS = ROOT / "data" / "results"


def majority_hits(log_dir: str, want_chart: str) -> dict[str, dict[tuple, bool]]:
    """model -> {(pokemon, attack_type): hit by majority over epochs}."""
    out: dict[str, dict[tuple, bool]] = {}
    strata: dict[tuple, str] = {}
    for info in list_eval_logs(str(ROOT / log_dir)):
        log = read_eval_log(info.name)
        args = log.eval.task_args or {}
        if log.status != "success" or args.get("chart", "gen1") != want_chart or args.get("chart_format", "table") != "table":
            continue
        if args.get("shuffle") or args.get("temperature") is not None:
            continue
        votes: dict[tuple, list[bool]] = defaultdict(list)
        for s in log.samples or []:
            sc = s.scores.get("choice") if s.scores else None
            if sc is None:
                continue
            meta = s.metadata or {}
            key = (meta["pokemon"], meta["attack_type"])
            strata[key] = meta.get("stratum", "")
            votes[key].append(sc.value == "C")
        model = log.eval.model.replace("openrouter/", "")
        out[model] = {k: sum(v) * 2 > len(v) for k, v in votes.items()}
    return out, strata


def main() -> None:
    table, strata = majority_hits("logs/pinned", "gen1")
    recall, _ = majority_hits("logs/recall", "none")
    rows = []
    for model in sorted(table, key=lambda m: m):
        if model not in recall:
            continue
        t, r = table[model], recall[model]
        agree = [k for k in t if strata.get(k) != "differs" and k in r]
        hits = [k for k in agree if t[k]]
        also = sum(1 for k in hits if r[k])
        rows.append({
            "model": model,
            "n_agree": len(agree),
            "table_hits_agree": len(hits),
            "also_recall": also,
            "share_also_recall": round(also / max(len(hits), 1), 3),
            "recall_acc_agree": round(sum(r[k] for k in agree) / max(len(agree), 1), 3),
            "recall_acc_all": round(sum(r.values()) / max(len(r), 1), 3),
            "table_acc_all": round(sum(t.values()) / max(len(t), 1), 3),
        })
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_recalljoin.json"
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"{'model':<34} agree  tbl-hits  also  share  recall(329) recall(400) table(400)")
    for r in rows:
        print(f"{r['model'].split('/')[-1]:<34} {r['n_agree']:>5} {r['table_hits_agree']:>9} {r['also_recall']:>5} {r['share_also_recall']:>6.2f} {r['recall_acc_agree']:>11.3f} {r['recall_acc_all']:>11.3f} {r['table_acc_all']:>10.3f}")
    print("wrote", path)


if __name__ == "__main__":
    main()
