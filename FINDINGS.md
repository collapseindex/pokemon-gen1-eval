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
| [D-003](#d-003) | prompt and format | PLAN.md did not say whether the model may reason before answering; reasoning is allowed, max_tokens pinned at 1024, parse failures reported as their own metric | decided before any run |
| [D-004](#d-004) | item draw | the pinned set is stratified by answer class, not by attack type: 13 to 45 cells per type, and the four `differs` attack types dominate; the first dev draw had no Bug or Poison attacks at all | pinned set kept, dev redrawn balanced |
| [D-005](#d-005) | scope and budget | PLAN.md's four conditions, three Anthropic models and $30 ceiling were written without the multiplication; the budget is $7 on OpenRouter; one condition (chart + full typing list in context), four models across four labs, a closeness scorer beside exact match; predictions P2, P4, P5, P6 retired and three addendum predictions registered here before any run | deviation declared |
| [D-006](#d-006) | chart format | the markdown table costs 3,032 input tokens per call, not the ~1,600 the addendum assumed, and the dev run shows the table itself is what Haiku misreads; a second chart format (one line per attacking type) is registered as a variant before any pinned run, with prediction A6 | deviation declared |
| [O-001](#o-001) | Haiku 4.5, dev set | 84% exact, 0 parse failures; 14 of 16 misses are the chart read transposed (cell (a, b) answered with (b, a)); 0 wrong-Pokemon lookups, 0 multiply errors | observed on dev, not scored against a prediction |
| [D-007](#d-007) | max_tokens | gpt-5-nano hit the 1,024 cap on 30 of 100 dev items with an empty completion: hidden reasoning tokens ate the budget; the 5% rule fired; nano runs at 4,096 | fixed, rule applied |
| [D-008](#d-008) | transposition count | the hand count in O-001 (14 of 16) and the code count (10 of 16) use different definitions: any mirrored cell vs the fully mirrored product; both kept, both named | definitions pinned |
| [O-002](#o-002) | four models, dev set, two chart formats | rows beats table for every model (+0.07 to +0.19 exact); for Haiku and Qwen the transposed misses fall with the format, for Gemini Flash-Lite they do not: its mirror-cell answers come from its prior, not the grid | observed on dev, not scored against a prediction |

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

### D-003
**The plan did not say whether the model may reason before answering**
`src/task.py` · 2026-08-29 · decided before any model call

PLAN.md fixes the item, the options and the scorer but not the response
format. The first draft of the task used Inspect's strict template (the whole
response is `ANSWER: X`), which makes condition B a *silent* lookup-and-multiply
and would penalise a non-thinking model for a reason unrelated to the chart.
Decided, before any run: reasoning is allowed (Inspect's chain-of-thought
multiple-choice template: think step by step, last line `ANSWER: X`),
`max_tokens` pinned at 1024, and the share of responses with no parseable
answer line is reported as `parse_failures` beside accuracy, since `choice()`
scores those as wrong and the two are different findings. The dev run's job
is to show that the truncation rate at 1024 is near zero; if it is not, the
limit is raised and this entry says so.

Same day, three wording changes to the instrument, also before any run: the
system prompt now gives the game's words for each multiplier (0 doesn't
affect, 1/2 not very effective, 2 super effective; two types multiply) and
says what to ignore (STAB, stats, move power, move-specific exceptions); the
chart conditions now say "use only the chart below, even where it disagrees
with what you remember about the games", so a miss on a `differs` cell under
C is an instruction-following failure and not a reasonable resolution of a
conflict with the system prompt. Red/Blue never printed a multiplier; the
numbers are the community's, and the mapping is given so the format is not
the thing being tested.

### D-004
**The draw balanced answer classes and let attack types fall where they may**
`src/sample.py` · 2026-08-29 · pinned set kept, dev set redrawn

Counting the pinned 400 by attack type: Rock 13, Psychic 15, up to Poison 39,
Ghost 44, Bug 45. The `differs` stratum is taken whole and all 71 of its
cells are Bug, Poison, Ghost or Ice attacks, so those four types are
over-represented and any per-attack-type breakdown is confounded with the
stratum. The first dev draw (seed 1, uniform within stratum) had 13 of 15
attack types: no Bug and no Poison at all, by chance (106 and 112 cells were
available). Defender types are skewed too, but that is the universe: 33 of
the 151 are Poison-typed.

The pinned set is registered and is not changed; `test_pinned_set_unchanged_by_balance_option`
holds the draw to the file on disk. What changes: per-attack-type accuracy
on the pinned set is reported with its n and read against the stratum mix,
and P6 (Ghost→Psychic the worst row) is read knowing Ghost has 44 cells, 30
of them `differs`. The dev set is redrawn with `--balance`: within each
stratum the draw cycles across attack types, so dual and single are near
even by type. Immunities and quads cannot be: 14 immune and 34 quad cells
remained after the pinned draw, and quad is nearly half Grass, because that
is where the game's 4x cells are (Grass on Rock/Ground, Rock/Water,
Ground/Water).

### D-005
**The plan's grid did not survive its own arithmetic, and the question got sharper for it**
scope, models, budget · 2026-08-29 · deviation declared, addendum registered before any run

PLAN.md registers four conditions, three Anthropic models, four runs each, and
a $30 ceiling. Multiplied out with the chart in context (~1k input tokens and
~200 output tokens per call, 19,200 calls) that is about $157 at list price,
and the available budget is $7 of OpenRouter credit. The ceiling was written
the way data-deltas D-003 wrote its batch size: without anyone doing the
multiplication. The plan is not edited; this entry is the record.

**What changes.**

- **One condition.** The full Gen 1 chart and the typing of all 151 Pokemon
  are in the system prompt; the question names only the attacking type and
  the defender. The model finds the defender in the list, reads two cells,
  multiplies. Nothing is recalled. This is the plan's condition B with the
  typing moved from the question into a reference list, which adds the
  find-it step and removes the last trace of trivia. The recall conditions
  (A, D) and the prior-override condition (C) stay in the code as parameters
  and are not run; P2, P4, P5 and P6 are retired unmeasured.
- **Models.** Four, one per lab, chosen by price from OpenRouter's public
  list on 2026-08-29: `anthropic/claude-haiku-4.5` (via the `:batch` route at
  $0.50/$2.50 per M), `openai/gpt-5-nano` ($0.05/$0.40),
  `google/gemini-2.5-flash-lite` ($0.10/$0.40),
  `qwen/qwen3-235b-a22b-2507` ($0.087/$0.35). Every model runs the pinned
  400 at three epochs. Projected total under $4. Sonnet and Opus wait for
  money.
- **A second scorer, never blended with the first.** `closeness` reports
  whether the game would have printed the same word (doesn't affect / not
  very effective / normal / super effective) and the distance on the log2
  scale, with immunity three steps from everything because it is a rule and
  not a magnitude, and an unparsed answer the farthest miss. Exact match
  stays primary. The reason to keep them apart: a 2 answered as 4 is
  "close" by word and is exactly the multiply failure the quad stratum
  exists to catch.

**Addendum predictions.** Canonical text and the item-set balance pass are in [ADDENDUM.md](ADDENDUM.md) (commit `48dd575`), hashed like the plan; A4 and A5 were added there. As first written here: P1 and P3
from PLAN.md still apply (P3 read as "the best model is at least 95%").

- **A1, the word is easier than the number.** For every model, bucket
  accuracy exceeds exact accuracy by at least 3 points, and at least half of
  the exact misses are one step off (2 for 4, 1/2 for 1/4, 1 for 2).
- **A2, the multiply is the failure.** For every model, exact accuracy on
  `quad` is below `single` by more than the epoch range, while bucket
  accuracy on `quad` is within the range of `single`. Reading the cells is
  fine; combining them is not.
- **A3, the list is found.** Misses that are explained by reading the wrong
  Pokemon's typing (the predicted multiplier equals the key for a different
  Pokemon named in the reasoning) are under 5% of items for every model.
  Scored by hand on the misses, in the viewer, and reported with the count.

### D-006
**The table is what gets misread, and it costs twice what was budgeted**
`src/task.py` chart_format · 2026-08-29 · deviation declared before any pinned run

Two facts from the dev log ([O-001](#o-001)). The system prompt with the
markdown table is 3,032 input tokens per call through OpenRouter, not the
~1,600 the addendum assumed (a 16-column pipe table tokenises badly), and
cache reads were 0, so the pinned grid at list price is about $4.70 for
Haiku alone. And 14 of Haiku's 16 misses were the same act: it named the
right row and column out loud and then reported the mirror cell.

Registered here, before any model touches the pinned set:

- **A second chart format**, `-T chart_format=rows`: the same 225 cells as
  fifteen lines, "Ground attacking: Normal 1, Fighting 1, ..., Electric 2,
  ...". Every cell is named by both types in reading order, so there is no
  axis to transpose. The table stays the registered default; rows is a
  variant, run on the same items, and reported beside it, never instead of
  it. Test: `test_chart_rows_matches_table_cell_for_cell` holds the two
  renderings equal cell for cell.
- **A6, the format is the finding.** For every model run in both formats,
  exact accuracy under `rows` exceeds exact accuracy under `table` by more
  than the epoch range, and the class of misses where the predicted value
  equals the transposed cell falls by at least half. If A6 fails for a model,
  that model's errors are not orientation and the transposition reading of
  O-001 does not generalise to it.
- **Budget.** The `:batch` route was probed with five dev items (log in
  `logs/probe/`): OpenRouter returns 404, "This model is only available
  through the Batch API. Use the /api/beta/batches endpoint instead", which
  Inspect's OpenRouter provider does not speak. So Haiku runs the pinned
  set once, at list price, table format only (about $1.60), and is reported
  with its stderr and without an epoch band; P1 is not scorable for Haiku
  and says so. The three cheap models run both formats at three epochs
  (about $2). The $5 ceiling in the addendum stands; the dev and probe
  runs so far cost about $0.40.

### O-001
**Haiku reads the chart transposed**
`openrouter/anthropic/claude-haiku-4.5` · dev set, 100 items, 1 epoch · 2026-08-29

Log `logs/dev/2026-08-29T08-58-40-00-00_pokemon-gen1_NJHSyki4BXErRoEZxtrSUT.eval`,
summary `data/results/20260829_020454_analyze_dev.json`. Exact 0.84, bucket
0.85, mean 0.27 steps off, parse failures 0.00, predicted-letter shares
within 1 of the target shares. By stratum: immune 1.00, dual 0.83, single
0.83, quad 0.73. 3,032 input and 180 output tokens per sample; about $0.39.

The 16 misses read one by one, which is the method A3 prescribes:

- **14 are the chart read transposed.** The reasoning says "row: Ground,
  column: Electric" and reports the value of Electric attacking Ground (0);
  Fire vs Diglett comes back 2 (Ground attacking Fire); Rock vs Articuno
  reads Flying attacking Rock (1/2) for Rock attacking Flying (2). In every
  one of the 14 the predicted multiplier equals the key with attacker and
  defender swapped. The chart is symmetric on most pairs, so the swap is
  only visible on the asymmetric cells, which is where these all are.
- **2 are a plain wrong cell** (Grass vs Ground read as 1/2; Ground vs
  Ghost read as 0), not a transposition.
- **0 wrong-Pokemon lookups**: all 100 typings were found correctly in the
  151-line list. **0 multiply errors**: every time both cells were read
  right, the product was right. The `quad` stratum's 0.73 is lookups, not
  arithmetic, which is the opposite of what A2 predicts for this model.

Not scored against a prediction (dev set, by D-002). It is the reason for
D-006.

### D-007
**A reasoning model spent the whole token budget thinking and never wrote the answer line**
`max_tokens` · gpt-5-nano · 2026-08-29 · fixed, rule applied

At `max_tokens` 1024 gpt-5-nano returned an empty completion with
`stop_reason: max_tokens` on 30 of 100 dev items in table format and 11 of
100 in rows: about 800 hidden reasoning tokens per item, then nothing left
for the `ANSWER:` line. `choice()` scores those as wrong, which is why the
`parse_failures` metric exists: the table would have read 0.69 and meant
"truncated", not "wrong". The 5% rule from ADDENDUM fired. Rerun at 4,096:
0.98 in both formats, zero failures, about 900 output tokens per item.

nano runs the pinned set at 4,096; the other three, which had 0 to 1
failures in 100 at 1,024, stay at 1,024. Recorded per run in the log's
`task_args` and in the analyze table's `max_tok` column. A budget that
cuts one model's reasoning and not another's is a confound, so it is
printed beside every number rather than hidden.

### D-008
**Two counts of "transposed", one by hand and one by code, and they disagree**
`src/analyze.py` transposed_misses · 2026-08-29 · definitions pinned

O-001 was read by hand: 14 of 16 Haiku misses were called transpositions.
The code count added for O-002 says 10 of 16. Both are right about
different things. The hand count called a miss transposed if *any* chart
cell in the reasoning was read mirrored (Rock vs Articuno: Rock→Ice read
correctly, Rock→Flying read as Flying→Rock). The code count calls a miss
transposed only if the predicted multiplier equals the product of *every*
cell mirrored, which on a dual-type defender is a stricter thing.

Both stay. The code count is the one in the tables, because it is
recomputable from the log without a reader; the hand count is the one
that describes what the model did, and A3-style hand reading of misses
stays in the method. The difference between them is itself reported. This
is the known-answer box firing the other way from D-001: this time the
hand was not wrong, but it was measuring something the code had to be told
about.

### O-002
**Rows beats table for every model; for one of them the mirror answers survive the format**
four models · dev set, 100 items, 1 epoch each · 2026-08-29

From `data/results/20260829_021421_analyze_dev.json`. Exact accuracy, then
transposed misses over misses on asymmetric cells over all misses:

| model | table | rows | transposed / asym / misses (table) | same (rows) |
|---|---|---|---|---|
| gpt-5-nano (4,096) | 0.98 | 0.98 | 2 / 2 / 2 | 0 / 2 / 2 |
| claude-haiku-4.5 | 0.84 | 0.96 | 10 / 16 / 16 | 2 / 4 / 4 |
| qwen3-235b-a22b-2507 | 0.75 | 0.82 | 7 / 19 / 25 | 4 / 12 / 18 |
| gemini-2.5-flash-lite | 0.55 | 0.64 | 18 / 36 / 45 | 20 / 29 / 36 |

Three things, in order of confidence:

1. **The format moves every model in the same direction**, +0.07 to +0.12
   exact for the three that had headroom. That is the A6 direction. It is
   one epoch on the dev set and is not scored.
2. **For Haiku the misses are the grid.** Ten of sixteen table misses are
   full-mirror answers; under rows, two of four. The multiply and the list
   lookup were never the problem (O-001).
3. **For Gemini Flash-Lite the mirror answers are not the grid.** Under
   rows there is no axis to confuse, and it still answers the mirrored
   cell on 20 of 29 asymmetric-cell misses. A mirrored answer on a rows
   prompt can only come from the model's own stored relation ("Rock is
   weak to Water" retrieved when asked about Water attacking Rock) winning
   over the line in front of it. Same symptom as Haiku, different cause;
   the format change separates them. Qwen sits between.

nano at 1,024 is in the results file too (0.69 / 0.88) and is D-007, not a
capability number.
