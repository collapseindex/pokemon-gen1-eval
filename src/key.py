"""Build the Generation I matchup answer key from the frozen PokeAPI CSVs.

Every number downstream comes from here. The key is derived, never typed:
the Gen 1 type chart is the modern chart with the ``type_efficacy_past.csv``
rows whose ``generation_id >= 1`` applied on top, and the Gen 1 typings are
the modern typings with ``pokemon_types_past.csv`` applied the same way.
PokeAPI's semantics for a past row: it holds *through* the generation named.

Run ``python -m src.key`` to write ``data/processed/gen1_key.csv`` and print
the known-answer cells for hand verification.
"""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

GENERATION = 1
DEX_MAX = 151
FACTOR_SCALE = 100  # PokeAPI stores 0 / 50 / 100 / 200

# The six multipliers a two-type defender can produce. Fixed option order for
# every item; the letter for each is its index in this list.
MULTIPLIERS = ["0", "1/4", "1/2", "1", "2", "4"]
MULT_VALUE = {"0": 0.0, "1/4": 0.25, "1/2": 0.5, "1": 1.0, "2": 2.0, "4": 4.0}


@dataclass(frozen=True)
class Cell:
    attack_type: str
    pokemon_id: int
    pokemon: str
    def_type1: str
    def_type2: str  # "" when single-typed
    gen1_multiplier: str
    modern_multiplier: str  # modern chart applied to the Gen 1 typing

    @property
    def dual(self) -> bool:
        return bool(self.def_type2)

    @property
    def differs(self) -> bool:
        return self.gen1_multiplier != self.modern_multiplier

    @property
    def def_types(self) -> str:
        return f"{self.def_type1}/{self.def_type2}" if self.def_type2 else self.def_type1


