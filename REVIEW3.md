# Third review: two runs, registered before spending

Written 2026-08-29 after a third external review of the submission draft
(`writeup/raw/20260829_review3_fable.md`, kept out of the repository), before
any of the runs below. Same rules as PLAN.md: this file is hashed in the README
and not edited afterwards; a mistake in it is a ledger entry.

## What the review established without a run (O-011)

The two Qwen mixtures on the ladder are the `-2507` *instruct* variants:
zero reasoning blocks and zero truncation in 1,200 calls each, about 167
output tokens per call. `qwen3-32b` is the hybrid model and reasoned on every
call (618 output tokens on average, one truncation in 1,200 at 4,096). So the
D-012 artefact does not touch the MoEs, but the 0.19 gap between the 30B-A3B
and the 32B is sparse-versus-dense *and* thinking-versus-not, and the paper
has not separated them. Run 2 does.

## Run 1: a relabelled chart

The reference is memorised, and the 71 contradicted cells are the only
measurement of reading against memory. Rerun the table format with the 15
type names relabelled by a seeded derangement (`src.key.type_permutation(0)`):
the chart is shown under the new names, the 151-line typing list uses the new
names, the question names the attacker by its new name, and every cell keeps
its value, so the key is unchanged and a test holds the two renderings equal
cell for cell. Memory of the real chart is then useless or harmful. All ten
models, pinned 400, one epoch, same hosts and budgets. About $0.80.

- **X1, reading scores stand.** For every open model at 27B and under, and
  the 30B MoE, the relabelled score lies within 0.05 of its table
  three-epoch mean (their recall share of table hits was 0.07 to 0.49, so
  little was memory).
- **X2, the memory share shows at the top.** `qwen3-32b`, `qwen3-235b-a22b`
  and `gpt-5-nano` each fall by more than 0.05 (their recall-also-hit share
  was 0.63 to 0.83).
- **X3, the order survives.** 8B < 12B < 27B under the relabelled chart, each
  step larger than the 8B and 12B table epoch ranges summed (0.030).

## Run 2: the 32B without thinking

`qwen3-32b`, table, three epochs, pinned 400, DeepInfra, 1,024 tokens, with
reasoning disabled through the provider (`reasoning: {enabled: false}` on the
request; if the host ignores the flag and reasoning blocks still appear, the
run is discarded and reported as such, not scored). About $0.35.

- **X4, density matters.** The non-thinking 32B still exceeds the 30B-A3B
  (0.642) by more than the sum of the two epoch ranges.
- **X5, thinking matters.** The non-thinking 32B falls below its thinking
  score (0.828) by more than the sum of the two epoch ranges.

If X4 fails, the paper's MoE paragraph has to say the 30B-A3B versus 32B gap
was thinking, not density. If X5 fails, thinking was not doing the work at
this rung.

## Not run

A uniformly sampled third item set (review concern 4): $3.90 of credit
covers runs 1 and 2 and not a third pass over ten models. Recorded as a
limitation.
