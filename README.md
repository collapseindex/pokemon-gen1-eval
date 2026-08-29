# pokemon-gen1-eval

**A narrow capability eval, built the way a safety eval is built.**

v0.1.0 · Apache-2.0 · pre-registered in [PLAN.md](PLAN.md) (commit `82c6bde`, blob `378f365` via `git hash-object PLAN.md`; not edited after this line) · ledger in [FINDINGS.md](FINDINGS.md)

Six-way multiple choice on the damage multiplier when a move of one of the 15
Generation I types hits one of the original 151 Pokémon as typed in Red/Blue.
The answer key is generated from PokeAPI's tables, never typed. The chart and
the full typing list are in the prompt, so the task is find, look up, multiply:
nothing is recalled. Exact match is the score; how close a miss was is
reported beside it, never blended in.

## Status

Harness complete, no model called yet. Key built and verified on 26 known
cells; 400-item set pinned; 100-item dev set drawn disjoint from it; both
scorers, the metrics and the analysis script negative-tested with a mock
model. Five ledger entries, all against the harness or the plan, all found
before the first API call. Registered condition: chart and full typing list
in context, four models across four labs, three epochs, under $4.

## Why this task

The trap in a capability eval is breadth: a broad eval becomes a trivia game
and the number stops meaning anything. This one is narrow on purpose and
procedural on purpose. The answer is a lookup (two chart cells) and a multiply,
the key is derivable by code, and the Gen 1 chart differs from the modern chart
in exactly four cells, which gives a built-in test of whether a model follows
the table in front of it or the one it memorised.

What it cannot say is in PLAN.md and is as important as what it can.

## Build log

Every decision, in order, with what it caught. Ledger ids point into
[FINDINGS.md](FINDINGS.md). The rule throughout: nothing is measured until the
instrument has been shown to fail on a planted wrong answer.

### 1. Source, not memory (2026-08-29)

The type chart and 151 typings could have been typed from a wiki. They were
pulled from PokeAPI instead, because PokeAPI carries `type_efficacy_past.csv`
and `pokemon_types_past.csv`: the generation-specific overrides that make
"Red/Blue" mean Red/Blue (Magnemite pure Electric, Clefairy Normal, Ghost
doing nothing to Psychic). Seven CSVs frozen at commit `7af36d9`, sha256
beside them in `data/raw/`. A changed hash invalidates every number.

### 2. Derive the key, then check it by hand (D-001)

`src/key.py` builds 2,265 cells (15 x 151) with two answers each: the Gen 1
multiplier and the modern chart applied to the Gen 1 typing. 71 cells differ.
Then 26 known-answer cells were written from memory and compared. **Six were
wrong, and the key was right.** The "modern" column had been written against
modern typings (Magnemite as Electric/Steel) instead of the modern chart on
the Gen 1 typing, and Grass vs Gyarados is 2 x 1/2 = 1, not 1/2.

Lesson: the verification list is written by a person and is as fallible as the
thing it verifies. When they disagree, check both. This time the person lost.

### 3. Pin the item set before any run

400 cells, seed 0, stratified by difficulty: every `differs` cell (71, taken
whole), then immunities, 4x/¼x, ordinary dual-type, ordinary single-type. The
file is committed and a test holds the draw to it byte for byte.

Why stratify by answer difficulty and not by type: the question is whether the
model multiplies, and the strata are where multiplying matters. The cost of
that choice is item 6 below.

### 4. Negative-test the scorer

`inspect_ai.scorer.choice()` is a regex for `ANSWER: X` and a letter compare.
Before trusting it: a mock model answering the key scores 1.0, one answering
key+1 scores 0.0, one that stops mid-reasoning scores 0.0 with
`parse_failures` = 1.0. A scorer that cannot fail is not a scorer.

### 5. A dev set, declared (D-002)

