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
    grouped,
    mean,
    metric,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState, multiple_choice, system_message

from .key import MULTIPLIERS, PROCESSED, chart_table, typings

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


def typing_list() -> str:
    """All 151 typings as a numbered list in dex order; identical for every
    item, so the prefix is cacheable where the provider supports it."""
    return "\n".join(
        f"{pid:>3}. {_display(name)}: {'/'.join(t.title() for t in ts)}"
        for pid, (name, ts) in sorted(typings().items())
    )


def system_prompt(chart: str, show_types: str | bool) -> str:
    parts = [SYSTEM_RULES]
    if chart != "none":
        label = "Generation I" if chart == "gen1" else "current"
        parts.append(
            f"Use only the type chart below (the {label} chart), even where it disagrees with "
            f"what you remember about the games. Rows are the attacking type, columns the defending type.\n\n"
            f"{chart_table(past=(chart == 'gen1'))}"
        )
    if show_types == "list":
        parts.append("The typing of every Pokemon, as in Red and Blue:\n\n" + typing_list())
    return "\n\n".join(parts)


def _question(row: dict[str, str], show_types: str | bool) -> str:
    mon = _display(row["pokemon"])
    if show_types is True or show_types == "inline":
        typing = row["def_type1"].title() + ("/" + row["def_type2"].title() if row["def_type2"] else "")
        mon = f"{mon} ({typing})"
    return f"A {row['attack_type'].title()}-type move hits {mon}. What is the damage multiplier from type effectiveness alone?"


def load_items(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_samples(rows: list[dict[str, str]], chart: str, show_types: str | bool) -> list[Sample]:
    answer_field = "modern_multiplier" if chart == "modern" else "gen1_multiplier"
    samples = []
    for r in rows:
        target = LETTERS[MULTIPLIERS.index(r[answer_field])]
        samples.append(
            Sample(
                id=r["item_id"],
                input=_question(r, show_types),
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


@scorer(
    name="choice",
    metrics=[
        accuracy(),
        stderr(),
        parse_failures(),
        grouped(accuracy(), "stratum", all=False),
        grouped(accuracy(), "answer_class", all=False),
        grouped(accuracy(), "attack_type", all=False),
    ],
)
def exact() -> Scorer:
    """Primary scorer: Inspect's choice() (exact ANSWER letter match) with this
    task's metrics attached to it, so the metrics list is per scorer and the
    closeness scorer keeps its own."""
    return choice()


@scorer(metrics=[{"bucket": [mean(), stderr()], "steps": [mean()]}])
def closeness() -> Scorer:
    """Secondary scorer. Reads the letter the multiple_choice solver marked
    as answered (the same thing choice() reads), maps it to a multiplier, and
    reports bucket match and steps off. Never averaged with exact accuracy."""

    async def score(state: TaskState, target: Target) -> Score:
        answered = None
        for i, c in enumerate(state.choices):
            if c.correct:
                answered = MULTIPLIERS[i]
                break
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
) -> Task:
    if chart not in ("none", "gen1", "modern"):
        raise ValueError("chart must be none, gen1 or modern")
    if show_types not in ("list", "inline", True, False):
        raise ValueError("show_types must be list, inline, true or false")
    rows = load_items(PROCESSED / items)
    return Task(
        dataset=MemoryDataset(build_samples(rows, chart, show_types), name=f"gen1_{chart}_{show_types}"),
        solver=[system_message(system_prompt(chart, show_types)), multiple_choice(shuffle=False, cot=cot)],
        scorer=[exact(), closeness()],
        config=GenerateConfig(max_tokens=max_tokens),
    )
