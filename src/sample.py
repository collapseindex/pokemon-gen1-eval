"""Draw the pinned item set from the key, stratified, seeded.

Strata (a cell belongs to the first that matches):
  differs   Gen 1 and modern charts disagree on this cell: all of them
  immune    gen1 multiplier is 0
  quad      gen1 multiplier is 4 or 1/4
  dual      dual-typed defender, ordinary multiplier
  single    single-typed defender, ordinary multiplier

Usage: python -m src.sample --n 400 --seed 0
Writes data/processed/items_s<seed>_n<n>.csv; the task reads that file.
"""

from __future__ import annotations

import argparse
import csv
import random
from collections import Counter
from pathlib import Path

from .key import PROCESSED, Cell, read_key

STRATA = ["differs", "immune", "quad", "dual", "single"]
# share of the non-"differs" budget; "differs" is taken whole
SHARES = {"immune": 0.15, "quad": 0.15, "dual": 0.40, "single": 0.30}


def stratum(c: Cell) -> str:
    if c.differs:
        return "differs"
    if c.gen1_multiplier == "0":
        return "immune"
    if c.gen1_multiplier in ("4", "1/4"):
        return "quad"
    return "dual" if c.dual else "single"


def _round_robin(pool: list[Cell], k: int, rng: random.Random) -> list[Cell]:
    """Take k cells from the pool spreading across attack types: shuffle each
    type's bucket, then cycle through the types taking one at a time."""
    buckets: dict[str, list[Cell]] = {}
    for c in pool:
        buckets.setdefault(c.attack_type, []).append(c)
    order = sorted(buckets)
    rng.shuffle(order)
    for b in buckets.values():
        rng.shuffle(b)
    out: list[Cell] = []
    while len(out) < k and any(buckets.values()):
        for t in order:
            if buckets[t] and len(out) < k:
                out.append(buckets[t].pop())
    return out


def draw(
    cells: list[Cell],
    n: int,
    seed: int,
    exclude: set[tuple[str, str]] | None = None,
    with_differs: bool = True,
    balance: bool = False,
) -> list[Cell]:
    """``exclude`` is a set of (attack_type, pokemon) already spent (a pinned
    set); ``with_differs=False`` skips the differs stratum entirely, for a
    development draw when the pinned set already holds all of them;
    ``balance=True`` spreads each stratum's draw across attack types
    (round-robin) instead of uniform random. The pinned set (seed 0, n 400)
    was drawn with balance=False and must reproduce byte for byte."""
    rng = random.Random(seed)
    pools: dict[str, list[Cell]] = {s: [] for s in STRATA}
    for c in cells:
        if exclude and (c.attack_type, c.pokemon) in exclude:
            continue
        pools[stratum(c)].append(c)
    chosen = list(pools["differs"]) if with_differs else []
    budget = n - len(chosen)
    if budget < 0:
        raise ValueError(f"n={n} is smaller than the {len(chosen)} differing cells")
    taken: set[tuple[str, str]] = set()
    for s, share in SHARES.items():
        k = min(round(budget * share), len(pools[s]))
        picked = _round_robin(pools[s], k, rng) if balance else rng.sample(pools[s], k)
        chosen.extend(picked)
        taken.update((c.attack_type, c.pokemon) for c in picked)
    # rounding across strata can leave the draw a cell short; top up from dual
    spare = [c for c in pools["dual"] if (c.attack_type, c.pokemon) not in taken]
    while len(chosen) < n and spare:
        chosen.append(spare.pop(rng.randrange(len(spare))))
    rng.shuffle(chosen)
    return chosen


def write_items(items: list[Cell], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["item_id", "stratum", "attack_type", "pokemon_id", "pokemon", "def_type1", "def_type2", "gen1_multiplier", "modern_multiplier"])
        for i, c in enumerate(items):
            w.writerow([f"i{i:04d}", stratum(c), c.attack_type, c.pokemon_id, c.pokemon, c.def_type1, c.def_type2, c.gen1_multiplier, c.modern_multiplier])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=400)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--exclude", default=None, help="an items csv whose cells must not be drawn again")
    ap.add_argument("--no-differs", action="store_true", help="skip the differs stratum")
    ap.add_argument("--tag", default="items", help="filename prefix (items, dev)")
    ap.add_argument("--balance", action="store_true", help="round-robin across attack types within each stratum")
    a = ap.parse_args()
    cells = read_key(PROCESSED / "gen1_key.csv")
    exclude = None
    if a.exclude:
        with (PROCESSED / a.exclude).open(newline="", encoding="utf-8") as fh:
            exclude = {(r["attack_type"], r["pokemon"]) for r in csv.DictReader(fh)}
    items = draw(cells, a.n, a.seed, exclude=exclude, with_differs=not a.no_differs, balance=a.balance)
    out = PROCESSED / f"{a.tag}_s{a.seed}_n{a.n}.csv"
    write_items(items, out)
    print(f"wrote {len(items)} items to {out}")
    print("strata:", dict(Counter(stratum(c) for c in items)))
    print("gen1 multipliers:", dict(Counter(c.gen1_multiplier for c in items)))
    print("attack types:", dict(Counter(c.attack_type for c in items).most_common()))


if __name__ == "__main__":
    main()
