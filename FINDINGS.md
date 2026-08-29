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
