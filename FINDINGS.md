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
| [D-009](#d-009) | upstream routing | OpenRouter split one llama run across two hosts and one of them returned HTTP 500 mid-generation on 31 of 100 items, scored as parse failures; provider pinned, host recorded per run; Qwen was served by ten different hosts in one run | fixed, census added |
| [O-003](#o-003) | two on-device-class models, dev set | llama-3.2-3b at chance (0.18) in both formats; gemma-3-4b below the majority baseline (0.26 table, 0.34 rows) with immunities the worst stratum | observed on dev, not scored against a prediction |
| [D-011](#d-011) | parse_failures metric | wrong whenever epochs > 1: Inspect's epoch reduction drops the `answer` field, so the in-log metric reads 0.94 on a run whose true rate is 0.198; analyze, which reads per-epoch samples, is the record | fixed: a `parsed` scorer with a numeric value, negative-tested at epochs=2 |
| [D-012](#d-012) | qwen3-32b, table | a thinking model at 1,024 tokens: 14% of table calls truncated before the answer line; rerun at 4,096: 0.828 [0.788, 0.862], 0.08% truncated; the 0.697 floor is superseded | rerun, fixed |
| [O-005](#o-005) | replication, four knee models, a second 400-item set | order and MoE placement replicate (R2, R3); every model lands inside its pinned interval or within the baseline shift (R4); the "12B beats always-1" half of R1 fails on a set whose majority is 0.478: 12B is where reading starts, not where it beats the dumbest strategy | scored |
| [O-006](#o-006) | rows x3, four knee rungs (REVIEW.md run 1) | the format gain has a band: rows minus table exceeds the sum of both epoch ranges by 2 to 3x for all four (V1 held); every one-epoch rows number within 0.02 of its three-epoch mean (V2 held) | scored |
| [O-007](#o-007) | qwen3-235b-a22b on a second host (REVIEW.md run 2) | DeepInfra 0.725 [0.679, 0.766] against GMICloud 0.764 [0.720, 0.803]: inside the interval (V3 held, at the edge); the host moves the number by 0.04; on both hosts the 235B MoE is below the 32B dense model (0.828) | scored |
| [D-013](#d-013) | git history | two internal files (the method checklist and a verbatim reviewer text) were purged from history before publication; every commit after the first of them was rewritten, so the commit ids recorded for the addendum, replication and review registrations changed; the blob hashes did not | recorded |
| [O-008](#o-008) | lookup residual and list position (review 2) | below 4B, 15 to 45% of lookup misses state a wrong typing for the defender; from 27B up, 0 to 1%: the small models fail to find the line, the large ones misread the cell; accuracy by list position shows a small primacy effect and no middle dip | recorded |
| [O-004](#o-004) | the ladder, pinned set | the knee is between 8B and 12B total params; nothing under 12B beats always-"1"; the MoE sits with its total size; rows beats table for 9 of 10 models, by up to +0.23; predictions scored: P1, P3, A6 (accuracy clause) held; A1, A2 (bucket clause), A4, A5, A6 (transposition clause), A7 (MoE clause) failed | scored |
| [D-010](#d-010) | model list | the question changed from "four labs" to "how small a model can do this": a nine-model size ladder replaces the addendum's list; Haiku and Flash-Lite drop from the pinned run (dev numbers kept); host, quantisation and parameter counts pinned in a registry; A7 registered | deviation declared |

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

**Addendum predictions.** Canonical text and the item-set balance pass are in [ADDENDUM.md](ADDENDUM.md) (commit `8717c65`), hashed like the plan; A4 and A5 were added there. As first written here: P1 and P3
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

### D-009
**The provider behind the provider: one run, two hosts, one of them broken**
OpenRouter routing · 2026-08-29 · fixed, census added

Two on-device-class models were added (the addendum allows additions):
`meta-llama/llama-3.2-3b-instruct` and `google/gemma-3-4b-it`. The first
llama dev run came back 0.17 with 31% parse failures, stop reason
`unknown`, completions cut mid-word at about 56 tokens. Not `max_tokens`.
Reading the raw responses in the log: OpenRouter had split the 100 calls
between two upstream hosts, Parasail (30, all clean) and Cloudflare (70, of
which 31 returned `finish_reason: error` with `{"code": 500, "message":
"Internal Server Error"}` and a partial completion). The rows run was the
same: 22 of 66 Cloudflare calls failed. `choice()` scored every one as
wrong, and without the parse-failure metric the model would have read as
"worse than chance" when a third of its answers had never been generated.

Fixes. The two tainted logs are moved to `logs/discarded/`. llama reruns
pinned to Parasail via Inspect's model arg
(`-M provider={"order":["Parasail"],"allow_fallbacks":false}`): 0.18 in
both formats, parse failures 3% and 0%. `analyze` now records the upstream
host per call and the count of host-side errors for every run, so a
mixed-host run is visible in the results file. The census found a second
thing: the Qwen dev runs were served by **ten different hosts** (Novita,
DeepInfra, GMICloud, Google, Nebius, Parasail, Alibaba, StreamLake,
AtlasCloud, Venice), which may not all serve the same quantisation. For
the pinned runs every model is pinned to one host and the host is in the
results file. The host is part of the instrument.

### O-003
**Two Siri-sized models: one at chance, one below the majority baseline**
llama-3.2-3b-instruct (Parasail), gemma-3-4b-it (DeepInfra) · dev set, 100 items, 1 epoch · 2026-08-29

| model | table | rows | bucket (rows) | immune | quad | transposed / asym / misses (rows) |
|---|---|---|---|---|---|---|
| llama-3.2-3b-instruct | 0.18 | 0.18 | 0.27 | 0.07 | 0.00 | 20 / 48 / 82 |
| gemma-3-4b-it | 0.26 | 0.34 | 0.44 | 0.50 | 0.27 | 19 / 44 / 66 |

Chance is 0.167 and always-"1" is 0.42. llama is at chance in both formats
and has not solved a single 4x or 1/4x cell; its reasoning names the right
Pokemon and then narrates a chart that is not the one in the prompt. gemma
is above chance, below the majority baseline, and moves with the format
(+0.08 under rows), so it is reading something. Its worst stratum is
immunities: a 0 in the chart is the easiest cell to read and the easiest
prior to override ("Ground can't hit Flying" is memorised; "Ghost can't
hit Normal" apparently is not). Neither model's transposed count is a
grid effect, since both are about as high under rows as under table.

What this says: the task is find, look up, multiply, with everything
needed in context, and the 3B-4B class cannot do it at a rate that beats
guessing the commonest answer. It does not say what these models know
about Pokemon; they were never asked to recall anything. Dev set, one
epoch, unscored.

### D-010
**The question got better, so the model list changed: a size ladder**
`src/models.py` · 2026-08-29 · deviation declared before any pinned run

The dev runs (O-001 to O-003) showed the frontier tier clears this task
(nano 0.98, Haiku 0.96 under rows) and the 3B class does not (llama at
chance). The interesting question is the one in between: **how small a
model can you get away with for find, look up, multiply over a reference
in context**, which is the on-device shape. The addendum's list (four labs,
one model each) does not answer it. This entry replaces the list and says
what that costs.

**The ladder**, one host per model, quantisation held constant within a
family where a host offers it, parameter counts as published:

| params | model | family | quant | host |
|---|---|---|---|---|
| 1.2B | llama-3.2-1b-instruct | llama-3 | unknown | Cloudflare (only host) |
| 3.2B | llama-3.2-3b-instruct | llama-3 | bf16 | Parasail |
| 4.3B | gemma-3-4b-it | gemma-3 | bf16 | DeepInfra |
| 8.0B | llama-3.1-8b-instruct | llama-3 | fp8 | DeepInfra |
| 12.2B | gemma-3-12b-it | gemma-3 | bf16 | DeepInfra |
| 27.4B | gemma-3-27b-it | gemma-3 | bf16 | Novita |
| 30.5B (3.3B active) | qwen3-30b-a3b-instruct-2507 | qwen-3 | bf16 | CoreWeave |
| 32.8B | qwen3-32b | qwen-3 | fp8 | DeepInfra |
| 235B (22B active) | qwen3-235b-a22b-2507 | qwen-3 | fp8 | GMICloud |
| undisclosed | gpt-5-nano (4,096 tokens) | ceiling | | OpenAI |

Table format at three epochs for every model, then rows at one epoch.
Projected about $3.20 on top of the $1.25 spent; the $5 ceiling stands.

**Removed from the pinned run**, which the addendum said would not happen:
`claude-haiku-4.5` ($1.60 a pass, and its finding is the format, measured
on dev) and `gemini-2.5-flash-lite` (undisclosed size, does not sit on a
curve). Their dev numbers are reported as dev numbers. gpt-5-nano stays as
the ceiling and is not on the curve either, for the same reason.

**How the curve is tracked.** `src/models.py` is the single source for
parameter counts (total and active, because a 30B MoE with 3.3B active is
two different points depending on the axis), host, quantisation and token
budget; nothing downstream types a number. `analyze` writes a
`_curve_.csv` beside the results JSON with, per (model, format): both
parameter counts, the pinned host and every host actually seen, host-side
error count, exact accuracy with its binomial stderr and the epoch range,
bucket, steps off, parse failures, transposed misses, and the quad, immune
and differs strata. The curve is that file, plotted; the plot is not the
record.

**A7, registered now.** Within each dense family (llama 1→3→8, gemma
4→12→27), exact accuracy is monotone in parameter count and every step is
larger than the two epoch ranges. The 30B-A3B MoE lands nearer the 3B-4B
points than the 32B dense point on exact accuracy: active parameters, not
total, predict this task. The smallest model to reach 0.90 exact under
table is at or above 12B.

### D-011
**The parse-failure metric lies as soon as there is more than one epoch**
`src/task.py` parse_failures · llama-3.2-1b, pinned set, 3 epochs · 2026-08-29 · open, fix after the ladder

First rung of the ladder: the in-log `parse_failures` read **0.943**. The
per-epoch samples say 238 of 1,200, **0.198**. The metric counts a score
as unparsed when `score.answer` is empty; with `epochs > 1` Inspect reduces
the three scores per item to one before metrics run, and the reduced score
carries a numeric value (0.667 for two hits in three) and `answer=None`.
Every reduced score therefore looks unparsed. On every one-epoch dev run
the number was right, which is why it was trusted; the first three-epoch
run is the first time the reducer touched it.

Consequences, in order. The rate in `analyze` is computed from the raw
per-epoch samples and is correct (`parse_failures 0.1983` for this log);
the curve CSV takes it from there. The in-log metric is wrong for every
pinned run and must not be read from `inspect view`. The fix is a third
scorer whose *value* is 1 or 0 for parsed, which reduces correctly by mean;
it is not applied while the ladder is running, because `run_ladder`
loads `task.py` fresh for each rung and a scorer added mid-ladder would
give the later rungs a different scorer set from the earlier ones.
Applied and negative-tested at epochs=2 once the ladder exits.

What the 1B failures are, since the number is now real: all 1,200 calls
finished `stop` on one host with zero host errors. The 238 unparsed
completions either give the answer without the required last line ("The
correct answer is C) 1/2") or start reproducing the type chart. That is
the model, and it is counted against it as the format demands.

### D-012
**One rung ran with its reasoning cut short, and the number is kept as a floor**
qwen3-32b, table format · 2026-08-29 · flagged, not rerun

qwen3-32b thinks before it answers by default. At `max_tokens` 1,024 the
table run (1,200 calls) truncated 14% of completions before the `ANSWER:`
line; the rows run, whose prompt is shorter, truncated 2%. The D-007 rule
says raise the budget and rerun. It was not applied: a 32B rerun at 4,096
costs about $0.80 of the $2.79 left in the wallet, and the rows number for
the same model (0.930, 2% truncated) already shows what the model can do.
So the table number, **0.697, was a floor**: 14% of its calls were scored
wrong without an answer having been produced.

**Rerun, same day**, registered in REPLICATION.md before running: 4,096
tokens, same host, same three epochs on the pinned set. **0.828 [0.788,
0.862]**, range 0.025, 1 truncated call in 1,200. The 1,024 log is in
`logs/superseded/` and is no longer in the curve. Two consequences for
O-004: under table, qwen3-32b dense (0.83) now passes qwen3-235b-a22b
(0.76) as well as under rows, so the 32B dense point is the top of the
open ladder in both formats; and the rows-minus-table gain for 32B shrinks
from +0.23 to +0.10, in line with its neighbours. A 0.13 swing from the
token budget alone is the reason the budget is printed beside every
number.

### O-004
**The ladder: a knee between 8B and 12B, and a grid that costs every model something**
nine models plus a ceiling · pinned 400 · table x3 epochs, rows x1 · 2026-08-29

Source: `data/results/20260829_035620_analyze_pinned.json`, curve
`20260829_035620_curve_pinned.csv` and `.svg`. Exact accuracy; majority
baseline 0.408, chance 0.167. Table has a three-epoch range; rows is one
epoch and carries only its binomial stderr (about 0.02 at n=400).

| params (active) | model | table | range | rows | rows minus table | true parse fail (table / rows) |
|---|---|---|---|---|---|---|
| 1.2B | llama-3.2-1b | 0.223 | 0.035 | 0.295 | +0.07 | 0.20 / 0.17 |
| 3.2B | llama-3.2-3b | 0.250 | 0.020 | 0.240 | -0.01 | 0.01 / 0.01 |
| 4.3B | gemma-3-4b | 0.275 | 0.050 | 0.450 | +0.18 | 0.00 / 0.00 |
| 8.0B | llama-3.1-8b | 0.279 | 0.010 | 0.432 | +0.15 | 0.02 / 0.03 |
| 12.2B | gemma-3-12b | 0.507 | 0.020 | 0.642 | +0.14 | 0.00 / 0.00 |
| 27.4B | gemma-3-27b | 0.617 | 0.022 | 0.688 | +0.07 | 0.00 / 0.00 |
| 30.5B (3.3B) | qwen3-30b-a3b | 0.642 | 0.050 | 0.820 | +0.18 | 0.00 / 0.00 |
| 32.8B | qwen3-32b | 0.697 at 1,024 tokens (floor); **0.828 [0.788, 0.862]** at 4,096 (D-012 rerun) | 0.025 | 0.930 | +0.10 | 0.00 / 0.02 |
| 235B (22B) | qwen3-235b-a22b | 0.764 | 0.018 | 0.843 | +0.08 | 0.00 / 0.00 |
| undisclosed | gpt-5-nano (4,096) | 0.954 | 0.022 | 0.988 | +0.03 | 0.00 / 0.01 |

In order of how much the data supports it:

1. **Nothing under 12B beats always answering "1."** 1B through 8B sit at
   0.22 to 0.28 under table, below the 0.41 majority, with quads at 0.01 to
   0.08. Gemma 12B is the first rung above the baseline (0.507) and the
   Gemma line is monotone from there (0.507, 0.617). The knee on this task,
   with the chart as a grid, is between 8B and 12B total parameters. Under
   rows the 4B and 8B rungs clear the baseline (0.45, 0.43) and the knee
   moves down to roughly 4B, which is the on-device class.
2. **The MoE goes with its total, not its active, size.** qwen3-30b-a3b
   (3.3B active) scores 0.642 table / 0.820 rows, beside the 27B and 32B
   dense points and far from the 3B and 4B points. Whatever limits the
   small dense models, it is not the compute per token. A7's MoE clause
   predicted the opposite and **failed**.
3. **Rows beats table for 9 of 10 models**, by more than the table range
   everywhere except llama-3.2-3b (which is at chance either way). The gain
   is +0.07 to +0.18 for the eight models that moved (largest at 4B, 8B and the
   30B MoE; 32B is +0.10 after the D-012 rerun, +0.23 before it) and +0.03 at
   the ceiling.
   Under rows, qwen3-32b (0.930) passes qwen3-235b (0.843) and comes within
   0.06 of the ceiling model's table number. The grid is a reading tax that
   every model pays and the larger ones pay less of; A6's accuracy clause
   **held** for 9 of 10.
4. **The full-mirror transposition count does not fall with the format**
   for most models (A6's second clause **failed**, 8 of 10). Only nano and
   qwen3-32b halve it. For everyone else a mirror-cell answer under rows is
   as common as under table, so, as with Gemini on dev (O-002), the
   mirrored answers below 32B are mostly the stored relation, not the grid.
   The format helps those models for other reasons (the visible one in the
   logs: fewer lookups land on the wrong row entirely).
5. **The prior leaks at the top, not the bottom** (A4 **failed**, and in an
   informative way). `differs` cells, where the chart in context contradicts
   the memorised chart, run 0.09 below `dual` for nano, 235B and 12B, 0.14 to
   0.28 below for 27B to 32B (the 32B figure is the 4,096-token rerun; it
   was 0.18 at 1,024), and show no gap at all for 1B to 8B. A model
   has to be able to read the chart before its memory can compete with it.
6. **The word is not much easier than the number** (A1 **failed** for 13 of
   20 runs). Bucket accuracy exceeds exact by 0.00 to 0.07, and for the
   models above 12B by about 0.02: their misses are mostly not the adjacent
   multiplier. A2's exact clause (quad below single) **held** for 9 of 10;
   its bucket clause failed everywhere, for the same reason.
7. **Position lean appears below 12B under table** (A5 **failed** for 6 of
   20 runs, all small models): gemma-3-4b predicts D on 10% of items where
   41% are D, and llama-3.2-3b on 11%. The small models are not falling
   back on the majority letter; they are answering something else.
8. **P1 held** for all ten (three-epoch ranges 0.010 to 0.050). **P3 held**
   on the ceiling model only: 0.954 under table. No open model reached 0.90
   under table; under rows the smallest to do so is qwen3-32b (A7's last
   clause, read against rows: 32B, not 12B).

Cost: the wallet went from $7.00 to $2.79 across every run in this ledger,
$4.21, under the addendum's $5 ceiling with the 32B rerun (D-012) left out.

### O-005
**Replication: the shape holds, and one clause of the knee was set-dependent**
llama-3.1-8b, gemma-3-12b, gemma-3-27b, qwen3-30b-a3b · `repl_s2_n400.csv` (dev 100 + 300 new, no overlap with the pinned set) · table x3 · 2026-08-29

Registered in REPLICATION.md (commit `3e389fc`) before any call. Source
`data/results/20260829_035523_analyze_replication.json`. This set's
majority baseline is **0.478** (the pinned set's is 0.408): the fresh pool
had no immunities left and few quads, so it is an easier set for a model
that leans on "1".

| params (active) | model | replication | 95% CI | pinned | shift | inside pinned CI |
|---|---|---|---|---|---|---|
| 8.0B | llama-3.1-8b | 0.326 | 0.282 to 0.373 | 0.279 | +0.047 | no, but under the 0.07 baseline allowance |
| 12.2B | gemma-3-12b | 0.480 | 0.431 to 0.529 | 0.507 | -0.027 | yes |
| 27.4B | gemma-3-27b | 0.649 | 0.601 to 0.694 | 0.617 | +0.032 | yes |
| 30.5B (3.3B) | qwen3-30b-a3b | 0.687 | 0.640 to 0.730 | 0.642 | +0.044 | yes |

- **R2 held.** 0.326 < 0.480 < 0.649; each step is 0.15 to 0.17, against
  epoch ranges of 0.018 to 0.045.
- **R3 held.** The MoE's interval overlaps 27B's (0.640 to 0.694 against
  0.601 to 0.694) and is nowhere near 8B's. Second set, same answer: the
  30B MoE with 3.3B active behaves like a 30B model.
- **R4 held**, all four. Three land inside their pinned intervals; 8B moves
  up 0.047 on an easier set, inside the 0.07 allowance the registration
  set for the baseline shift. No model moved more than 0.05 between two
  disjoint draws of 400.
- **R1 half failed.** 8B's interval is entirely below 0.478, as
  predicted. 12B's (0.431 to 0.529) straddles it. On the pinned set 12B
  beat its majority (0.507 against 0.408); here it ties. The claim that
  survives both sets is the weaker and more useful one: 12B is the first
  rung that reads the chart (quads 0.34 here against 0.10 for 8B, immune
  0.76 against 0.36), not the first rung that beats always answering "1".
  Whether a 12B model "beats the baseline" depends on how many neutral
  cells the item set has; whether it reads the chart does not.

What this does not do: it does not touch the `differs` cells or the
rows format, and it does not rerun the other six models. The knee's shape
is replicated; the exact accuracy at which a model "passes" is a property
of the item mix and is reported as such.

Cost of the replication and the D-012 rerun together: $1.51 ($2.79 to
$1.28). Project total $5.72, which is $0.72 over the addendum's $5
ceiling; the overrun is the two runs REPLICATION.md registered after the
ceiling was set, and is recorded here rather than absorbed.

### O-006
**The format gain, with a band**
llama-3.1-8b, gemma-3-12b, gemma-3-27b, qwen3-30b-a3b · rows format, pinned 400, three epochs · 2026-08-29

Registered in REVIEW.md (run 1) after an external review pointed out that the
paper's format result rested on one-epoch rows runs with no model-side band.
Source: `logs/rows3/`, analyzed to `data/results/`.

| model | table x3 | rows x3 | 95% CI | rows range | gain | sum of ranges | rows x1 (earlier) |
|---|---|---|---|---|---|---|---|
| llama-3.1-8b | 0.279 | 0.412 | 0.364 to 0.461 | 0.045 | +0.133 | 0.055 | 0.432 |
| gemma-3-12b | 0.507 | 0.646 | 0.598 to 0.691 | 0.028 | +0.139 | 0.048 | 0.642 |
| gemma-3-27b | 0.617 | 0.680 | 0.633 to 0.724 | 0.020 | +0.063 | 0.042 | 0.688 |
| qwen3-30b-a3b | 0.642 | 0.828 | 0.787 to 0.861 | 0.015 | +0.186 | 0.065 | 0.820 |

- **V1 held, 4 of 4.** Every gain exceeds the sum of the two epoch ranges,
  by 1.5x (27B) to 3x (30B-A3B).
- **V2 held, 4 of 4.** The earlier one-epoch rows numbers sit 0.004 to 0.020
  from the three-epoch means. One epoch was a fair estimate here; the paper
  now says so with the measurement rather than the assumption.

Cost about $1.05 (REVIEW.md budget: $7.28 available after a top-up).

### O-007
**The 235B MoE on a second host: the host moves it by 0.04, the ordering does not move**
qwen3-235b-a22b-2507 · DeepInfra (fp8) against GMICloud (fp8) · table, pinned 400, three epochs · 2026-08-29

Registered in REVIEW.md (run 2) after an external review noted that the
"235B MoE below 32B dense" ordering rested on one host for the model D-009 had
seen served by ten hosts. Source: `logs/host2/`, analyzed to `data/results/`.

| host | exact | 95% CI | range | quad | single | differs | host errors |
|---|---|---|---|---|---|---|---|
| GMICloud (pinned run) | 0.764 | 0.720 to 0.803 | 0.018 | 0.82 | 0.85 | 0.60 | 0 |
| DeepInfra (this run) | 0.725 | 0.679 to 0.766 | 0.013 | 0.62 | 0.87 | 0.55 | 0 |
| qwen3-32b dense, for comparison | 0.828 | 0.788 to 0.862 | 0.025 | 0.65 | 0.94 | 0.69 | 0 |

- **V3 held, at the edge.** 0.725 is inside GMICloud's interval, whose lower
  bound is 0.720. The registration said that if the second host landed
  above 0.828 the ordering would flip; it landed 0.04 lower instead.
- **What the 0.04 means.** Two hosts, same model id, same declared
  quantisation, differ by twice this model's epoch range and by about the
  gap between neighbouring rungs of the ladder. Quad accuracy moved from
  0.82 to 0.62. A single-host number for a model with many hosts carries
  roughly that much extra uncertainty, and the paper now says so instead
  of listing "host pinned" as if pinning removed the problem.
- **The ordering stands.** On both hosts the 235B MoE is below the 32B dense
  model, whose interval starts at 0.788. Contribution 2's total-parameter
  clause is restored with "on two hosts" attached.

Cost about $0.45. Review-round total (runs 1 and 2): about $1.50.

### D-013
**History rewritten to drop two internal files; three registration commit ids changed, no blob hash did**
git · 2026-08-29 · recorded

Before the repository goes public, `CHECKLIST.md` (the internal method
checklist walked against this eval) and `writeup/raw/20260829_review_fable.md`
(a reviewer's text, verbatim) were removed from every commit with
`git filter-branch --index-filter`, and the reflog and original refs were
dropped. Both files stay on disk, gitignored. `git log --all` on either path
now returns nothing.

A rewrite changes the id of every commit after the first touched one. The
registration files are pinned two ways in the README: by the blob hash of the
file (`git hash-object`, content-addressed, unchanged by the rewrite) and by
the commit that introduced it. The blob hashes are the binding ones and did
not move. The commit ids were remapped and the README and this ledger now
carry the new ones:

| file | blob (unchanged) | commit before | commit after |
|---|---|---|---|
| PLAN.md | 378f365 | 82c6bde | 82c6bde (predates the purged files) |
| ADDENDUM.md | b3eee1d | 48dd575 | 8717c65 |
| REPLICATION.md | (as recorded in README) | b5a081d | 3e389fc |
| REVIEW.md | 4faeb2b | c4dccd8 | 94313fe |

Anyone holding an old commit id can match it by commit message; the messages
were not changed.

### O-008
**Inside the lookup residual, and where in the list the misses are**
all ten models, table format, pinned 400 · `src/lookup_analysis.py` · 2026-08-29

Asked by the second review: `lookup` was the largest miss category at every
rung and a residual. Two automated reads of the reasoning, both from
`data/results/20260829_074749_lookup_pinned.json`.

**Stated typing.** For each lookup miss, the type words within 220 characters
after the first mention of the defender's name, with two exclusions a hand
check of 20 cases forced: the attacking type (the reasoning names it beside
the defender, "Ice attacks against Electric-type") and "normal" when followed
by "damage" or "effectiveness". Before the exclusions the classifier called
39% of llama-8b's lookup misses wrong-line; after, 4%, and every remaining
flagged case in a 13-case hand read was a genuine wrong typing ("Golduck,
which is Water/Psychic"; "Hypno's Psychic type, Ice and Rock are super
effective") or a partial one ("Beedrill: Bug").

| model | lookup misses | wrong typing | right typing | none stated |
|---|---|---|---|---|
| llama-3.2-1b | 329 | 0.45 | 0.25 | 0.30 |
| llama-3.2-3b | 468 | 0.16 | 0.54 | 0.30 |
| gemma-3-4b | 492 | 0.15 | 0.81 | 0.03 |
| llama-3.1-8b | 466 | 0.04 | 0.88 | 0.07 |
| gemma-3-12b | 311 | 0.08 | 0.92 | 0.00 |
| gemma-3-27b | 146 | 0.01 | 0.99 | 0.00 |
| qwen3-30b-a3b | 170 | 0.00 | 0.99 | 0.01 |
| qwen3-32b | 93 | 0.01 | 0.61 | 0.38 |
| qwen3-235b-a22b | 100 | 0.00 | 1.00 | 0.00 |
| gpt-5-nano | 24 | 0.00 | 0.46 | 0.54 |

Below 4B a sixth to a half of lookup misses have the wrong line (or a
recalled typing that is wrong); from 8B up almost all have the right line
and misread the chart. The "none stated" share at 32B and the ceiling is
reasoning that skips the typing sentence, not a failure.

**Position in the list.** Accuracy by dex bin (1-30, 31-60, 61-90, 91-120,
121-151): the first bin is best for eight of ten models, by 0.02 to 0.11
(llama-3.2-3b 0.33 against 0.18 to 0.27; gemma-3-27b 0.72 against 0.56 to
0.60); the other four bins are flat within each model. A primacy effect, no
middle dip. This is not the lost-in-the-middle shape; a 151-line list may be
too short to show it, and the small models fail across the whole list.

Not registered; reported as an observation. Cost: none (existing logs).

### O-009
**The recall condition: what the scores are without the reference**
all ten models, no chart, no typing list, pinned 400 x 3 epochs · `logs/recall/` · 2026-08-29

Registered in REVIEW2.md (run 1) before running. The prompt keeps the rules
and the question and drops the chart and the 151-line list; the model has
only what it remembers. Same hosts, same budgets (qwen3-32b at 1,024 tokens,
so 11% of its recall calls truncated; its recall number is a floor).

| model | recall | 95% CI | range | table | table minus recall | sum of ranges | W1 |
|---|---|---|---|---|---|---|---|
| llama-3.2-1b | 0.142 | 0.11 to 0.18 | 0.045 | 0.223 | 0.081 | 0.080 | held |
| llama-3.2-3b | 0.204 | 0.17 to 0.25 | 0.028 | 0.250 | 0.046 | 0.048 | failed by 0.002 |
| gemma-3-4b | 0.172 | 0.14 to 0.21 | 0.003 | 0.275 | 0.103 | 0.053 | held |
| llama-3.1-8b | 0.190 | 0.15 to 0.23 | 0.015 | 0.279 | 0.089 | 0.025 | held |
| gemma-3-12b | 0.266 | 0.22 to 0.31 | 0.030 | 0.507 | 0.241 | 0.050 | held |
| gemma-3-27b | 0.279 | 0.24 to 0.33 | 0.028 | 0.617 | 0.338 | 0.050 | held |
| qwen3-30b-a3b | 0.248 | 0.21 to 0.29 | 0.013 | 0.642 | 0.394 | 0.062 | held |
| qwen3-32b | 0.507 | 0.46 to 0.56 | 0.052 | 0.828 | 0.321 | 0.077 | held |
| qwen3-235b-a22b | 0.510 | 0.46 to 0.56 | 0.020 | 0.764 | 0.254 | 0.038 | held |
| gpt-5-nano | 0.665 | 0.62 to 0.71 | 0.028 | 0.954 | 0.289 | 0.050 | reported |

**W1 (the reference helps every open model)**: held for 8 of 9; llama-3.2-3b
misses the bar by 0.002 and is at chance with or without the chart.
**W3 (recall below the majority baseline at 8B and under)**: held, 4 of 4;
in fact recall is below 0.41 through 27B and the 30B MoE. Nobody under 32B
remembers the Generation I chart well enough to beat "always 1".

**W2 ("would have gotten it anyway")**, `src/recall_join.py`, from
`data/results/20260829_083017_recalljoin.json`: on the 329 items where the
Gen I and modern charts agree, the share of a model's table hits (majority
over epochs) that its recall run also hits:

| model | table hits (of 329) | also hit by recall | share |
|---|---|---|---|
| llama-3.2-1b | 56 | 4 | 0.07 |
| llama-3.2-3b | 67 | 33 | 0.49 |
| gemma-3-4b | 84 | 38 | 0.45 |
| llama-3.1-8b | 72 | 17 | 0.24 |
| gemma-3-12b | 174 | 65 | 0.37 |
| gemma-3-27b | 220 | 61 | 0.28 |
| qwen3-30b-a3b | 224 | 55 | 0.25 |
| qwen3-32b | 289 | 181 | 0.63 |
| qwen3-235b-a22b | 264 | 172 | 0.65 |
| gpt-5-nano | 326 | 271 | 0.83 |

Held below 0.5 at 8B and under (4 of 4), held above 0.5 at 32B and 235B,
failed at 27B (0.28) and the 30B MoE (0.25). So the prediction that memory
grows with size was half right: it grows within Qwen and at the ceiling, but
gemma-3-27b and qwen3-30b-a3b read the chart well while remembering almost
none of it. Their table scores are reading. At 32B and above, roughly
two-thirds of the hits would have come without the reference, so those
scores are a ceiling on reference-following and the differs stratum
remains the only clean measurement there. Cost about $0.92.

### O-010
**Shuffled options on the two leaning models; temperature 0 on the 12B rung**
`logs/shuffle/`, `logs/temp0/` · 2026-08-29

Registered in REVIEW2.md (runs 2 and 3). Shuffle, one epoch, pinned 400,
table format:

| model | fixed order: value "2" | shuffled: value "2" | fixed exact | shuffled exact | shuffled parse fail |
|---|---|---|---|---|---|
| gemma-3-4b | 0.68 | 0.63 | 0.275 | 0.263 | 0.00 |
| llama-3.2-3b | 0.56 | 0.44 | 0.250 | 0.205 | 0.09 |

**W4, value clause**: held, both within 10 points (4 and 12 points; llama
is at 12 by the raw model output and 8 by the scorer's mapped value, which
counts unparsed answers differently; the registered wording says "share of
answers", so the scorer's 0.48 is the number and it holds). The lean is to
the value "super effective", not to the letter E. **W4, letter clause**
("the most common answer letter under shuffle falls below 0.40"): not
measurable from the log, see D-014.

Temperature 0, gemma-3-12b, three epochs: 0.502, interval 0.453 to 0.550,
range 0.015, against 0.507 and range 0.020 at the host default. **W5 held**:
inside the default interval, range no larger. The host default was not
doing much on this rung. Cost about $0.40 for both.

### D-014
**Inspect's `multiple_choice(shuffle=True)` rewrites the log to look unshuffled and discards the reasoning**
harness (upstream) · 2026-08-29 · recorded, worked around

After a parsed answer, `pretend_we_didnt_shuffle` in
`inspect_ai/solver/_multiple_choice.py` replaces the user prompt with the
unshuffled rendering, replaces the completion with a bare `ANSWER: <letter
in original order>`, and the model event shares those objects, so the
written log carries no trace of the order the model saw or of its reasoning
(the 34 llama and 3 gemma samples with no parsed answer keep the shuffled
prompt, which is how the shuffle was confirmed to have happened at all).
The letter is mapped to the option's original position, so the *value* the
model chose survives and the exact score is right. What is lost: the shown
letter, so W4's letter clause cannot be scored, and the chain of thought, so
the error taxonomy cannot be run on these two logs. Anyone using the
`shuffle` parameter for a position-bias study should shuffle at dataset
load (`shuffle_choices`) instead, which the parameter's own deprecation
notice recommends and which leaves the log honest. The `run_ladder`
`--shuffle` flag stays as is for provenance; a note points here.
