"""Inspect task: Generation I type matchups as six-way multiple choice.

    inspect eval src/task.py -T chart=none -T show_types=false --model anthropic/claude-haiku-4-5-20251001

Conditions (PLAN.md):
  A  chart=none   show_types=false   recall: no chart, no typing
  D  chart=none   show_types=true    typing given, chart from memory
  B  chart=gen1   show_types=true    procedure: Gen 1 chart and typing given
  C  chart=modern show_types=true    modern chart given for Gen 1 typings;
                                     scored against the *provided* chart

The target is the Gen 1 multiplier except under chart=modern, where the
correct answer is what the provided chart says: the item then measures
whether the model follows the table in front of it or its prior.
"""

from __future__ import annotations

import csv
from pathlib import Path

from inspect_ai import Task, task
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.model import GenerateConfig
from inspect_ai.scorer import Metric, SampleScore, accuracy, choice, grouped, metric, stderr
from inspect_ai.solver import multiple_choice, system_message

from .key import MULTIPLIERS, PROCESSED, chart_table

SYSTEM = (
    "You are answering questions about type matchups in Pokemon Red and Blue "
    "(Generation I, the original 151 Pokemon, as typed in those games).\n\n"
    "Answer with the damage multiplier from type effectiveness alone: 0 (the move "
    "doesn't affect the defender), 1/2 (not very effective), 1 (normal damage), or "
    "2 (super effective). A defender with two types multiplies the two factors, so "
    "1/4 and 4 are possible.\n\n"
    "Ignore STAB, stats, move power, and any move-specific exceptions. Only the "
    "attacking type against the defender's type or types counts."
)

MAX_TOKENS = 1024  # reasoning is allowed; truncations are counted by parse_failures()

LETTERS = "ABCDEF"


def _display(identifier: str) -> str:
    special = {"nidoran-f": "Nidoran (female)", "nidoran-m": "Nidoran (male)", "mr-mime": "Mr. Mime", "farfetchd": "Farfetch'd"}
    return special.get(identifier, identifier.replace("-", " ").title())


def _prompt(row: dict[str, str], chart: str, show_types: bool) -> str:
    mon = _display(row["pokemon"])
    typing = row["def_type1"].title() + ("/" + row["def_type2"].title() if row["def_type2"] else "")
    parts = []
    if chart != "none":
        label = "Generation I" if chart == "gen1" else "current"
        parts.append(
            f"Use only the type chart below (the {label} chart), even where it disagrees with "
            f"what you remember about the games. Rows are the attacking type, columns the defending type.\n\n"
            f"{chart_table(past=(chart == 'gen1'))}\n"
        )
    defender = f"{mon} ({typing})" if show_types else mon
    parts.append(f"A {row['attack_type'].title()}-type move hits {defender}. What is the damage multiplier from type effectiveness alone?")
    return "\n".join(parts)


def load_items(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_samples(rows: list[dict[str, str]], chart: str, show_types: bool) -> list[Sample]:
    answer_field = "modern_multiplier" if chart == "modern" else "gen1_multiplier"
    samples = []
    for r in rows:
        target = LETTERS[MULTIPLIERS.index(r[answer_field])]
        samples.append(
            Sample(
                id=r["item_id"],
                input=_prompt(r, chart, show_types),
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
                    "show_types": show_types,
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


@task
def pokemon_gen1(
    chart: str = "none",
    show_types: bool = False,
    items: str = "items_s0_n400.csv",
    cot: bool = True,
    max_tokens: int = MAX_TOKENS,
) -> Task:
    if chart not in ("none", "gen1", "modern"):
        raise ValueError("chart must be none, gen1 or modern")
    rows = load_items(PROCESSED / items)
    return Task(
        dataset=MemoryDataset(build_samples(rows, chart, show_types), name=f"gen1_{chart}_{'types' if show_types else 'notypes'}"),
        solver=[system_message(SYSTEM), multiple_choice(shuffle=False, cot=cot)],
        scorer=choice(),
        metrics=[
            accuracy(),
            stderr(),
            parse_failures(),
            grouped(accuracy(), "stratum", all=False),
            grouped(accuracy(), "answer_class", all=False),
            grouped(accuracy(), "attack_type", all=False),
        ],
        config=GenerateConfig(max_tokens=max_tokens),
    )
