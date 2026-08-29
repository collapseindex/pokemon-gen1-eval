# Replication, registered

**Registered:** 2026-08-29, after the ladder (O-004) and before any call on
this set. Same rule as PLAN.md and ADDENDUM.md: not edited after its hash is
recorded in the README; a mistake here is a D entry.

## What is being replicated

O-004's headline: with the chart as a grid, the knee sits between 8B and 12B
total parameters, and the 30B MoE with 3.3B active scores with the 27B and
32B dense models. Those are claims about four rungs, so the replication runs
those four on items none of them has seen.

## The set

`data/processed/repl_s2_n400.csv`, 400 items, zero overlap with the pinned
set, built as:

- the 100 dev items (`dev_s1_n100.csv`, seed 1). They were used to debug
  the harness with Haiku, nano, Gemini Flash-Lite, Qwen 235B, Llama 3B and
  Gemma 4B (O-001 to O-003); **none of the four models below has ever been
  run on them**;
- plus 300 new cells, seed 2, drawn round-robin by attack type from the
  1,765 cells neither the pinned set nor the dev set used.

Why not 400 fresh cells: the pinned set holds every one of the 77 immunity
cells and all 71 `differs` cells, and the dev set took 14 of the remaining
zeros, so the unused pool has no immunities and 19 quads. A fresh 400 would
be almost entirely ordinary cells and would make the majority baseline
easier to beat than on the pinned set. The dev items bring 14 immunities and
15 quads back in.

Composition, counted before this file was written: dual 232, single 120,
quad 34, immune 14, no `differs`. Answer classes: 1x 191 (**majority
baseline 0.478**, higher than the pinned set's 0.408), 2x 90, 1/2 71, 1/4
23, 0 14, 4x 11. Attack types 22 to 37 per type.

## Runs

Table format only (the registered format), three epochs, the pinned host and
token budget from `src/models.py`:

| params (active) | model | pinned-set exact, 95% CI |
|---|---|---|
| 8.0B | llama-3.1-8b-instruct | 0.279 [0.237, 0.325] |
| 12.2B | gemma-3-12b-it | 0.507 [0.459, 0.556] |
| 27.4B | gemma-3-27b-it | 0.617 [0.568, 0.663] |
| 30.5B (3.3B) | qwen3-30b-a3b-instruct-2507 | 0.642 [0.594, 0.688] |

About $0.90. Logged to `logs/replication/`.

Alongside, and not part of the replication: qwen3-32b, table, three epochs,
on the **pinned** set at `max_tokens` 4,096, the D-012 rerun. Its result
replaces the 0.697 floor in the curve if its parse-failure rate is under 5%;
otherwise both numbers are reported.

## Predictions

Intervals are 95% Wilson over 400 items, computed by `src/stats.py`.

- **R1, the knee replicates.** On this set, llama-3.1-8b's interval lies
  entirely below the majority baseline (0.478) and gemma-3-12b's interval
  lies entirely above it.
- **R2, the order replicates.** 8B < 12B < 27B on exact accuracy, each
  step larger than the two epoch ranges.
- **R3, the MoE stays with the big ones.** qwen3-30b-a3b's interval
  overlaps gemma-3-27b's and does not overlap llama-3.1-8b's.
- **R4, stability across item draws.** Each model's replication accuracy
  falls inside its pinned-set interval, or the difference is explained by
  the baseline shift (this set's majority is 0.07 higher, so a model that
  leans on "1" may rise by up to that much). A model that moves by more
  than 0.07 outside its interval is a finding about item sensitivity, not
  noise.

## What this cannot say

Nothing about the `differs` cells or the prior-override reading (A4), since
none are left to draw. Nothing about rows format. Nothing about the models
not rerun; nano, 235B, 32B and the three smallest keep their single pinned
result. Four models is a check on the shape of the knee, not a second
ladder.
