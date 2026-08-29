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
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from inspect_ai.log import EvalLog, list_eval_logs, read_eval_log

from .key import MULTIPLIERS, ROOT, efficacy, typings
from .models import BY_ID
from .stats import wilson

LETTERS = "ABCDEF"
CHANCE = 1 / len(MULTIPLIERS)
RESULTS = ROOT / "data" / "results"


def _letter_to_mult(letter: str | None) -> str | None:
    if not letter or letter not in LETTERS:
        return None
    return MULTIPLIERS[LETTERS.index(letter)]


def _rate(hits: int, n: int) -> float | None:
    return round(hits / n, 4) if n else None


_LENIENT_LETTER = re.compile(r"(?:answer is|answer:|correct answer is|option)\s*\(?([A-F])\)?", re.I)
_LENIENT_MULT = re.compile(r"(?:multiplier is|answer is|answer:)\s*\**\s*(0|1/4|1/2|1|2|4)\b")


def lenient_parse(text: str) -> str | None:
    """A second, forgiving read of a completion with no ANSWER line: the last
    'answer is X' or 'answer is <multiplier>' in the text. Reported beside the
    strict score, never in place of it (review point 6, REVIEW.md)."""
    m = list(_LENIENT_LETTER.finditer(text or ""))
    if m:
        return MULTIPLIERS[LETTERS.index(m[-1].group(1).upper())]
    m = list(_LENIENT_MULT.finditer(text or ""))
    return m[-1].group(1) if m else None


def _transposed_key(chart: str) -> dict[str, dict[str, str]]:
    """pokemon -> attack type -> the multiplier you get by reading every chart
    cell mirrored (defender attacking attacker). Equals the true key on
    symmetric cells, so a transposition is only detectable where they differ."""
    eff = efficacy(past=(chart != "modern"))
    out: dict[str, dict[str, str]] = {}
    labels = {0.0: "0", 0.25: "1/4", 0.5: "1/2", 1.0: "1", 2.0: "2", 4.0: "4"}
    for _, (name, ts) in typings().items():
        out[name] = {}
        for a in {k[0] for k in eff}:
            v = 1.0
            for t in ts:
                v *= eff[(t, a)] / 100
            out[name][a] = labels[v]
    return out


