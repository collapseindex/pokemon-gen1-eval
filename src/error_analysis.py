"""Classify every miss in the pinned logs and build confusion matrices.

    python -m src.error_analysis --log-dir logs/pinned

Per sample, the first category that applies, in this order:

  unparsed    no ANSWER letter (truncation, host error, format miss)
  mirrored    predicted equals the key with attacker and defender swapped
              (only counted on cells where the mirror differs from the key)
  immunity    target is 0 and the prediction is not (the rule "doesn't affect"
              was overridden); or the reverse, a 0 predicted for a non-0 target
  multiply    same game word, one log2 step off: 4 read as 2, 1/4 as 1/2, or
              the reverse; both cells were read, the product was not
  lookup      everything else: at least one cell was read wrong or the wrong
              Pokemon was found; the aggregate cannot tell those apart

The order is a choice and is stated in the paper: a miss that is both mirrored
and one step off is filed as mirrored. Output: one JSON with, per (model,
format): n, exact, category counts, and the 6x6 confusion matrix in
multiplier order 0, 1/4, 1/2, 1, 2, 4 (rows target, columns predicted, plus an
unparsed column). Written to data/results/<stamp>_errors_<logdir>.json.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

from .analyze import _letter_to_mult, _transposed_key
from .key import MULTIPLIERS, ROOT

RESULTS = ROOT / "data" / "results"
CATEGORIES = ["unparsed", "mirrored", "immunity", "multiply", "lookup"]
BUCKET = {"0": "doesnt_affect", "1/4": "not_very", "1/2": "not_very", "1": "normal", "2": "super", "4": "super"}
LOG2 = {"1/4": -2, "1/2": -1, "1": 0, "2": 1, "4": 2}


def classify(target: str, predicted: str | None, mirrored: str | None) -> str | None:
    """None for a hit."""
    if predicted == target:
        return None
    if predicted is None:
        return "unparsed"
    if mirrored is not None and mirrored != target and predicted == mirrored:
        return "mirrored"
    if target == "0" or predicted == "0":
        return "immunity"
    if BUCKET[predicted] == BUCKET[target] and abs(LOG2[predicted] - LOG2[target]) == 1:
        return "multiply"
    return "lookup"


def analyse(log) -> dict:
    args = log.eval.task_args or {}
    chart = args.get("chart", "gen1")
    mirror = _transposed_key(chart)
    cats: Counter = Counter()
    confusion = defaultdict(Counter)
    by_stratum = defaultdict(Counter)
    n = hits = 0
    for s in log.samples or []:
        sc = s.scores.get("choice") if s.scores else None
        if sc is None:
            continue
        n += 1
        meta = s.metadata or {}
        target = _letter_to_mult(s.target if isinstance(s.target, str) else s.target[0])
        predicted = _letter_to_mult(sc.answer)
        m = mirror.get(meta.get("pokemon", ""), {}).get(meta.get("attack_type", ""))
        cat = classify(target, predicted, m)
        confusion[target][predicted or "unparsed"] += 1
        if cat is None:
            hits += 1
        else:
            cats[cat] += 1
            by_stratum[meta.get("stratum", "?")][cat] += 1
    order = MULTIPLIERS + ["unparsed"]
    return {
        "model": log.eval.model.replace("openrouter/", ""),
        "format": args.get("chart_format", "table"),
        "max_tokens": args.get("max_tokens", 1024),
        "epochs": log.eval.config.epochs or 1,
        "n": n,
        "exact": round(hits / n, 4) if n else None,
        "misses": n - hits,
        "categories": {c: cats.get(c, 0) for c in CATEGORIES},
        "categories_share_of_misses": {c: round(cats.get(c, 0) / max(n - hits, 1), 3) for c in CATEGORIES},
        "by_stratum": {st: {c: v.get(c, 0) for c in CATEGORIES} for st, v in sorted(by_stratum.items())},
        "confusion_order": order,
        "confusion": [[confusion[t].get(p, 0) for p in order] for t in MULTIPLIERS],
        "log": Path(log.location).name,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default="logs/pinned")
    a = ap.parse_args()
    log_dir = ROOT / a.log_dir
    rows = []
    for info in list_eval_logs(str(log_dir)):
        log = read_eval_log(info.name)
        if log.status == "success" and log.samples:
            rows.append(analyse(log))
    rows.sort(key=lambda r: (r["format"], r["model"]))
    RESULTS.mkdir(parents=True, exist_ok=True)
    out = RESULTS / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_errors_{log_dir.name}.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(f"{'model':<34}{'fmt':<6}{'n':>5}{'exact':>7}{'miss':>6}  " + "".join(f"{c:>10}" for c in CATEGORIES))
    for r in rows:
        print(f"{r['model'].split('/')[-1]:<34}{r['format']:<6}{r['n']:>5}{r['exact']:>7.3f}{r['misses']:>6}  " + "".join(f"{r['categories'][c]:>10}" for c in CATEGORIES))
    print("wrote", out)


if __name__ == "__main__":
    main()
