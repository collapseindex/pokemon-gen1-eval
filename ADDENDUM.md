# Pre-registration addendum

**Registered:** 2026-08-29, before any model call. Supersedes the conditions,
models, cost ceiling and predictions P2, P4, P5, P6 of [PLAN.md](PLAN.md),
for the reasons in FINDINGS D-005. PLAN.md itself is unchanged.
**Rule:** same as the plan. Not edited after its hash is recorded in the
README; a mistake here is a D entry in FINDINGS.md.

## The one condition

System prompt: the rules (the game's words for each multiplier; two types
multiply; ignore STAB, stats, move power, move-specific exceptions), the Gen 1
type chart as a 15 x 15 table, and the typing of all 151 Pokémon as a numbered
list. About 1,600 tokens, byte-identical for every item. The instruction says
to use only the chart given, even where it disagrees with memory.

Question: "A [Type]-type move hits [Pokémon]. What is the damage multiplier
from type effectiveness alone?" Six fixed options in fixed order: 0, 1/4, 1/2,
1, 2, 4. Reasoning allowed (chain-of-thought template, `ANSWER: X` on the last
line), `max_tokens` 1024.

The task is find (the defender in the list), look up (two chart cells),
multiply. No Pokémon knowledge is required or rewarded. A model that has
never heard of Golem can score 100%.

## The item set, as it is

`data/processed/items_s0_n400.csv`, unchanged since it was pinned. Counted
on 2026-08-29 before this file was written:

| dimension | what the set holds |
|---|---|
| answer class | 1x 163 (40.8%), 2x 69, 0x 63, 1/2 45, 1/4 31, 4x 29 |
| the game's word | normal 163 (40.8%), super 98, not very 76, doesn't affect 63 |
| **majority baseline** | **0.408** on exact and on bucket (both are "1" / "normal") |
| chance | 0.167 exact; 0.25 bucket |
| stratum | dual 132, single 99, differs 71, quad 49, immune 49 |
| attack type | 13 (Rock) to 45 (Bug); the four `differs` types (Bug, Ghost, Poison, Ice) are the top four |
| defender | 256 dual-typed, 144 single; Poison in 120 cells (33 of 151 Pokémon are Poison-typed) |
| coverage | 137 of 151 Pokémon appear; 14 never; Scyther 9 times, Kakuna 8 |
| target letter | D 163, E 69, A 63, C 45, B 31, F 29 |

Two consequences, stated now. Per-attack-type accuracy is confounded with the
`differs` stratum and is read with n, not as a finding on its own. The
`differs` stratum keeps its meaning under this condition: the chart in context
says one thing (0, 1, 2, 4) and the model's prior says another (2, 1/2, 1/2,
1/4 respectively), and the instruction says to use the chart; those 71 cells
measure whether the model reads the table it was given.

## Models

Four, one per lab, chosen by price from OpenRouter's public model list on
2026-08-29. Each runs the pinned 400 at three epochs at the provider default
temperature.

| model | $ in / out per M |
|---|---|
| `openrouter/anthropic/claude-haiku-4.5` | 1.00 / 5.00 (the `:batch` route, 0.50 / 2.50, if Inspect accepts it) |
| `openrouter/openai/gpt-5-nano` | 0.05 / 0.40 |
| `openrouter/google/gemini-2.5-flash-lite` | 0.10 / 0.40 |
| `openrouter/qwen/qwen3-235b-a22b-2507` | 0.087 / 0.35 |

Models may be added; none removed. A model whose parse-failure rate on the
dev set exceeds 5% has `max_tokens` raised (recorded) before it touches the
pinned set; if that does not fix it, the model is reported with its failure
rate and not dropped.

## Order of operations

1. Dev set (`dev_s1_n100.csv`, disjoint from the pinned set, no `differs`
   cells), Haiku, one epoch. Read: parse failures, ten samples in the viewer,
   confusion matrix. Nothing from this run is scored against a prediction.
2. Dev set, the other three models, one epoch each, same reading.
3. Pinned set, all four models, three epochs. `python -m src.analyze` on the
   logs is the results table.

## Metrics

Exact accuracy (primary) with stderr and the epoch range; bucket accuracy and
mean steps off (secondary, never averaged with exact); parse failures; exact
and bucket by stratum; exact by answer class and by attack type with n;
confusion matrix in multipliers; predicted-letter distribution. The two
baselines on the same line as every accuracy.

## Predictions

Carried from PLAN.md: **P1** (epoch range of exact accuracy between 1 and 5
points for every model) and **P3**, read as: the best model scores at least
95% exact.

- **A1, the word is easier than the number.** For every model, bucket
  accuracy exceeds exact accuracy by at least 3 points, and at least half of
  the exact misses are one step off (2 for 4, 1/2 for 1/4, 1 for 2, 1 for
  1/2).
- **A2, the multiply is the failure.** For every model, exact accuracy on
  `quad` is below `single` by more than the epoch range, while bucket
  accuracy on `quad` is within the epoch range of bucket accuracy on
  `single`.
- **A3, the list is found.** Misses explained by reading another Pokémon's
  line (the predicted multiplier equals the key for a different Pokémon that
  the reasoning names or types) are under 5% of items for every model. Hand
  scored on the misses in the viewer; the count is reported.
- **A4, the table beats the prior, mostly.** For the best model, exact
  accuracy on `differs` is within the epoch range of `dual`. For the smallest
  model it is below `dual` by more than the range: the memorised chart leaks
  into a lookup it was told not to use.
- **A5, no position lean.** For every model, the share of predicted letter D
  is within 10 points of the target share of D (40.8%).

## Cost ceiling

$5 of the $7 for everything above, including the dev runs. If it is
exceeded, the run stops where it is and the shortfall is a ledger entry.

## What this cannot say

Nothing about recall: the conditions that measured it are not run. Nothing
about any model's knowledge of Pokémon. Nothing about the modern chart or
later generations. Nothing about free-form answering. Per-stratum n is as low
as 49 (quad, immune), so stratum claims carry a band roughly twice the
overall one. Four models at three epochs is a small grid; a difference
between two models inside both their ranges is not a difference.