def summarize(log: EvalLog) -> dict:
    samples = log.samples or []
    args = log.eval.task_args or {}
    chart = args.get("chart", "none")
    mirror = _transposed_key(chart)
    transposed_misses = 0
    detectable_misses = 0  # misses on cells where the mirror differs from the key
    per_epoch: dict[int, list[int]] = defaultdict(list)
    parse_fail = 0
    by = {"stratum": defaultdict(list), "answer_class": defaultdict(list), "attack_type": defaultdict(list)}
    confusion: Counter = Counter()
    letters: Counter = Counter()
    targets: Counter = Counter()
    prior = Counter()  # chart=modern, differs cells only
    bucket_hits: list[float] = []
    steps: list[float] = []
    bucket_by_stratum: dict[str, list[float]] = defaultdict(list)
    lenient_hits = 0
    recovered = 0

    providers: Counter = Counter()
    provider_errors: Counter = Counter()
    for s in samples:
        sc = s.scores.get("choice") if s.scores else None
        if sc is None:
            continue
        for ev in s.events or []:
            if getattr(ev, "event", None) == "model" and getattr(ev, "call", None) and ev.call.response:
                r = ev.call.response
                prov = r.get("provider") or "?"
                providers[prov] += 1
                ch = (r.get("choices") or [{}])[0]
                if ch.get("error") or ch.get("finish_reason") == "error":
                    provider_errors[prov] += 1
        hit = 1 if sc.value == "C" else 0
        cl = s.scores.get("closeness")
        if cl is not None and isinstance(cl.value, dict):
            bucket_hits.append(float(cl.value["bucket"]))
            steps.append(float(cl.value["steps"]))
            bucket_by_stratum[(s.metadata or {}).get("stratum", "?")].append(float(cl.value["bucket"]))
        meta = s.metadata or {}
        # the closeness scorer records the chosen option's value; under shuffle the
        # letter no longer maps to a fixed multiplier, so prefer the value
        cl_ans = (s.scores.get("closeness").answer if s.scores and s.scores.get("closeness") else "") or ""
        predicted = cl_ans if cl_ans in MULTIPLIERS else (_letter_to_mult(sc.answer) if not args.get("shuffle") else None)
        target = meta.get("answer_class") or _letter_to_mult(s.target if isinstance(s.target, str) else s.target[0])
        per_epoch[s.epoch].append(hit)
        if predicted is None:
            parse_fail += 1
            lp = lenient_parse(s.output.completion if s.output else "")
            if lp is not None:
                recovered += 1
                if lp == target:
                    lenient_hits += 1
        elif hit:
            lenient_hits += 1
        letters[sc.answer or "(none)"] += 1
        targets[target] += 1
        confusion[(target, predicted or "(none)")] += 1
        by["stratum"][meta.get("stratum", "?")].append(hit)
        by["answer_class"][target].append(hit)
        by["attack_type"][meta.get("attack_type", "?")].append(hit)
        if not hit and predicted is not None:
            mirrored = mirror.get(meta.get("pokemon", ""), {}).get(meta.get("attack_type", ""))
            if mirrored is not None and mirrored != target:
                detectable_misses += 1
                if predicted == mirrored:
                    transposed_misses += 1
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
    n_items = n_total // max(len(per_epoch), 1)
    mean_acc = sum(accs) / len(accs) if accs else None
    ci = wilson(mean_acc, n_items) if mean_acc is not None else (None, None)
    majority = max(targets.values()) / sum(targets.values()) if targets else None

    def grouped(d):
        out = {}
        for k, v in sorted(d.items(), key=lambda kv: str(kv[0])):
            acc = _rate(sum(v), len(v))
            n_i = len(v) // max(len(per_epoch), 1)
            lo, hi = wilson(acc, n_i) if acc is not None else (None, None)
            out[k] = {"n": len(v), "n_items": n_i, "accuracy": acc, "ci95": [round(lo, 4), round(hi, 4)] if acc is not None else None}
        return out

    return {
        "log": Path(log.location).name,
        "model": log.eval.model,
        "condition": {"chart": chart, "show_types": args.get("show_types", False), "cot": args.get("cot", True), "items": args.get("items")},
        "n_samples": n_total,
        "epochs": len(per_epoch),
        "accuracy_mean": round(mean_acc, 4) if mean_acc is not None else None,
        "n_items": n_items,
        "accuracy_ci95": [round(ci[0], 4), round(ci[1], 4)] if mean_acc is not None else None,
        "accuracy_epoch_range": round(max(accs) - min(accs), 4) if accs else None,
        "accuracy_per_epoch": epoch_acc,
        "parse_failures": _rate(parse_fail, n_total),
        "lenient_accuracy": _rate(lenient_hits, n_total),
        "lenient_recovered": recovered,
        "misses": n_total - sum(sum(v) for v in per_epoch.values()),
        "misses_on_asymmetric_cells": detectable_misses,
        "transposed_misses": transposed_misses,
        "chart_format": args.get("chart_format", "table"),
        "shuffle": bool(args.get("shuffle", False)),
        "upstream_providers": dict(providers),
        "upstream_provider_errors": dict(provider_errors),
        "max_tokens": args.get("max_tokens"),
        "input_tokens_per_sample": round(sum(u.input_tokens for u in log.stats.model_usage.values()) / n_total) if n_total and log.stats and log.stats.model_usage else None,
        "output_tokens_per_sample": round(sum(u.output_tokens for u in log.stats.model_usage.values()) / n_total) if n_total and log.stats and log.stats.model_usage else None,
        "bucket_accuracy": round(sum(bucket_hits) / len(bucket_hits), 4) if bucket_hits else None,
        "mean_steps_off": round(sum(steps) / len(steps), 4) if steps else None,
        "bucket_by_stratum": {k: round(sum(v) / len(v), 4) for k, v in sorted(bucket_by_stratum.items())},
        "baseline_chance": round(CHANCE, 4),
        "baseline_majority": round(majority, 4) if majority else None,
        "by_stratum": grouped(by["stratum"]),
        "by_answer_class": grouped(by["answer_class"]),
        "by_attack_type": grouped(by["attack_type"]),
        "confusion": {f"{t}->{p}": c for (t, p), c in sorted(confusion.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1])))},
        "predicted_letters": {k: v for k, v in sorted(letters.items())},
        "differs_under_modern_chart": dict(prior) if chart == "modern" else None,
    }


