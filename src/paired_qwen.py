"""Score REVIEW4.md's Y1 to Y4 with paired tests over items (see src.paired).

    python -m src.paired_qwen > data/results/<stamp>_paired_qwen.json
Prints a JSON object with the four verdict strings the paper quotes.
"""

from __future__ import annotations

import csv
import glob
import json

from .key import ROOT
from .paired import boot, mcnemar, per_item


def main() -> None:
    pinned, _ = per_item("logs/pinned", {"chart_format": ("table", "table"), "chart": ("gen1", "gen1")})
    dense, _ = per_item("logs/qwen_dense", {"chart_format": ("table", "table"), "chart": ("gen1", "gen1")})
    q8, q14, q32 = dense["qwen3-8b"], dense["qwen3-14b"], pinned["qwen3-32b"]
    moe, l8 = pinned["qwen3-30b-a3b-instruct-2507"], pinned["llama-3.1-8b-instruct"]
    acc = lambda h: sum(sum(v) / len(v) for v in h.values()) / len(h)
    rng = {}
    for pat in ("*_curve_pinned.csv", "*_curve_qwen_dense.csv"):
        for r in csv.DictReader(open(sorted(glob.glob(str(ROOT / "data/results" / pat)))[-1], newline="", encoding="utf-8")):
            if r["format"] == "table":
                rng[r["model"].split("/")[-1]] = float(r["exact_epoch_range"])
    d1, lo1, hi1 = boot(q8, q14)
    d2, lo2, hi2 = boot(q14, q32)
    mono = acc(q8) < acc(q14) < acc(q32) and lo1 > 0 and lo2 > 0
    y1 = (r"\textsc{held}" if mono else r"\textsc{failed}") + f": $8$B $\\to$ $14$B ${d1:+.3f}$ $[{lo1:+.3f}, {hi1:+.3f}]$, $14$B $\\to$ $32$B ${d2:+.3f}$ $[{lo2:+.3f}, {hi2:+.3f}]$"
    d, lo, hi = boot(q14, moe)
    y2 = f"${d:+.3f}$ $[{lo:+.3f}, {hi:+.3f}]$ below it" if d < 0 else f"${d:+.3f}$ $[{lo:+.3f}, {hi:+.3f}]$ above it"
    d3, lo3, hi3 = boot(l8, q8)
    x, y, p = mcnemar(l8, q8)
    y3 = f"${d3:+.3f}$ $[{lo3:+.3f}, {hi3:+.3f}]$ against a range sum of ${rng['llama-3.1-8b-instruct'] + rng['qwen3-8b']:.3f}$"
    y4 = f"{acc(q8):.3f} and {acc(q14):.3f}"
    out = {"Y1": y1, "Y2": y2, "Y3": y3, "Y4": y4, "acc": {"qwen3-8b": round(acc(q8), 4), "qwen3-14b": round(acc(q14), 4), "qwen3-32b": round(acc(q32), 4), "moe": round(acc(moe), 4), "llama8b": round(acc(l8), 4)},
           "mcnemar_llama8b_vs_qwen8b": [x, y, p]}
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