def _read(name: str) -> list[dict[str, str]]:
    with (RAW / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def gen_types() -> dict[int, str]:
    """Type id -> identifier for every type that existed in GENERATION."""
    return {
        int(r["id"]): r["identifier"]
        for r in _read("types.csv")
        if int(r["generation_id"]) <= GENERATION
    }



def efficacy(past: bool) -> dict[tuple[str, str], int]:
    """(attack, target) -> factor (0/50/100/200). ``past=True`` applies the
    Gen 1 overrides; ``past=False`` is the modern chart on Gen 1 types."""
    types = gen_types()
    chart: dict[tuple[str, str], int] = {}
    for r in _read("type_efficacy.csv"):
        a, t = int(r["damage_type_id"]), int(r["target_type_id"])
        if a in types and t in types:
            chart[(types[a], types[t])] = int(r["damage_factor"])
    if past:
        for r in _read("type_efficacy_past.csv"):
            if int(r["generation_id"]) >= GENERATION:
                a, t = int(r["damage_type_id"]), int(r["target_type_id"])
                if a in types and t in types:
                    chart[(types[a], types[t])] = int(r["damage_factor"])
    assert len(chart) == len(types) ** 2, "chart is not square"
    return chart


def typings() -> dict[int, tuple[str, list[str]]]:
    """pokemon_id -> (identifier, [types in slot order]) for the first DEX_MAX,
    as typed in GENERATION."""
    types = gen_types()
    names = {int(r["id"]): r["identifier"] for r in _read("pokemon.csv") if int(r["id"]) <= DEX_MAX}
    current: dict[int, dict[int, str]] = {}
    for r in _read("pokemon_types.csv"):
        pid = int(r["pokemon_id"])
        if pid in names:
            current.setdefault(pid, {})[int(r["slot"])] = types.get(int(r["type_id"]), r["type_id"])
    past_rows = [r for r in _read("pokemon_types_past.csv") if int(r["pokemon_id"]) in names]
    # group the rows in force per pokemon: all slots of the smallest applicable generation
    in_force: dict[int, dict[int, str]] = {}
    gen_of: dict[int, int] = {}
    for r in past_rows:
        g, pid = int(r["generation_id"]), int(r["pokemon_id"])
        if g < GENERATION:
            continue
        if pid not in gen_of or g < gen_of[pid]:
            gen_of[pid] = g
            in_force[pid] = {}
        if g == gen_of[pid]:
            in_force[pid][int(r["slot"])] = types[int(r["type_id"])]
    out: dict[int, tuple[str, list[str]]] = {}
    for pid, name in names.items():
        slots = in_force.get(pid, current[pid])
        ts = [slots[s] for s in sorted(slots)]
        for t in ts:
            assert t in types.values(), f"{name} has a non-Gen-{GENERATION} type {t}"
        out[pid] = (name, ts)
    assert len(out) == DEX_MAX
    return out


def _mult(factors: list[int]) -> str:
    v = 1.0
    for f in factors:
        v *= f / FACTOR_SCALE
    for label, value in MULT_VALUE.items():
        if abs(v - value) < 1e-9:
            return label
    raise ValueError(f"multiplier {v} is not one of {MULTIPLIERS}")


def build_key() -> list[Cell]:
    gen1 = efficacy(past=True)
    modern = efficacy(past=False)
    cells: list[Cell] = []
    for attack in gen_types().values():
        for pid, (name, ts) in typings().items():
            cells.append(
                Cell(
                    attack_type=attack,
                    pokemon_id=pid,
                    pokemon=name,
                    def_type1=ts[0],
                    def_type2=ts[1] if len(ts) > 1 else "",
                    gen1_multiplier=_mult([gen1[(attack, t)] for t in ts]),
                    modern_multiplier=_mult([modern[(attack, t)] for t in ts]),
                )
            )
    return cells


KEY_FIELDS = [
    "attack_type", "pokemon_id", "pokemon", "def_type1", "def_type2",
    "gen1_multiplier", "modern_multiplier", "dual", "differs",
]


def write_key(cells: list[Cell], path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(KEY_FIELDS)
        for c in cells:
            w.writerow([
                c.attack_type, c.pokemon_id, c.pokemon, c.def_type1, c.def_type2,
                c.gen1_multiplier, c.modern_multiplier, int(c.dual), int(c.differs),
            ])
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_key(path: Path) -> list[Cell]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            Cell(
                attack_type=r["attack_type"],
                pokemon_id=int(r["pokemon_id"]),
                pokemon=r["pokemon"],
                def_type1=r["def_type1"],
                def_type2=r["def_type2"],
                gen1_multiplier=r["gen1_multiplier"],
                modern_multiplier=r["modern_multiplier"],
            )
            for r in csv.DictReader(fh)
        ]


def chart_table(past: bool) -> str:
    """The chart as a markdown table, attack type down the rows, defender
    across the columns. Used verbatim in the prompt for the chart conditions."""
    types = list(gen_types().values())
    chart = efficacy(past=past)
    show = {0: "0", 50: "1/2", 100: "1", 200: "2"}
    head = "| attack \\ defend | " + " | ".join(types) + " |"
    sep = "|" + "---|" * (len(types) + 1)
    rows = [head, sep]
    for a in types:
        rows.append(f"| {a} | " + " | ".join(show[chart[(a, t)]] for t in types) + " |")
    return "\n".join(rows)



def chart_rows(past: bool) -> str:
    """The same chart as one line per attacking type: "Ground attacking:
    Normal 1, Fighting 1, ...". No axis to transpose; every cell is named by
    both types in the order they are read."""
    types = list(gen_types().values())
    chart = efficacy(past=past)
    show = {0: "0", 50: "1/2", 100: "1", 200: "2"}
    lines = []
    for a in types:
        cells = ", ".join(f"{t.title()} {show[chart[(a, t)]]}" for t in types)
        lines.append(f"{a.title()} attacking: {cells}")
    return "\n".join(lines)


# Cells whose answer is known independently of the data, for hand verification.
# (attack, pokemon, expected gen1, expected modern chart ON THE GEN 1 TYPING).
# The fourth column is not "what happens in a modern game": Magnemite here is
# pure Electric and Clefairy pure Normal, so only the four chart cells can
# differ. Six of these were first written against modern typings (FINDINGS D-001).
KNOWN_ANSWERS = [
    ("rock", "charizard", "4", "4"),
    ("ground", "charizard", "0", "0"),
    ("ice", "charizard", "2", "1"),        # Ice vs Fire is 1x in Gen 1
    ("water", "golem", "4", "4"),
    ("electric", "golem", "0", "0"),
    ("normal", "gengar", "0", "0"),
    ("fighting", "gengar", "0", "0"),
    ("ground", "gengar", "2", "2"),
    ("psychic", "gengar", "2", "2"),
    ("ghost", "alakazam", "0", "2"),      # the Gen 1 Ghost-vs-Psychic bug
    ("bug", "venusaur", "4", "1"),        # Bug vs Poison 2x in Gen 1
    ("poison", "parasect", "4", "2"),     # Poison vs Bug 2x in Gen 1
    ("ground", "magnemite", "2", "2"),    # pure Electric in Gen 1, both columns
    ("fire", "magnemite", "1", "1"),
    ("fighting", "clefairy", "2", "2"),   # Normal in Gen 1; the typing, not the chart, is what changed later
    ("poison", "clefable", "1", "1"),
    ("fighting", "jigglypuff", "2", "2"),
    ("dragon", "dragonite", "2", "2"),
    ("ice", "dragonite", "4", "4"),
    ("electric", "gyarados", "4", "4"),
    ("grass", "gyarados", "1", "1"),      # 2 x 1/2
    ("bug", "mr-mime", "2", "2"),         # pure Psychic in Gen 1
    ("water", "blastoise", "1/2", "1/2"),
    ("electric", "pikachu", "1/2", "1/2"),
    ("fire", "articuno", "2", "2"),       # Ice/Flying: 2 x 1
    ("rock", "articuno", "4", "4"),
]


def main() -> None:
    cells = build_key()
    key_path = PROCESSED / "gen1_key.csv"
    digest = write_key(cells, key_path)
    by = {(c.attack_type, c.pokemon): c for c in cells}
    n_diff = sum(c.differs for c in cells)
    manifest = {
        "generation": GENERATION,
        "dex_max": DEX_MAX,
        "types": list(gen_types().values()),
        "cells": len(cells),
        "dual_cells": sum(c.dual for c in cells),
        "differs_cells": n_diff,
        "gen1_multiplier_counts": {m: sum(c.gen1_multiplier == m for c in cells) for m in MULTIPLIERS},
        "key_sha256": digest,
    }
    (PROCESSED / "key_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"{len(cells)} cells, {manifest['dual_cells']} dual, {n_diff} differ between Gen 1 and modern")
    print("gen1 multiplier counts:", manifest["gen1_multiplier_counts"])
    print(f"key sha256 {digest}\n")
    print(f"{'attack':<9}{'defender':<12}{'types':<18}{'gen1':>5}{'modern':>8}  known")
    bad = 0
    for a, p, g, m in KNOWN_ANSWERS:
        c = by[(a, p)]
        ok = (c.gen1_multiplier, c.modern_multiplier) == (g, m)
        bad += not ok
        print(f"{a:<9}{p:<12}{c.def_types:<18}{c.gen1_multiplier:>5}{c.modern_multiplier:>8}  {'ok' if ok else 'MISMATCH expected ' + g + '/' + m}")
    print(f"\nknown-answer cells: {len(KNOWN_ANSWERS) - bad}/{len(KNOWN_ANSWERS)} match")


if __name__ == "__main__":
    main()
