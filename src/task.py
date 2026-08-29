"""Inspect task: Generation I type matchups as six-way multiple choice.

One registered condition (FINDINGS D-005): the full Gen 1 type chart and the
typing of all 151 Pokemon are in the system prompt, and the question names
only the attacking type and the defender. The model's job is to find the
defender in the list, read two chart cells, and multiply. Nothing is recalled.

    inspect eval src/task.py --model openrouter/anthropic/claude-haiku-4.5 --epochs 3

Two scorers, reported side by side and never blended:
  choice     exact letter match, pass/fail (primary)
  closeness  bucket match (the game's word: doesn't affect / not very / normal /
             super effective) and steps off on the log2 scale

The earlier recall conditions (-T chart=none, -T show_types=false or inline)
are kept as parameters for a later run with more budget; PLAN.md describes
them.
"""

from __future__ import annotations

import csv
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import (
    Metric,
    SampleScore,
    Score,
    Scorer,
    Target,
    accuracy,
    choice,
    mean,
    metric,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState, multiple_choice, system_message

try:  # imported as a package (pytest, python -m src.*) ...
    from .key import MULTIPLIERS, PROCESSED, chart_rows, chart_table, type_permutation, typings
    from .stats import wilson
except ImportError:  # ... or loaded as a standalone file by `inspect eval src/task.py`
    from key import MULTIPLIERS, PROCESSED, chart_rows, chart_table, type_permutation, typings  # type: ignore[no-redef]
    from stats import wilson  # type: ignore[no-redef]

LETTERS = "ABCDEF"
MAX_TOKENS = 1024  # reasoning is allowed; truncations are counted by parse_failures()

# The game's words. 1/4 and 1/2 both print "not very effective"; 2 and 4 both
# print "super effective". Immunity is its own word and its own rule.
BUCKET = {"0": "doesnt_affect", "1/4": "not_very", "1/2": "not_very", "1": "normal", "2": "super", "4": "super"}
LOG2 = {"1/4": -2, "1/2": -1, "1": 0, "2": 1, "4": 2}
IMMUNITY_DISTANCE = 3  # 0 is a rule, not a magnitude: never "close" to any multiplier
UNPARSED_DISTANCE = IMMUNITY_DISTANCE + 1

SYSTEM_RULES = (
    "You are answering questions about type matchups in Pokemon Red and Blue "
    "(Generation I, the original 151 Pokemon, as typed in those games).\n\n"
    "Answer with the damage multiplier from type effectiveness alone: 0 (the move "
    "doesn't affect the defender), 1/2 (not very effective), 1 (normal damage), or "
    "2 (super effective). A defender with two types multiplies the two factors, so "
    "1/4 and 4 are possible.\n\n"
    "Ignore STAB, stats, move power, and any move-specific exceptions. Only the "
    "attacking type against the defender's type or types counts."
)


def _display(identifier: str) -> str:
    special = {"nidoran-f": "Nidoran (female)", "nidoran-m": "Nidoran (male)", "mr-mime": "Mr. Mime", "farfetchd": "Farfetch'd"}
    return special.get(identifier, identifier.replace("-", " ").title())


def typing_list(relabel: dict[str, str] | None = None) -> str:
    """All 151 typings as a numbered list in dex order; identical for every
    item, so the prefix is cacheable where the provider supports it."""
    name = relabel or {}
    return "\n".join(
        f"{pid:>3}. {_display(name_)}: {'/'.join(name.get(t, t).title() for t in ts)}"
        for pid, (name_, ts) in sorted(typings().items())
    )


def _relabel(chart: str) -> dict[str, str] | None:
    """chart="permuted": the Gen 1 chart and typings shown under a seeded
    relabelling of the 15 type names (REVIEW3.md run 1). Nothing else changes."""
    return type_permutation(0) if chart == "permuted" else None


def system_prompt(chart: str, show_types: str | bool, chart_format: str = "table") -> str:
    parts = [SYSTEM_RULES]
    relabel = _relabel(chart)
    if chart != "none":
        label = {"gen1": "Generation I", "permuted": "relabelled"}.get(chart, "current")
        past = chart in ("gen1", "permuted")
        if chart_format == "table":
            body = f"Rows are the attacking type, columns the defending type.\n\n{chart_table(past=past, relabel=relabel)}"
        elif chart_format == "rows":
            body = f"Each line is one attacking type, followed by its multiplier against every defending type.\n\n{chart_rows(past=past, relabel=relabel)}"
        else:
            raise ValueError("chart_format must be table or rows")
        parts.append(
            f"Use only the type chart below (the {label} chart), even where it disagrees with "
            f"what you remember about the games. {body}"
        )
    if show_types == "list":
        parts.append("The typing of every Pokemon, as in Red and Blue:\n\n" + typing_list(relabel))
    return "\n\n".join(parts)


def _question(row: dict[str, str], show_types: str | bool, relabel: dict[str, str] | None = None) -> str:
    mon = _display(row["pokemon"])
    name = relabel or {}
    if show_types is True or show_types == "inline":
        typing = name.get(row["def_type1"], row["def_type1"]).title() + ("/" + name.get(row["def_type2"], row["def_type2"]).title() if row["def_type2"] else "")
        mon = f"{mon} ({typing})"
    attack = name.get(row["attack_type"], row["attack_type"])
    return f"A {attack.title()}-type move hits {mon}. What is the damage multiplier from type effectiveness alone?"


def load_items(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_samples(rows: list[dict[str, str]], chart: str, show_types: str | bool) -> list[Sample]:
    answer_field = "modern_multiplier" if chart == "modern" else "gen1_multiplier"
    relabel = _relabel(chart)
    samples = []
    for r in rows:
        target = LETTERS[MULTIPLIERS.index(r[answer_field])]
        samples.append(
            Sample(
                id=r["item_id"],
                input=_question(r, show_types, relabel),
                choices=list(MULTIPLIERS),
                target=target,
                metadata={
                    "stratum": r["stratum"],
                    "attack_type": r["attack_type"],
                    "pokemon": r["pokemon"],
                    "def_types": r["def_type1"] + ("/" + r["def_type2"] if r["def_type2"] else ""),
                    "gen1_multiplier": r["gen1_multiplier"],
                    "modern_multiplier": r["modern_multiplier"],
                    "answer_class": r[answer_field],
                    "chart": chart,
                    "show_types": str(show_types),
                },
            )
        )
    return samples


def _ci(which: int) -> Metric:
    """95% Wilson bound on accuracy with n = number of distinct items (epoch
    repeats are not independent trials). Reads the reduced per-item scores,
    which is what Inspect hands a metric after epoch reduction."""

    def m(scores: list[SampleScore]) -> float:
        vals = []
        for s in scores:
            v = s.score.value
            if isinstance(v, (int, float)):
                vals.append(float(v))
            elif v == "C":
                vals.append(1.0)
            elif v == "I":
                vals.append(0.0)
        if not vals:
            return float("nan")
        return wilson(sum(vals) / len(vals), len(vals))[which]

    return m


@metric
def ci95_low() -> Metric:
    return _ci(0)


@metric
def ci95_high() -> Metric:
    return _ci(1)


@metric
def parse_failures() -> Metric:
    """Share of samples where no ANSWER letter could be parsed (truncation,
    refusal, wrong format). choice() scores these as incorrect; this keeps
    them visible as their own number."""

    def m(scores: list[SampleScore]) -> float:
        if not scores:
            return 0.0
        return sum(1 for s in scores if not s.score.answer) / len(scores)

    return m


def closeness_of(predicted: str | None, target: str) -> dict[str, float]:
    """bucket: 1 if the game would print the same word; steps: distance on the
    log2 scale, with immunity IMMUNITY_DISTANCE from everything else and an
    unparsed answer scored as the farthest miss."""
    if predicted is None or predicted not in MULTIPLIERS:
        return {"bucket": 0.0, "steps": float(UNPARSED_DISTANCE)}
    bucket = 1.0 if BUCKET[predicted] == BUCKET[target] else 0.0
    if predicted == target:
        steps = 0.0
    elif "0" in (predicted, target):
        steps = float(IMMUNITY_DISTANCE)
    else:
        steps = float(abs(LOG2[predicted] - LOG2[target]))
    return {"bucket": bucket, "steps": steps}


@scorer(name="choice", metrics=[accuracy(), ci95_low(), ci95_high(), stderr(), parse_failures()])
def exact() -> Scorer:
    """Primary scorer: Inspect's choice() (exact ANSWER letter match). The log
    carries the headline (accuracy, its 95% Wilson interval over items,
    stderr, and the single-epoch parse-failure metric); every grouping (by
    stratum, answer class, attack type) lives in analyze, with n. Fewer
    in-log metrics also means the viewer's task-list column is accuracy."""
    return choice()


@scorer(metrics=[mean()])
def parsed() -> Scorer:
    """1 if an ANSWER letter was parsed, else 0. A numeric value, so Inspect's
    epoch reduction averages it correctly; the parse_failures metric on the
    exact scorer does not survive reduction (FINDINGS D-011) and is kept only
    for one-epoch runs."""

    async def score(state: TaskState, target: Target) -> Score:
        answered = any(c.correct for c in state.choices)
        return Score(value=1.0 if answered else 0.0, answer="parsed" if answered else "")

    return score


@scorer(metrics=[{"bucket": [mean(), stderr()], "steps": [mean()]}])
def closeness() -> Scorer:
    """Secondary scorer. Reads the letter the multiple_choice solver marked
    as answered (the same thing choice() reads), maps it to a multiplier, and
    reports bucket match and steps off. Never averaged with exact accuracy."""

    async def score(state: TaskState, target: Target) -> Score:
        # read the chosen option's value, not its position: correct under shuffle
        answered = None
        for c in state.choices:
            if c.correct:
                answered = c.value
                break
        t = state.metadata.get("answer_class") if state.metadata else None
        if t is None:
            t = MULTIPLIERS[LETTERS.index(target.text)]
        val = closeness_of(answered, t)
        return Score(
            value=val,
            answer=answered or "",
            explanation=f"predicted {answered} vs {t}: bucket {val['bucket']:.0f}, {val['steps']:.0f} steps",
        )

    return score


@task
def pokemon_gen1(
    chart: str = "gen1",
    show_types: str | bool = "list",
    items: str = "items_s0_n400.csv",
    cot: bool = True,
    max_tokens: int = MAX_TOKENS,
    chart_format: str = "table",
    shuffle: bool = False,
) -> Task:
    if chart not in ("none", "gen1", "modern"):
        raise ValueError("chart must be none, gen1 or modern")
    if show_types not in ("list", "inline", True, False):
        raise ValueError("show_types must be list, inline, true or false")
    if chart_format not in ("table", "rows"):
        raise ValueError("chart_format must be table or rows")
    rows = load_items(PROCESSED / items)
    return Task(
        dataset=MemoryDataset(build_samples(rows, chart, show_types), name=f"gen1_{chart}_{show_types}_{chart_format}{'_shuffled' if shuffle else ''}"),
        solver=[system_message(system_prompt(chart, show_types, chart_format)), multiple_choice(shuffle=shuffle, cot=cot)],
        scorer=[exact(), closeness(), parsed()],
        config=GenerateConfig(max_tokens=max_tokens),
    )