def curve_rows(rows: list[dict]) -> list[dict]:
    """One line per (model, format) for the scaling curve: parameter counts
    from the registry, accuracy with its stderr and epoch range from the
    log. A model not in the registry gets no parameter count and is kept
    with a blank, never guessed."""
    out = []
    for r in rows:
        mid = r["model"].replace("openrouter/", "")
        m = BY_ID.get(mid)
        n = r["n_samples"] / max(r["epochs"], 1)
        acc = r["accuracy_mean"]
        out.append({
            "model": mid,
            "family": m.family if m else "",
            "params_total_b": m.params_total_b if m else "",
            "params_active_b": m.params_active_b if m else "",
            "quant": m.quant if m else "",
            "host_pinned": m.host if m else "",
            "hosts_seen": ";".join(f"{k}:{v}" for k, v in sorted(r["upstream_providers"].items())),
            "host_errors": sum(r["upstream_provider_errors"].values()),
            "format": r["chart_format"],
            "max_tokens": r["max_tokens"] or 1024,
            "items": int(n),
            "epochs": r["epochs"],
            "exact": acc,
            "exact_stderr": round((acc * (1 - acc) / n) ** 0.5, 4) if acc is not None and n else "",
            "exact_ci95_low": r["accuracy_ci95"][0] if r["accuracy_ci95"] else "",
            "exact_ci95_high": r["accuracy_ci95"][1] if r["accuracy_ci95"] else "",
            "exact_epoch_range": r["accuracy_epoch_range"],
            "bucket": r["bucket_accuracy"],
            "steps_off": r["mean_steps_off"],
            "parse_failures": r["parse_failures"],
            "lenient_accuracy": r["lenient_accuracy"],
            "transposed_misses": r["transposed_misses"],
            "misses": r["misses"],
            "quad": r["by_stratum"].get("quad", {}).get("accuracy", ""),
            "immune": r["by_stratum"].get("immune", {}).get("accuracy", ""),
            "differs": r["by_stratum"].get("differs", {}).get("accuracy", ""),
            "log": r["log"],
        })
    out.sort(key=lambda c: (c["format"], float(c["params_total_b"]) if c["params_total_b"] not in ("", None) and c["params_total_b"] == c["params_total_b"] else 1e9, c["model"]))
    return out


def table(rows: list[dict]) -> str:
    head = "| model | format | max_tok | n | epochs | acc | 95% CI | bucket | steps | range | parse fail | transposed / asym misses / misses | majority | immune | quad | dual | single | differs |"
    sep = "|" + "---|" * 19
    out = [head, sep]
    for r in rows:
        st = r["by_stratum"]
        cell = lambda k: (f"{st[k]['accuracy']:.2f}" if k in st and st[k]["accuracy"] is not None else "-")
        out.append(
            f"| {r['model'].replace('openrouter/', '')} | {r['chart_format']} | {r['max_tokens'] or 1024} | {r['n_samples']} | {r['epochs']} "
            f"| {r['accuracy_mean']:.3f} | {r['accuracy_ci95'][0]:.3f} to {r['accuracy_ci95'][1]:.3f} | {(r['bucket_accuracy'] if r['bucket_accuracy'] is not None else float('nan')):.3f} | {(r['mean_steps_off'] if r['mean_steps_off'] is not None else float('nan')):.2f} "
            f"| {r['accuracy_epoch_range']:.3f} | {r['parse_failures']:.2f} | {r['transposed_misses']} / {r['misses_on_asymmetric_cells']} / {r['misses']} | {r['baseline_majority']:.2f} "
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
    import csv as _csv
    curve = curve_rows(rows)
    curve_path = RESULTS / f"{stamp}_curve_{log_dir.name}.csv"
    with curve_path.open("w", newline="", encoding="utf-8") as fh:
        w = _csv.DictWriter(fh, fieldnames=list(curve[0].keys()))
        w.writeheader()
        w.writerows(curve)
    print(table(rows))
    print(f"\nchance {CHANCE:.3f}; majority is the share of the commonest answer class in that item set")
    for r in rows:
        print(f"\n{r['log']}")
        print("  by answer class:", {k: f"{v['accuracy']:.2f} (n={v['n']})" for k, v in r["by_answer_class"].items()})
        print("  predicted letters:", r["predicted_letters"])
        print("  upstream providers:", r["upstream_providers"], "| errors:", r["upstream_provider_errors"] or "none")
        if r["differs_under_modern_chart"]:
            print("  differs under modern chart:", r["differs_under_modern_chart"])
    print(f"\nwrote {out}\nwrote {curve_path}")
    print("\nscaling curve (exact, table format, by total params):")
    for c in curve:
        if c["format"] == "table" and c["params_total_b"] not in ("", None) and c["params_total_b"] == c["params_total_b"]:
            band = f" range {c['exact_epoch_range']:.3f}" if c["epochs"] > 1 else " (1 epoch)"
            print(f"  {c['params_total_b']:>7.1f}B  {c['model']:<40} {c['exact']:.3f} [{c['exact_ci95_low']:.3f}, {c['exact_ci95_high']:.3f}]{band}  active {c['params_active_b']}B {c['quant']}")


if __name__ == "__main__":
    main()
