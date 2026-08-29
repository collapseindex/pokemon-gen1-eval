# Pre-registration: Generation I type matchups as a capability eval

**Registered:** 2026-08-29, before any model call.
**Rule:** this file is not edited after its commit hash is recorded in the README.
A mistake in it is a D entry in FINDINGS.md, not a fix here.

## Question

On a narrow, procedural task with a code-generated answer key (the damage
multiplier when a move of type X hits one of the original 151 Pokémon as typed
in Red/Blue), how much of a model's accuracy is recall of the chart and typings,
how much is applying a table it is given, and does it follow a table that
contradicts its prior?

The point is not Pokémon. It is to build one capability eval end to end with
the same discipline as a safety eval: a key nobody typed, a scorer that was
shown to fail, a noise band measured before any comparison, and a claim no
wider than the instrument.

## The instrument

- **Universe.** 15 Generation I types x 151 Pokémon as typed in Generation I
  (PokeAPI `pokemon_types.csv` + `pokemon_types_past.csv`): 2,265 cells.
- **Chart.** PokeAPI `type_efficacy.csv` with `type_efficacy_past.csv` rows
  for Generation I applied: Bug→Poison 2x, Poison→Bug 2x, Ghost→Psychic 0x,
  Ice→Fire 1x. The Ghost→Psychic 0x is the shipped game's behaviour, not the
  intended one; this eval scores the shipped game. Source frozen at PokeAPI
  commit `7af36d9`, hashes in `data/raw/`.
- **Item.** "A [Type]-type move hits [Pokémon]. What is the damage multiplier
  from type effectiveness alone?" Six fixed options in fixed order:
  0, 1/4, 1/2, 1, 2, 4. Never shuffled, so position bias is a property of the
  model, not the item.
- **Item set.** 400 cells, seed 0, stratified: every cell where the Gen 1 and
  modern charts disagree (taken whole), then 15% immunities, 15% 4x or 1/4x,
  40% ordinary dual-type, 30% ordinary single-type of the remainder.
  Pinned in `data/processed/items_s0_n400.csv` before any run.
- **Scorer.** Exact letter match (`inspect_ai.scorer.choice`). Negative-tested:
  a mock model answering the key scores 1.0, one answering key+1 scores 0.0.

## Conditions, same 400 items

| id | chart in context | defender typing shown | scored against | what it isolates |
|---|---|---|---|---|
| A | none | no | Gen 1 | pure recall (typing and chart from memory) |
| D | none | yes | Gen 1 | chart recall only |
| B | Gen 1 | yes | Gen 1 | pure procedure: lookup and multiply |
| C | modern | yes | **the provided (modern) chart** | does it follow the table or its prior? |

Every model runs every condition with `epochs=3` at temperature 1 (the
default, so the band is the deployment band) and once at temperature 0.

## Models

Three, one per tier, chosen for price: `anthropic/claude-haiku-4-5-20251001`,
`anthropic/claude-sonnet-5`, `anthropic/claude-opus-5`. Others may be added;
none removed.

## Metrics

Accuracy overall and per stratum, per condition, per model: mean over
epochs and the epoch range (max minus min) as the noise band. Two baselines
reported beside every number: chance (1/6) and always-"1" (the majority
class, whose share is in `key_manifest.json`).

## Predictions

- **P1, noise band.** For every (model, condition), the range of overall
  accuracy across three epochs is at least 1 point and at most 5 points.
- **P2, typing is the recall bottleneck.** D minus A is positive for every
  model and at least as large as B minus D. That is: giving the typing helps
  more than giving the chart, because the 15x15 chart is better memorised than
  151 typings.
- **P3, procedure gain.** B is at least 95% for the largest model and B minus
  A is positive for every model, by more than the noise band.
- **P4, prior override.** On the `differs` stratum under C, accuracy against
  the provided chart is below accuracy on the non-differs strata under C by
  more than the noise band, for every model. Models will drift toward the
  memorised chart on the cells where the table contradicts it.
- **P5, immunities and quads.** Under A, the `immune` and `quad` strata score
  below `single` for every model; multiplying two factors is harder than
  reading one.
- **P6, the bug cell.** Ghost→Psychic (0x shipped, 2x intended) is the single
  worst attack-type row under A and D for every model.

## What this cannot say

Nothing about code, maths, or reasoning at large. Nothing about the modern
chart or later generations. Nothing about a model's Pokémon knowledge beyond
type effectiveness (no stats, moves, abilities). Nothing about free-form
answering: the six-option format removes the "explain" part of the task.
With 400 items the per-stratum n is as low as ~50, so stratum-level claims
carry a wider band than the overall number; the `differs` stratum is exactly
as big as the game made it.

## Cost ceiling

Three models x four conditions x four runs x 400 items, of which the chart
conditions carry a ~1.5k-token table per item. Under $30 total, or the run
is stopped and the shortfall is a ledger entry.
