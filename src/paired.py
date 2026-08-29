"""Paired tests over items for the comparisons the paper makes (review 4).

Every run saw the same pinned 400 items, so a difference between two runs is
a paired difference. For each named pair this script reports, over items:

  d           mean accuracy difference (per-item epoch means), run B minus A
  boot95      95% paired bootstrap interval on d (10,000 resamples, seed 0)
  mcnemar     exact McNemar p on per-item majority hits (b discordant one way,
              c the other; two-sided binomial)

Also, for the answer-class confound the review raised: per model, accuracy
on the "differs" stratum against the rest of the pinned set within each
answer class, so the differs gap is compared like with like.

    python -m src.paired
Writes data/results/<stamp>_paired.json and prints both tables.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import datetime
from math import comb
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

from .key import ROOT

RESULTS = ROOT / "data" / "results"
BOOT = 10_000


def per_item(log_dir: str, want: dict) -> dict[str, dict[str, list[float]]]:
    """model -> item_id -> list of hits (one per epoch), for logs matching `want` task args."""
    out: dict[str, dict[str, list[float]]] = {}
    meta: dict[str, dict] = {}
    for info in list_eval_logs(str(ROOT / log_dir)):
        log = read_eval_log(info.name)
        args = log.eval.task_args or {}
        if log.status != "success" or any(args.get(k, d) != v for k, (v, d) in want.items()):
            continue
        model = log.eval.model.split("/")[-1]
        hits: dict[str, list[float]] = defaultdict(list)
        for s in log.samples or []:
            sc = s.scores.get("choice") if s.scores else None
            if sc is None:
                continue
            hits[str(s.id)].append(1.0 if sc.value == "C" else 0.0)
            meta[str(s.id)] = s.metadata or {}
        out[model] = dict(hits)
    return out, meta


def mcnemar(a: dict[str, list[float]], b: dict[str, list[float]]) -> tuple[int, int, float]:
    items = sorted(set(a) & set(b))
    maj = lambda v: sum(v) * 2 > len(v)
    x = sum(1 for i in items if maj(a[i]) and not maj(b[i]))
    y = sum(1 for i in items if maj(b[i]) and not maj(a[i]))
    n = x + y
    if n == 0:
        return x, y, 1.0
    k = min(x, y)
    p = sum(comb(n, j) for j in range(0, k + 1)) / 2 ** n * 2
    return x, y, min(p, 1.0)


def boot(a: dict[str, list[float]], b: dict[str, list[float]]) -> tuple[float, float, float]:
    items = sorted(set(a) & set(b))
    diffs = [sum(b[i]) / len(b[i]) - sum(a[i]) / len(a[i]) for i in items]
    d = sum(diffs) / len(diffs)
    rng = random.Random(0)
    n = len(diffs)
    samples = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(BOOT))
    return d, samples[int(0.025 * BOOT)], samples[int(0.975 * BOOT) - 1]


def main() -> None:
    table, meta = per_item("logs/pinned", {"chart_format": ("table", "table"), "chart": ("gen1", "gen1")})
    rows, _ = per_item("logs/pinned", {"chart_format": ("rows", "table"), "chart": ("gen1", "gen1")})
    pairs = [
        ("llama-3.2-1b-instruct", "llama-3.2-3b-instruct", table, table, "Llama 1B -> 3B, table"),
        ("llama-3.2-3b-instruct", "llama-3.1-8b-instruct", table, table, "Llama 3B -> 8B, table"),
        ("llama-3.2-1b-instruct", "llama-3.1-8b-instruct", table, table, "Llama 1B -> 8B, table"),
        ("gemma-3-4b-it", "gemma-3-12b-it", table, table, "Gemma 4B -> 12B, table"),
        ("gemma-3-4b-it", "llama-3.1-8b-instruct", table, table, "Gemma 4B vs Llama 8B, table"),
        ("gemma-3-27b-it", "qwen3-30b-a3b-instruct-2507", table, table, "Gemma 27B vs Qwen 30B-A3B, table"),
        ("qwen3-30b-a3b-instruct-2507", "qwen3-32b", table, table, "Qwen 30B-A3B vs 32B, table"),
        ("qwen3-235b-a22b-2507", "qwen3-32b", table, table, "Qwen 235B-A22B vs 32B, table"),
    ] + [(m, m, table, rows, f"{m.split('-instruct')[0]}: table -> rows") for m in table if m in rows]
    out = []
    print(f"{'comparison':<40} {'d':>7} {'boot95':>18} {'b/c':>9} {'McNemar p':>10}")
    for a_name, b_name, A, B, label in pairs:
        if a_name not in A or b_name not in B:
            continue
        d, lo, hi = boot(A[a_name], B[b_name])
        x, y, p = mcnemar(A[a_name], B[b_name])
        out.append({"comparison": label, "a": a_name, "b": b_name, "d": round(d, 4), "boot95": [round(lo, 4), round(hi, 4)], "discordant": [x, y], "mcnemar_p": round(p, 5)})
        print(f"{label:<40} {d:+.3f} [{lo:+.3f}, {hi:+.3f}]   {x:>3}/{y:<3} {p:>10.4f}")

    # differs vs rest within answer class, table format
    print("\ndiffers stratum vs rest, within answer class (table, per-item epoch mean); n in parentheses")
    classes = ["0", "1/2", "1", "2", "4"]
    within = {}
    print(f"{'model':<30}" + "".join(f"{c:>18}" for c in classes))
    for m in sorted(table, key=lambda k: k):
        row = {}
        cells = []
        for c in classes:
            dif = [sum(v) / len(v) for i, v in table[m].items() if meta[i].get("answer_class") == c and meta[i].get("stratum") == "differs"]
            rest = [sum(v) / len(v) for i, v in table[m].items() if meta[i].get("answer_class") == c and meta[i].get("stratum") != "differs"]
            if dif and rest:
                row[c] = {"differs": round(sum(dif) / len(dif), 3), "n_differs": len(dif), "rest": round(sum(rest) / len(rest), 3), "n_rest": len(rest)}
                cells.append(f"{sum(dif)/len(dif):.2f}/{sum(rest)/len(rest):.2f} ({len(dif)}/{len(rest)})")
            else:
                cells.append("-")
        within[m] = row
        print(f"{m:<30}" + "".join(f"{c:>18}" for c in cells))
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_paired.json"
    path.write_text(json.dumps({"pairs": out, "differs_within_class": within}, indent=2), encoding="utf-8")
    print("wrote", path)


if __name__ == "__main__":
    main()
