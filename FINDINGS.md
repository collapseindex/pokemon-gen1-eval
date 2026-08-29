# Findings

A ledger, not an essay. Three series:

| series | what it records |
|---|---|
| **D** | a defect in this harness: a key cell that was wrong, a scorer that passed what it had not verified, a plan that said one thing and code that did another |
| **O** | an observation from the runs, scored against the prediction PLAN.md made for it |
| **N** | a negative result: a prediction that failed, recorded rather than dropped |

Ids are permanent. PLAN.md is never edited; a mistake in it is a D entry here.

## Index

| id | subject | finding | status |
|---|---|---|---|
| [D-001](#d-001) | known-answer list | six of 26 hand-written expectations were wrong; the derived key was right | fixed |
| [D-002](#d-002) | item sets | PLAN.md named no development set; a 100-item dev set disjoint from the pinned 400 is added for harness work | deviation declared |

## Defects in this harness

### D-001
**Six of 26 hand-written known answers were wrong; the key was right**
`src/key.py` KNOWN_ANSWERS · 2026-08-29 · fixed

First run of `python -m src.key`: 20 of 26 known-answer cells matched. The six
mismatches were all in the fourth column (modern chart applied to the Gen 1
typing), and all were the author's error, not the data's:

- Ground/Magnemite, Fire/Magnemite, Fighting/Clefairy, Poison/Clefable,
  Fighting/Jigglypuff: written against *modern typings* (Electric/Steel, Fairy).
  The column is defined as the modern chart on the Gen 1 typing, where Magnemite
  is pure Electric and Clefairy pure Normal, so only the four changed chart
  cells can make the two columns differ.
- Grass/Gyarados: written as 1/2. Water/Flying is 2 x 1/2 = 1.

Fixed by correcting the list and its comment. Kept because it is the point of
the known-answer box: the verification list is written by a person and is as
fallible as anything else; when it disagrees with a derived key, both get
checked, and this time the person lost. `differs` cells: 71, exactly the cells
touching the four Gen 1 chart overrides (`test_differs_cells_are_exactly_the_override_cells`).

### D-002
**The plan pinned one item set and named no development set**
`src/sample.py` · 2026-08-29 · deviation declared

PLAN.md pins 400 items and says every model runs on them. It says nothing
about where the harness gets debugged, which means the first real run would
have been on the registered set with the scorer and metrics untried on a live
model. A development set is added: 100 cells drawn with seed 1 from the 1,865
cells the pinned set did not use, same strata and shares, disjoint by
construction (`test_dev_draw_is_disjoint_from_pinned_set`). It has no
`differs` cells, because the pinned set already holds all 71 that exist; any
dev work on condition C therefore sees only cells where the two charts agree.

Rule for the dev set: nothing measured on it is reported against a
prediction. The pinned set is still the only set the plan's numbers come
from, and it is not run until the dev run has been read in the log viewer
end to end. The plan is not edited.
