"""What it costs to run this task at volume, per model.

The paper measures accuracy. This measures the thing a deployment engineer
actually decides on: cost per *correct* answer at a given daily volume. A cheap
wrong answer is worth nothing, so cost per call is the wrong metric.

Token counts are measured, not assumed: mean input and output tokens per call
from the pinned table-format runs. Prices are per million tokens and must be
supplied; the defaults below are OpenRouter list prices verified 2026-08-29 for
the two models where it was checked, and clearly-labelled representative bands
elsewhere. Prices move; re-check before quoting.

    python -m src.economics --volume 100000
"""

from __future__ import annotations

import argparse

# model -> (mean input tokens, mean output tokens, exact accuracy)
# measured from logs/pinned and logs/qwen_dense, table format, this repository
MEASURED = {
    "gpt-5-nano (ceiling)":        (2750, 917, 0.954),
    "qwen3-14b (thinking)":        (2767, 731, 0.896),
    "qwen3-8b (thinking)":         (2766, 1154, 0.850),
    "qwen3-32b (thinking)":        (2767, 618, 0.828),
    "qwen3-235b-a22b (instruct)":  (2750, 167, 0.764),
    "qwen3-30b-a3b (instruct)":    (2750, 167, 0.642),
    "gemma-3-27b":                 (2732, 70, 0.617),
    "gemma-3-12b":                 (2728, 63, 0.507),
}

# $ per million tokens (input, output).
# `verified` = read from the provider's API on 2026-08-29.
# `band` = representative published range for that class, not a quote.
PRICES = {
    "qwen3-8b (thinking)":         (0.117, 0.455, "verified"),
    "qwen3-14b (thinking)":        (0.120, 0.240, "verified"),
    "qwen3-32b (thinking)":        (0.150, 0.600, "band"),
    "qwen3-30b-a3b (instruct)":    (0.100, 0.300, "band"),
    "qwen3-235b-a22b (instruct)":  (0.200, 0.800, "band"),
    "gemma-3-12b":                 (0.050, 0.100, "band"),
    "gemma-3-27b":                 (0.100, 0.200, "band"),
    "gpt-5-nano (ceiling)":        (0.050, 0.400, "band"),
    "a frontier model":            (3.000, 15.000, "band"),
}
# the frontier row has no measured accuracy here; assume it matches the ceiling
FRONTIER_ACCURACY = 0.954
FRONTIER_OUTPUT = 700  # reasoning models on this task ran 618-1154; midpoint


def rows(volume: int, cache_discount: float):
    out = []
    items = dict(MEASURED)
    items["a frontier model"] = (2750, FRONTIER_OUTPUT, FRONTIER_ACCURACY)
    for name, (tin, tout, acc) in items.items():
        pin, pout, src = PRICES[name]
        billed_in = tin * (1 - cache_discount)
        per_call = (billed_in * pin + tout * pout) / 1e6
        per_correct = per_call / acc
        out.append({
            "model": name, "acc": acc, "in": tin, "out": tout, "price": src,
            "per_call": per_call, "per_correct": per_correct,
            "daily": per_call * volume, "annual": per_call * volume * 365,
            "annual_correct": per_correct * volume * 365,
        })
    return sorted(out, key=lambda r: r["per_correct"])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--volume", type=int, default=100_000, help="lookups per day")
    ap.add_argument("--cache", type=float, default=0.0, help="share of input tokens served from cache (0 to 1)")
    ap.add_argument("--min-accuracy", type=float, default=0.0,
                    help="accuracy floor. cost per correct answer alone is not a decision rule: "
                         "a cheap model at 0.51 is undeployable no matter what it costs")
    a = ap.parse_args()
    print(f"\n{a.volume:,} lookups/day, prompt cache discount {a.cache:.0%}\n")
    print(f"{'model':<28}{'acc':>6}{'out tok':>9}{'$/1k calls':>12}{'$/1k correct':>14}{'$/day':>10}{'$/year':>13}  price")
    eligible = [r for r in rows(a.volume, a.cache) if r["acc"] >= a.min_accuracy]
    for r in rows(a.volume, a.cache):
        if r["acc"] < a.min_accuracy:
            continue
        print(f"{r['model']:<28}{r['acc']:>6.3f}{r['out']:>9}{r['per_call']*1000:>12.2f}"
              f"{r['per_correct']*1000:>14.2f}{r['daily']:>10.0f}{r['annual']:>13,.0f}  {r['price']}")
    best = eligible[0]
    frontier = [r for r in eligible if r["model"] == "a frontier model"][0]
    print(f"\ncheapest per correct answer: {best['model']} at ${best['per_correct']*1000:.2f} per 1,000 correct")
    print(f"a frontier model:            ${frontier['per_correct']*1000:.2f} per 1,000 correct"
          f"  ({frontier['per_correct']/best['per_correct']:.0f}x)")
    print(f"annual difference at this volume: ${frontier['annual'] - best['annual']:,.0f}\n")
    print("Caveats: prices marked `band` are representative, not quotes. Accuracy is on this")
    print("task only. The frontier row assumes ceiling-model accuracy and midpoint output length.")
    print("Cost per correct answer is not a deployment rule on its own: set an accuracy floor from")
    print("what a wrong answer costs, then take the cheapest model that clears it.")


if __name__ == "__main__":
    main()