PLAN.md pinned one set and said nothing about where the harness gets debugged.
Running the first live model on the registered set with an untried scorer
would have been the wrong order. 100 cells drawn from the 1,865 the pinned set
did not use; zero overlap by construction; no `differs` cells because the
pinned set holds all 71. Nothing measured on it is reported against a
prediction.

### 6. Attack types were not even (D-004)

Checked the class balance before running: answer classes are skewed to 1x
(41%) because most cells in the game are neutral, which is fine as long as
the majority baseline is printed beside every accuracy. But attack types in
the pinned set run 13 (Rock) to 45 (Bug), because the 71 `differs` cells are
all Bug/Poison/Ghost/Ice attacks, and the first dev draw had **no Bug and no
Poison attacks at all**, by chance. The pinned set stays (registered) and
per-type accuracy on it is read with n; the dev set was redrawn round-robin
across types within each stratum. Immunities and quads cannot be evened: 14
and 34 cells were left, and quad is half Grass because that is where the
game's 4x cells are.

Also caught here: a commit went through with a failing test because
`pytest | tail` hid the exit code. Amended. Run pytest bare.

### 7. The prompt (D-003)

Three changes before any run, each with a reason:

- **Reasoning allowed.** The first draft forced the whole response to be
  `ANSWER: X`, which turns condition B into a silent lookup-and-multiply and
  penalises a non-thinking model for a reason unrelated to the chart. Now
  Inspect's chain-of-thought template (think, then `ANSWER: X` on the last
  line), `max_tokens` pinned at 1024, and `parse_failures` reported so a
  truncation is its own number and not folded into "wrong". `-T cot=false`
  gets the silent version back as a later comparison.
- **The game's words as the mapping.** Red/Blue never printed a multiplier;
  it printed "super effective", "not very effective", "doesn't affect". The
  numbers are the community's. The system prompt gives the mapping and says
  that two types multiply, so 1/4 and 4 are legal answers, and says what to
  ignore (STAB, stats, move power, move-specific exceptions).
- **An unambiguous chart instruction.** Condition C says "use only the chart
  below, even where it disagrees with what you remember about the games."
  Without that, a miss on a `differs` cell could be a reasonable resolution
  of a conflict with the system prompt instead of an instruction-following
  failure, and P4 would not mean what it says.

Answer format stays numeric (0, 1/4, 1/2, 1, 2, 4) rather than the game's
words: the words collapse 4x into 2x and lose the multiply step, which is the
`quad` stratum and the point of the task.

### 8. Metrics that answer different questions

In the log, from Inspect: `accuracy`, `stderr`, `parse_failures`, and accuracy
by stratum, by answer class, by attack type. In `src/analyze.py`, from the
log: the epoch range (the noise band P1 is scored on), chance and majority
baselines on the same line as every accuracy, the confusion matrix in
multipliers (a 4 scored as 2 is a multiply failure; a 4 scored as 1 is a
lookup failure), the predicted-letter distribution (fixed A–F order makes
position bias measurable), and under `chart=modern` the split on `differs`
cells: followed the table / followed the prior / neither.

Analyze is negative-tested too: an always-"1" mock must come back with
accuracy equal to the majority share, only letter D predicted, and 0.0 on
immune and quad.

### 9. The budget did the multiplication the plan skipped (D-005)

Pricing the registered grid honestly: ~19,200 calls, ~$157 at list price,
against $7 of OpenRouter credit and a plan that said $30. Same failure as
data-deltas D-003 (a batch size nobody multiplied out). Rather than shrink
the item set, the question got narrower and better:

- **One condition.** The chart and the full 151-line typing list go in the
  system prompt; the question names only the attacker's type and the
  defender. Find it in the list, read two cells, multiply. That is the
  skill; nothing else is being measured. The recall conditions stay in the
  code as parameters and are not run, and P2/P4/P5/P6 retire unmeasured.
- **Four models, four labs**, chosen by price from OpenRouter's public list:
  Haiku 4.5 (batch route), GPT-5 nano, Gemini 2.5 Flash-Lite, Qwen3 235B.
  Three epochs each on the pinned 400, projected under $4 total. Cross-lab
  under one prompt is worth more here than Sonnet and Opus would have been.
