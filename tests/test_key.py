"""The key and the task, negative-tested.

Every test here is a check that can fail: the known answers are independent
of the data, the perturbation test proves a wrong chart changes the key, and
the mock-model tests prove the scorer awards 1.0 for the key and 0.0 for a
planted wrong answer.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src import key as K
from src.sample import STRATA, draw, stratum
from src.task import LETTERS, build_samples, load_items

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def cells():
    return K.build_key()


def test_shape(cells):
    assert len(cells) == 15 * 151
    assert len(K.gen_types()) == 15
    assert set(K.gen_types().values()) == {
        "normal", "fighting", "flying", "poison", "ground", "rock", "bug", "ghost",
        "fire", "water", "grass", "electric", "psychic", "ice", "dragon",
    }


def test_known_answers(cells):
    by = {(c.attack_type, c.pokemon): c for c in cells}
    bad = [
        (a, p, c.gen1_multiplier, c.modern_multiplier, g, m)
        for a, p, g, m in K.KNOWN_ANSWERS
        for c in [by[(a, p)]]
        if (c.gen1_multiplier, c.modern_multiplier) != (g, m)
    ]
    assert bad == []


def test_gen1_typings_applied():
    t = {name: ts for name, ts in K.typings().values()}
    assert t["magnemite"] == ["electric"]
    assert t["magneton"] == ["electric"]
    assert t["clefairy"] == ["normal"]
    assert t["jigglypuff"] == ["normal"]
    assert t["mr-mime"] == ["psychic"]
    assert t["charizard"] == ["fire", "flying"]
    assert all(len(ts) in (1, 2) for ts in t.values())


def test_gen1_chart_overrides():
    g = K.efficacy(past=True)
    m = K.efficacy(past=False)
    assert g[("bug", "poison")] == 200 and m[("bug", "poison")] == 50
    assert g[("poison", "bug")] == 200 and m[("poison", "bug")] == 100
    assert g[("ghost", "psychic")] == 0 and m[("ghost", "psychic")] == 200
    assert g[("ice", "fire")] == 100 and m[("ice", "fire")] == 50
    changed = {k for k in g if g[k] != m[k]}
    assert changed == {("bug", "poison"), ("poison", "bug"), ("ghost", "psychic"), ("ice", "fire")}


def test_differs_cells_are_exactly_the_override_cells(cells):
    for c in cells:
        touched = any(
            (c.attack_type, t) in {("bug", "poison"), ("poison", "bug"), ("ghost", "psychic"), ("ice", "fire")}
            for t in (c.def_type1, c.def_type2) if t
        )
        assert c.differs == touched, c


def test_negative_perturbed_chart_changes_key(cells, monkeypatch):
    """Plant one wrong cell in the chart; the key must move on exactly the
    cells that touch it and nowhere else."""
    real = K.efficacy

    def wrong(past: bool):
        chart = real(past)
        if past:
            chart[("water", "fire")] = 50  # planted: water resisted by fire
        return chart

    monkeypatch.setattr(K, "efficacy", wrong)
    perturbed = K.build_key()
    moved = [(a.attack_type, a.pokemon) for a, b in zip(cells, perturbed) if a.gen1_multiplier != b.gen1_multiplier]
    assert moved, "a wrong chart produced an identical key: the key is not derived from the chart"
    assert all(a == "water" for a, _ in moved)
    fire_mons = {name for name, ts in K.typings().values() if "fire" in ts}
    assert {p for _, p in moved} == fire_mons


def test_key_written_matches_build(cells):
    path = ROOT / "data" / "processed" / "gen1_key.csv"
    if not path.exists():
        pytest.skip("run python -m src.key first")
    assert K.read_key(path) == cells


def test_sample_takes_all_differing_and_is_deterministic(cells):
    a = draw(cells, 400, 0)
    b = draw(cells, 400, 0)
    assert [(c.attack_type, c.pokemon) for c in a] == [(c.attack_type, c.pokemon) for c in b]
    assert len(a) == len({(c.attack_type, c.pokemon) for c in a}), "duplicate items"
    n_diff = sum(c.differs for c in cells)
    assert sum(c.differs for c in a) == n_diff
    assert {stratum(c) for c in a} == set(STRATA)


def test_dev_draw_is_disjoint_from_pinned_set(cells):
    pinned = draw(cells, 400, 0)
    spent = {(c.attack_type, c.pokemon) for c in pinned}
    dev = draw(cells, 100, 1, exclude=spent, with_differs=False)
    assert len(dev) == 100
    assert not ({(c.attack_type, c.pokemon) for c in dev} & spent)
    assert not any(c.differs for c in dev)


def test_targets_are_letters_of_the_right_multiplier(tmp_path, cells):
    rows = [
        {"item_id": "i0", "stratum": "differs", "attack_type": "ghost", "pokemon_id": "65", "pokemon": "alakazam",
         "def_type1": "psychic", "def_type2": "", "gen1_multiplier": "0", "modern_multiplier": "2"},
    ]
    s_gen1 = build_samples(rows, "gen1", True)[0]
    s_modern = build_samples(rows, "modern", True)[0]
    assert s_gen1.target == LETTERS[K.MULTIPLIERS.index("0")]
    assert s_modern.target == LETTERS[K.MULTIPLIERS.index("2")]
    assert "Generation I" in s_gen1.input and "current" in s_modern.input
    assert "(Psychic)" in s_gen1.input
    assert "(Psychic)" not in build_samples(rows, "none", False)[0].input


def _run_mock(answers: list[str], rows):
    from inspect_ai import Task, eval as inspect_eval
    from inspect_ai.dataset import MemoryDataset
    from inspect_ai.model import ModelOutput, get_model
    from inspect_ai.scorer import choice
    from inspect_ai.solver import multiple_choice

    samples = build_samples(rows, "gen1", True)
    model = get_model("mockllm/model", custom_outputs=[ModelOutput.from_content("mockllm/model", f"ANSWER: {a}") for a in answers])
    t = Task(dataset=MemoryDataset(samples), solver=[multiple_choice(shuffle=False)], scorer=choice())
    log = inspect_eval(t, model=model, log_dir=str(ROOT / "logs" / "tests"), display="none")[0]
    return log.results.scores[0].metrics["accuracy"].value


@pytest.mark.slow
def test_scorer_awards_key_and_rejects_planted_wrong_answer():
    rows = load_items(ROOT / "data" / "processed" / "items_s0_n400.csv")[:6]
    right = [LETTERS[K.MULTIPLIERS.index(r["gen1_multiplier"])] for r in rows]
    wrong = [LETTERS[(K.MULTIPLIERS.index(r["gen1_multiplier"]) + 1) % 6] for r in rows]
    assert _run_mock(right, rows) == 1.0
    assert _run_mock(wrong, rows) == 0.0
