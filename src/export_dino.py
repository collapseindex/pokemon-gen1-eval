"""Export an item set in dinostomp's item shape (input / target / choices),
built by the task's own sample builder so the audited text is what the model
sees.

    python -m src.export_dino [items_s0_n400 dev_s1_n100 ...]
"""

from __future__ import annotations

import json
import sys

from .task import PROCESSED, build_samples, load_items


def main() -> None:
    names = sys.argv[1:] or ["items_s0_n400", "dev_s1_n100"]
    for name in names:
        rows = load_items(PROCESSED / f"{name}.csv")
        out = PROCESSED / f"{name}_dino.jsonl"
        with out.open("w", encoding="utf-8", newline="\n") as fh:
            for s in build_samples(rows, "gen1", "list"):
                record = {"id": s.id, "input": s.input, "target": s.target, "choices": s.choices, "stratum": s.metadata["stratum"]}
                fh.write(json.dumps(record) + "\n")
        print("wrote", out.name)


if __name__ == "__main__":
    main()
