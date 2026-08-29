"""Run the ladder on the pinned set, bottom up, one host per model.

    python -m src.run_ladder                 # table x3 epochs for every model, then rows x1
    python -m src.run_ladder --only 3b,4b    # substring match on model id
    python -m src.run_ladder --formats rows  # just the rows pass

Every run is one `inspect eval` subprocess with the model's pinned host and
max_tokens from the registry. A run that fails leaves its log and the
ladder continues; nothing is retried silently. Logs go to logs/pinned/.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .models import LADDER

ROOT = Path(__file__).resolve().parent.parent
INSPECT = ROOT / ".venv" / "Scripts" / "inspect.exe"
ITEMS = "items_s0_n400.csv"
EPOCHS = {"table": 3, "rows": 1}


def run_one(model, fmt: str, log_dir: Path) -> int:
    cmd = [
        str(INSPECT), "eval", "src/task.py",
        "-T", f"items={ITEMS}", "-T", f"chart_format={fmt}", "-T", f"max_tokens={model.max_tokens}",
        "--model", model.inspect_model, "-M", model.provider_arg,
        "--epochs", str(EPOCHS[fmt]), "--log-dir", str(log_dir), "--display", "plain",
    ]
    print(f"\n### {model.id} [{fmt}] x{EPOCHS[fmt]} host={model.host} quant={model.quant} max_tokens={model.max_tokens}", flush=True)
    proc = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    tail = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip() and "warning" not in l.lower()]
    for line in tail:
        if line.startswith(("accuracy", "parse_failures", "Log:", "logs/")) or "Error" in line or "error" in line:
            print("   ", line.strip(), flush=True)
    errored = any(("Error code:" in l or "Traceback" in l) for l in tail)
    code = proc.returncode or (1 if errored else 0)
    print(f"    exit {code}{' (error trace in output)' if errored and not proc.returncode else ''}", flush=True)
    return code


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="comma-separated substrings of model ids")
    ap.add_argument("--formats", default="table,rows")
    ap.add_argument("--log-dir", default="logs/pinned")
    a = ap.parse_args()
    log_dir = ROOT / a.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    wanted = [m for m in LADDER if not a.only or any(s in m.id for s in a.only.split(","))]
    failures = []
    for fmt in a.formats.split(","):
        for m in wanted:
            if run_one(m, fmt, log_dir) != 0:
                failures.append((m.id, fmt))
    print("\nladder done;", "all runs exited 0" if not failures else f"failed: {failures}", flush=True)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
