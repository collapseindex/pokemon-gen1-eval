"""Two analyses the second review asked for, both from the pinned table logs.

1. Position in the list. Accuracy against where the defender sits in the
   151-line typing list (dex number, five bins), per model. Lost-in-the-middle
   predicts worse accuracy for mid-list defenders.

2. What a "lookup" miss is. For every miss filed as `lookup` by
   src.error_analysis, read the reasoning for the typing it states for the
   named Pokemon (the type words within a window after the first mention of
   the name) and compare with the true typing. Three outcomes:
     wrong-line    stated typing does not match the true typing (found the
                   wrong Pokemon, or recalled a typing instead of reading one)
     right-line    stated typing matches; the miss is in the chart read
     unstated      no typing statement found in the window
   This is an automated first cut; a hand check of a sample is reported in
   the ledger beside it.

    python -m src.lookup_analysis --log-dir logs/pinned
Writes data/results/<stamp>_lookup_<logdir>.json and prints both tables.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from inspect_ai.log import list_eval_logs, read_eval_log

from .analyze import _letter_to_mult, _transposed_key
from .error_analysis import classify
from .key import ROOT, gen_types, typings

RESULTS = ROOT / "data" / "results"
TYPES = list(gen_types().values())
TYPE_RE = re.compile(r"\b(" + "|".join(TYPES) + r")\b", re.I)
BINS = [(1, 30), (31, 60), (61, 90), (91, 120), (121, 151)]
WINDOW = 220


def display(identifier: str) -> str:
    special = {"nidoran-f": "nidoran", "nidoran-m": "nidoran", "mr-mime": "mr. mime", "farfetchd": "farfetch'd"}
    return special.get(identifier, identifier.replace("-", " "))


def stated_typing(text: str, pokemon: str, attack_type: str | None = None, true_types: set[str] | None = None) -> set[str] | None:
    """Type words in a window after the first mention of the Pokemon's name.
    The attacking type is dropped from the window unless it is genuinely one of
    the defender's types, since the reasoning names it beside the defender
    ("Ice attacks against Electric-type") and it would otherwise read as a
    stated typing (hand check, 2026-08-29)."""
    low = text.lower()
    name = display(pokemon).lower()
    i = low.find(name)
    if i < 0:
        return None
    window = low[i + len(name): i + len(name) + WINDOW]
    found = []
    for m in TYPE_RE.finditer(window):
        t = m.group(1).lower()
        if attack_type and t == attack_type.lower() and not (true_types and t in true_types):
            continue
        # "normal damage" / "normal effectiveness" is the multiplier's word, not a type
        if t == "normal" and re.match(r"\s*(damage|effectiveness|multiplier)", window[m.end():]):
            continue
        if t not in found:
            found.append(t)
        if len(found) == 2:
            break
    return set(found) if found else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log-dir", default="logs/pinned")
    a = ap.parse_args()
    dex = {name: pid for pid, (name, _) in typings().items()}
    true_types = {name: set(ts) for _, (name, ts) in typings().items()}
    mirror = _transposed_key("gen1")
    out = []
    for info in list_eval_logs(str(ROOT / a.log_dir)):
        log = read_eval_log(info.name)
        args = log.eval.task_args or {}
        if log.status != "success" or args.get("chart_format", "table") != "table" or args.get("chart", "gen1") != "gen1":
            continue
        pos_hits: dict[tuple, list[int]] = defaultdict(list)
        lookup = Counter()
        n_lookup = 0
        for s in log.samples or []:
            sc = s.scores.get("choice") if s.scores else None
            if sc is None:
                continue
            meta = s.metadata or {}
            pid = dex[meta["pokemon"]]
            b = next(bb for bb in BINS if bb[0] <= pid <= bb[1])
            hit = sc.value == "C"
            pos_hits[b].append(1 if hit else 0)
            target = meta.get("answer_class") or _letter_to_mult(s.target if isinstance(s.target, str) else s.target[0])
            cl = s.scores.get("closeness")
            predicted = (cl.answer if cl and cl.answer else None) or _letter_to_mult(sc.answer)
            m = mirror.get(meta["pokemon"], {}).get(meta["attack_type"])
            if classify(target, predicted, m) == "lookup":
                n_lookup += 1
                st = stated_typing(s.output.completion if s.output else "", meta["pokemon"], meta["attack_type"], true_types[meta["pokemon"]])
                if st is None:
                    lookup["unstated"] += 1
                elif st == true_types[meta["pokemon"]]:
                    lookup["right-line"] += 1
                else:
                    lookup["wrong-line"] += 1
        out.append({
            "model": log.eval.model.replace("openrouter/", ""),
            "epochs": log.eval.config.epochs or 1,
            "position_accuracy": {f"{lo}-{hi}": {"n": len(v), "accuracy": round(sum(v) / len(v), 3)} for (lo, hi), v in sorted(pos_hits.items())},
            "lookup_misses": n_lookup,
            "lookup_split": {k: lookup.get(k, 0) for k in ("wrong-line", "right-line", "unstated")},
            "lookup_split_share": {k: round(lookup.get(k, 0) / max(n_lookup, 1), 3) for k in ("wrong-line", "right-line", "unstated")},
            "log": Path(log.location).name,
        })
    out.sort(key=lambda r: r["model"])
    RESULTS.mkdir(parents=True, exist_ok=True)
    path = RESULTS / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_lookup_{Path(a.log_dir).name}.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"{'model':<34}" + "".join(f"{lo}-{hi}".rjust(9) for lo, hi in BINS) + "   lookup  wrong-line right-line unstated")
    for r in out:
        row = f"{r['model'].split('/')[-1]:<34}" + "".join(f"{r['position_accuracy'][f'{lo}-{hi}']['accuracy']:>9.3f}" for lo, hi in BINS)
        sp = r["lookup_split_share"]
        print(row + f"   {r['lookup_misses']:>6}  {sp['wrong-line']:>9.2f} {sp['right-line']:>10.2f} {sp['unstated']:>8.2f}")
    print("wrote", path)


if __name__ == "__main__":
    main()
