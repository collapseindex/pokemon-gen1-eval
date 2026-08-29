# Second review round, registered

**Registered:** 2026-08-29, after a second external review of the draft and
before any of the runs below. Same rule as the other registration files: not
edited after its hash is recorded in the README; a mistake here is a D entry.
Credit available: $5.78. Budget for this round: $2.00.

## Run 1: the recall condition

The paper's title claim is reference-following, and every score so far was
measured with the reference in the prompt. Nothing separates reading the
chart from remembering it except the 71 contradicted items. Run the original
plan's condition A (no chart, no typing list; the question names attacker and
defender only) on the pinned 400 at three epochs for all ten models, same
hosts and budgets. The prompt is about 250 tokens, so the pass costs about
$0.90.

- **W1, the reference helps every open model.** For each of the nine open
  models, table accuracy minus recall accuracy exceeds the sum of the two
  epoch ranges. (The ceiling model is reported, not predicted.)
- **W2, "would have gotten it anyway" grows with size.** On the 329 pinned
  items where the Generation I and modern charts agree, define for each
  model the share of its table-format hits that its recall run also hits
  (matched by item, majority over epochs). That share is below 0.5 for
  every rung at 8B and under, and above 0.5 for every rung from 27B up.
- **W3, recall does not clear the majority baseline below 12B.** For every
  rung at 8B and under, recall accuracy is below 0.408.

## Run 2: shuffled option order on two small models

The paper says gemma-3-4b and llama-3.2-3b lean toward the value "2" rather
than the letter E; with a fixed order those are the same claim. Rerun the
table format on the pinned 400 at one epoch for both with the option order
shuffled per item (Inspect's `multiple_choice(shuffle=True)`; the scorers
read option values, not positions). About $0.20.

- **W4, it is a value lean.** For each of the two, the share of answers
  whose value is "2" under shuffle is within 10 points of the fixed-order
  share (0.68 and 0.56), and the most common answer *letter* under shuffle
  falls below 0.40.

## Run 3: temperature 0 on one rung

Temperature is the host's default and is not exposed. Rerun gemma-3-12b,
table, three epochs, on the pinned 400 with temperature 0 requested. About
$0.22.

- **W5, the default was not doing much.** The temperature-0 mean lies inside
  the default-temperature interval (0.459 to 0.556), and its three-epoch
  range is at most the default run's (0.020).

## Not run

gemma-3-1b-it is not served on OpenRouter as of this date, so the Gemma
within-family curve stays at three points.

## What these do not do

They do not add a second family of MoE models, do not pin temperature across
the ladder, and do not hand-score the lookup residual (that is an analysis
item and is reported in the ledger, not predicted here).
