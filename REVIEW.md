# Review-driven runs, registered

**Registered:** 2026-08-29, after an external review of the paper draft and
before either run. Same rule as PLAN.md, ADDENDUM.md and REPLICATION.md: not
edited after its hash is recorded in the README; a mistake here is a D entry.

The review (filed verbatim in `writeup/raw/20260829_review_fable.md`) made two
points that money can answer. Credit available: $7.28.

## Run 1: rows format at three epochs on the four knee models

The paper's format result rests on rows runs at one epoch, with no model-side
noise band. Rerun the rows format on the pinned 400 at three epochs for the
four rungs the replication already covered, same hosts and budgets as
`src/models.py`:

| model | table (3 ep.) | rows (1 ep., existing) |
|---|---|---|
| llama-3.1-8b-instruct | 0.279 | 0.432 |
| gemma-3-12b-it | 0.507 | 0.642 |
| gemma-3-27b-it | 0.617 | 0.688 |
| qwen3-30b-a3b-instruct-2507 | 0.642 | 0.820 |

About $1.05. Logged to `logs/rows3/`.

- **V1, the format gain has a band and clears it.** For each of the four, the
  three-epoch rows mean minus the three-epoch table mean exceeds the sum of
  the two epoch ranges.
- **V2, the one-epoch rows number was inside the band.** For each of the four,
  the existing one-epoch rows accuracy lies within the three-epoch rows range
  or within 0.03 of the three-epoch rows mean.

## Run 2: qwen3-235b-a22b on a second host

The paper's "235B MoE below 32B dense" ordering rests on one host (GMICloud,
fp8), for a model the ledger (D-009) had already seen served by ten hosts of
unknown quantisation on the dev set. Rerun the table format, three epochs, on
the pinned 400 through DeepInfra (fp8, the host most of the ladder uses), with
fallbacks disabled. About $0.45. Logged to `logs/host2/`.

- **V3, the host is not the story.** DeepInfra's three-epoch mean lies inside
  GMICloud's 95% interval (0.720 to 0.803). If it does, the ordering
  235B-A22B < 32B dense stands with two hosts behind it. If it lies above
  0.828 (the 32B dense number), the ordering flips and the paper says so.
  Anything in between is reported as "host-dependent" and the claim is
  withdrawn from the contributions.

## What these do not do

They do not add a recall condition, do not pin temperature (provider defaults
stay, and are reported as such), and do not touch the other five rungs. The
review's other points are text and analysis changes and are answered in the
ledger, not here.
