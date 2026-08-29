# Fourth registration: the Qwen3 dense rungs

Written 2026-08-29 after a sixth external read of the submission draft,
before the run below. Same rules as PLAN.md: hashed in the README, never
edited afterwards; a mistake here is a ledger entry.

## Why

The mixture-of-experts claim rests on two points, both confounded: the 30B-A3B
against the 27B is cross-family and cross-host, and against the 32B it is
sparse-versus-dense entangled with thinking-versus-not (O-011, D-016). Qwen3
ships dense 8B and 14B hybrid models (no 4B is served on OpenRouter as of
today). Running them gives a within-family dense ladder 8B, 14B, 32B in the
32B's own regime (reasoning on, 4,096 tokens), a second confound-free step
beside Gemma 4B to 12B, and a same-family answer to "does 3.3B active behave
like 30B dense or like 3B dense".

## Run 1

`qwen/qwen3-8b` (Alibaba, the only host; quantisation not reported) and
`qwen/qwen3-14b` (DeepInfra fp8, the 32B's host), table format, three
epochs, pinned 400, 4,096 tokens, reasoning at the host default (on), into
`logs/qwen_dense/`. About $1.40 of the $2.44 left.

- **Y1, the dense ladder is monotone.** 8B < 14B < 32B on exact accuracy,
  each step larger than the paired 95% interval's half-width (paired
  bootstrap over items, `src.paired`).
- **Y2, the 3.3B-active mixture behaves like a large dense model.**
  qwen3-30b-a3b (0.642, no thinking) scores at or above the thinking 14B
  dense model, minus the sum of their epoch ranges.
- **Y3, thinking and family beat size at 8B.** The thinking qwen3-8b exceeds
  llama-3.1-8b (0.279) by more than the sum of the two epoch ranges.
- **Y4, the same knee.** qwen3-8b under table is at or below the majority
  baseline (0.408) and qwen3-14b is above it, by more than each one's
  three-epoch range.

## What this does not do

It does not remove the thinking confound from the 30B-A3B versus 32B
comparison (that needs a host that honours reasoning-off, D-016) and it
does not add the uniform third item set; $1 of credit remains after this
run and the deadline is three hours away.
