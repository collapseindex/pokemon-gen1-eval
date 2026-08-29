# pokemon-gen1-eval

**A narrow capability eval, built the way a safety eval is built.**

v0.1.0 · Apache-2.0 · pre-registered in [PLAN.md](PLAN.md) (commit `82c6bde`, blob `378f365` via `git hash-object PLAN.md`; not edited after this line) · ledger in [FINDINGS.md](FINDINGS.md)

Six-way multiple choice on the damage multiplier when a move of one of the 15
Generation I types hits one of the original 151 Pokémon as typed in Red/Blue.
The answer key is generated from PokeAPI's tables, never typed. Four conditions
separate recall of the typings, recall of the chart, applying a chart that is
given, and following a given chart that contradicts the memorised one.

## Status

Scaffold only. No model has been called. Key built and hand-verified on 26
known cells; item set pinned; scorer negative-tested with a mock model.

## Reproduce

```bash
pip install -r requirements.txt
python -m src.key                       # build data/processed/gen1_key.csv, print the known-answer cells
python -m src.sample --n 400 --seed 0   # pin the item set
pytest                                  # key, sampler, prompt, scorer (mock model, no API calls)

# one condition, one model (needs ANTHROPIC_API_KEY)
inspect eval src/task.py -T chart=gen1 -T show_types=true --model anthropic/claude-haiku-4-5-20251001 --epochs 3
inspect view                            # the log viewer
```

Conditions are `-T chart={none,gen1,modern} -T show_types={true,false}`; see
PLAN.md for the four that are registered.

## Layout

```
PLAN.md              the pre-registration; not edited after its hash is recorded
FINDINGS.md          the ledger: D defects, O observations, N negative results
src/key.py           Gen 1 chart + typings -> 2,265-cell key; known-answer cells
src/sample.py        stratified, seeded item draw
src/task.py          the Inspect task: prompt, six fixed options, choice() scorer
tests/               known answers, perturbed-chart negative test, mock-model scorer test
data/raw/            PokeAPI CSVs frozen at commit 7af36d9, sha256 beside them
data/processed/      the key, its manifest, the pinned item set
data/results/        run summaries
logs/                Inspect logs
```

## Source and license

Type and typing data from [PokeAPI](https://github.com/PokeAPI/pokeapi)
(BSD-3, `data/raw/POKEAPI_LICENSE.md`). Pokémon and Pokémon character names
are trademarks of Nintendo. Code here is Apache-2.0.