- **Closeness, beside exact match and never blended with it.** Bucket match
  is the game's own word (doesn't affect / not very / normal / super
  effective); steps off is distance on the log2 scale, with immunity three
  steps from everything because it is a rule, not a magnitude. The reason
  to keep the two apart: a 2 answered as 4 is "close" by word and is exactly
  the multiply failure the quad stratum exists to catch. Three addendum
  predictions (A1 to A3) are registered in the ledger before any run.

Caught while wiring it: a task-level `metrics=` list applies to every
scorer, so `closeness` was silently reporting `accuracy`. Metrics now live
on each scorer. A dict-valued score surfaces as separate entries (`bucket`,
`steps`) in the log; the analyze script reads them from there.

### 10. Next

Haiku on the dev set, one epoch, about $0.30. Read in this order: parse
failures (want 0.00), then ten samples in the viewer to see whether the
reasoning finds the right line in the list before it reads the chart, then
the confusion matrix and the exact-vs-bucket gap. Only then the pinned set.

## Reproduce

```bash
pip install -r requirements.txt
python -m src.key                                   # build the key, print the 26 known cells
python -m src.sample --n 400 --seed 0               # pin the item set (reproduces the committed file)
python -m src.sample --n 100 --seed 1 --exclude items_s0_n400.csv --no-differs --tag dev --balance
pytest                                              # 15 tests, no API calls, about 40 s

# dev run, one condition, one model (needs ANTHROPIC_API_KEY)
inspect eval src/task.py -T chart=gen1 -T show_types=true -T items=dev_s1_n100.csv \
  --model anthropic/claude-haiku-4-5-20251001 --log-dir logs/dev
inspect view --log-dir logs/dev
python -m src.analyze --log-dir logs/dev
```

Defaults are the registered condition (`chart=gen1`, `show_types=list`).
Other parameters: `-T chart={none,gen1,modern}`, `-T show_types={list,inline,false}`,
`-T items=<csv in data/processed>`, `-T cot={true,false}`, `-T max_tokens=N`.

## How to read a run

1. `parse_failures` first. Anything above zero: open those samples. Truncation
   and format drift are harness problems, not model findings.
2. `accuracy` against the two baselines on the same line. A number below the
   majority share means the model is worse than answering "1" every time.
3. Strata. `single` is a one-cell lookup; `dual` is two cells and a multiply;
   `quad` and `immune` are where the multiply has to be right; `differs`
   (pinned set only) is where Gen 1 and modern disagree.
4. Confusion matrix. Where do the misses land?
5. Predicted letters. Fixed order means a lean toward D is a lean toward "1".
6. Epoch range before any comparison between conditions or models. If the
   difference is inside the band, it is not a difference.

## Layout

```
PLAN.md              the pre-registration; not edited after its hash is recorded
FINDINGS.md          the ledger: D defects, O observations, N negative results
src/key.py           Gen 1 chart + typings -> 2,265-cell key; the 26 known-answer cells
src/sample.py        stratified, seeded draw; --exclude, --no-differs, --balance for dev sets
src/task.py          the Inspect task: rules + chart + typing list, six fixed options, CoT, two scorers
src/analyze.py       logs -> one timestamped summary in data/results/
tests/               key, sampler, prompt, scorer and analyze, each negative-tested
data/raw/            PokeAPI CSVs frozen at commit 7af36d9, sha256 beside them
data/processed/      the key, its manifest, the pinned set, the dev set
data/results/        analyze output, one file per run of the script
logs/                Inspect logs (gitignored)
```

## Source and license

Type and typing data from [PokeAPI](https://github.com/PokeAPI/pokeapi)
(BSD-3, `data/raw/POKEAPI_LICENSE.md`). Pokémon and Pokémon character names
are trademarks of Nintendo. Code here is Apache-2.0.
