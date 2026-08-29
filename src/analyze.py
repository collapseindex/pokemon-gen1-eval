"""Read Inspect logs and write one summary; nothing in the report is typed.

    python -m src.analyze --log-dir logs/dev

For every .eval log in the directory: the run's condition and model, accuracy
per epoch with the mean and the epoch range (the noise band P1 is scored on),
parse failures, the two baselines (chance, majority class of that item set),
accuracy by stratum / answer class / attack type with n, the confusion matrix
(target x predicted, in multipliers), the predicted-letter distribution
(position bias), and under chart=modern the prior-following rate on the
`differs` cells. Writes data/results/YYYYMMDD_HHMMSS_analyze_<logdir>.json and
prints a markdown table.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from .key import MULTIPLIERS, ROOT

LETTERS = "ABCDEF"
CHANCE = 1 / len(MULTIPLIERS)
RESULTS = ROOT / "data" / "results"


def _letter_to_mult(letter: str | None) -> str | None:
    if not letter or letter not in LETTERS:
        return None
    return MULTIPLIERS[LETTERS.index(letter)]


def _rate(hits: int, n: int) -> float | None:
    return round(hits / n, 4) if n else None


def summarize(log: EvalLog) -> dict:
    samples = log.samples or []
    args = log.eval.task_args or {}
    chart = args.get("chart", "none")
    per_epoch: dict[int, list[int]] = defaultdict(list)
    parse_fail = 0
    by = {"stratum": defaultdict(list), "answer_class": defaultdict(list), "attack_type": defaultdict(list)}
    confusion: Counter = Counter()
    letters: Counter = Counter()
    targets: Counter = Counter()
    prior = Counter()  # chart=modern, differs cells only

    for s in samples:
        sc = s.scores.get("choice") if s.scores else None
        if sc is None:
            continue
        hit = 1 if sc.value == "C" else 0
        predicted = _letter_to_mult(sc.answer)
        target = _letter_to_mult(s.target if isinstance(s.target, str) else s.target[0])
        meta = s.metadata or {}
        per_epoch[s.epoch].append(hit)
        if predicted is None:
            parse_fail += 1
        letters[sc.answer or "(none)"] += 1
        targets[target] += 1
        confusion[(target, predicted or "(none)")] += 1
        by["stratum"][meta.get("stratum", "?")].append(hit)
        by["answer_class"][target].append(hit)
        by["attack_type"][meta.get("attack_type", "?")].append(hit)
        if chart == "modern" and meta.get("stratum") == "differs":
            if predicted == meta.get("modern_multiplier"):
                prior["followed_table"] += 1
            elif predicted == meta.get("gen1_multiplier"):
                prior["followed_prior"] += 1
            else:
                prior["neither"] += 1

    n_total = sum(len(v) for v in per_epoch.values())
    epoch_acc = {e: _rate(sum(v), len(v)) for e, v in sorted(per_epoch.items())}
    accs = [a for a in epoch_acc.values() if a is not None]
    majority = max(targets.values()) / sum(targets.values()) if targets else None

    def grouped(d):
        return {k: {"n": len(v), "accuracy": _rate(sum(v), len(v))} for k, v in sorted(d.items(), key=lambda kv: str(kv[0]))}

    return {
        "log": Path(log.location).name,
        "model": log.eval.model,
        "condition": {"chart": chart, "show_types": args.get("show_types", False), "cot": args.get("cot", True), "items": args.get("items")},
        "n_samples": n_total,
        "epochs": len(per_epoch),
        "accuracy_mean": round(sum(accs) / len(accs), 4) if accs else None,
        "accuracy_epoch_range": round(max(accs) - min(accs), 4) if accs else None,
        "accuracy_per_epoch": epoch_acc,
        "parse_failures": _rate(parse_fail, n_total),
        "baseline_chance": round(CHANCE, 4),
        "baseline_majority": round(majority, 4) if majority else None,
        "by_stratum": grouped(by["stratum"]),
        "by_answer_class": grouped(by["answer_class"]),
        "by_attack_type": grouped(by["attack_type"]),
        "confusion": {f"{t}->{p}": c for (t, p), c in sorted(confusion.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1])))},
        "predicted_letters": {k: v for k, v in sorted(letters.items())},
        "differs_under_modern_chart": dict(prior) if chart == "modern" else None,
    }


def table(rows: list[dict]) -> str:
    head = "| model | chart | types | cot | n | epochs | acc | range | parse fail | majority | immune | quad | dual | single | differs |"
    sep = "|" + "---|" * 15
    out = [head, sep]
    for r in rows:
        st = r["by_stratum"]
        cell = lambda k: (f"{st[k]['accuracy']:.2f}" if k in st and st[k]["accuracy"] is not None else "-")
        out.append(
            f"| {r['model']} | {r['condition']['chart']} | {r['condition']['show_types']} | {r['condition']['cot']} | {r['n_samples']} | {r['epochs']} "
            f"| {r['accuracy_mean']:.3f} | {r['accuracy_epoch_range']:.3f} | {r['parse_failures']:.2f} | {r['baseline_majority']:.2f} "
            f"| {cell('immune')} | {cell('quad')} | {cell('dual')} | {cell('single')} | {cell('differs')} |"
        )
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default="logs/dev")
    a = ap.parse_args()
    log_dir = (ROOT / a.log_dir) if not Path(a.log_dir).is_absolute() else Path(a.log_dir)
    rows = [summarize(read_eval_log(info.name)) for info in list_eval_logs(str(log_dir))]
    rows = [r for r in rows if r["n_samples"]]
    if not rows:
        print(f"no logs with samples in {log_dir}")
        return
    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = RESULTS / f"{stamp}_analyze_{log_dir.name}.json"
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print(table(rows))
    print(f"\nchance {CHANCE:.3f}; majority is the share of the commonest answer class in that item set")
    for r in rows:
        print(f"\n{r['log']}")
        print("  by answer class:", {k: f"{v['accuracy']:.2f} (n={v['n']})" for k, v in r["by_answer_class"].items()})
        print("  predicted letters:", r["predicted_letters"])
        if r["differs_under_modern_chart"]:
            print("  differs under modern chart:", r["differs_under_modern_chart"])
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
