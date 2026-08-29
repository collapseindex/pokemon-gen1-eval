"""Draw the scaling curve from the latest curve CSV. The CSV is the record;
this only renders it.

    python -m src.plot_curve [data/results/<stamp>_curve_pinned.csv]

Writes data/results/<stamp>_curve_pinned.svg: exact accuracy against total
parameters (log axis), one series per chart format, 95% Wilson CI bars,
family written beside each point, the majority and chance baselines, and the
ceiling model as a dashed line since it has no parameter count.
"""

from __future__ import annotations

import csv
import math
import sys
from pathlib import Path

from .key import ROOT

RESULTS = ROOT / "data" / "results"

# Reference palette, light mode, validated (dataviz skill): slot 1 blue, slot 2 orange.
SERIES = {"table": "#2a78d6", "rows": "#eb6834"}
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e6e5e1"
SURFACE = "#fcfcfb"

W, H = 880, 520
L, R, T, B = 70, 30, 40, 70


def load(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _f(v: str) -> float | None:
    try:
        x = float(v)
        return None if math.isnan(x) else x
    except (TypeError, ValueError):
        return None


def render(rows: list[dict], majority: float, chance: float) -> str:
    pts = [r for r in rows if _f(r["params_total_b"]) is not None]
    ceilings = [r for r in rows if _f(r["params_total_b"]) is None and r["model"]]
    xs = [math.log10(_f(r["params_total_b"])) for r in pts]
    x0, x1 = min(xs) - 0.1, max(xs) + 0.1

    def X(p: float) -> float:
        return L + (math.log10(p) - x0) / (x1 - x0) * (W - L - R)

    def Y(a: float) -> float:
        return T + (1 - a) * (H - T - B)

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="system-ui, -apple-system, Segoe UI, sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="{SURFACE}"/>']
    # y grid
    for a in (0, 0.2, 0.4, 0.6, 0.8, 1.0):
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" stroke="{GRID}" stroke-width="1"/>')
        out.append(f'<text x="{L-8}" y="{Y(a)+4:.1f}" text-anchor="end" fill="{INK2}">{a:.0%}</text>')
    # x ticks
    for p in (1, 3, 10, 30, 100, 300):
        if x0 <= math.log10(p) <= x1:
            out.append(f'<line x1="{X(p):.1f}" x2="{X(p):.1f}" y1="{T}" y2="{H-B}" stroke="{GRID}" stroke-width="1"/>')
            out.append(f'<text x="{X(p):.1f}" y="{H-B+18}" text-anchor="middle" fill="{INK2}">{p}B</text>')
    out.append(f'<text x="{(L+W-R)/2:.0f}" y="{H-B+40}" text-anchor="middle" fill="{INK2}">total parameters (log scale)</text>')
    out.append(f'<text transform="translate(16 {(T+H-B)/2:.0f}) rotate(-90)" text-anchor="middle" fill="{INK2}">exact accuracy, pinned 400 items</text>')
    # baselines
    for a, label in ((majority, f"always “1” {majority:.0%}"), (chance, f"chance {chance:.0%}")):
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" stroke="{INK2}" stroke-width="1" stroke-dasharray="2 4"/>')
        out.append(f'<text x="{W-R-4}" y="{Y(a)-5:.1f}" text-anchor="end" fill="{INK2}">{label}</text>')
    # ceilings
    for r in ceilings:
        a = _f(r["exact"])
        if a is None:
            continue
        col = SERIES.get(r["format"], INK2)
        out.append(f'<line x1="{L}" x2="{W-R}" y1="{Y(a):.1f}" y2="{Y(a):.1f}" stroke="{col}" stroke-width="1.5" stroke-dasharray="6 4"/>')
        out.append(f'<text x="{L+4}" y="{Y(a)-5:.1f}" fill="{INK2}">{r["model"].split("/")[-1]} ({r["format"]}) {a:.0%}, size undisclosed</text>')
    # series
    for fmt in ("table", "rows"):
        s = sorted([r for r in pts if r["format"] == fmt], key=lambda r: _f(r["params_total_b"]))
        if not s:
            continue
        col = SERIES[fmt]
        path = " ".join(f'{"M" if i == 0 else "L"}{X(_f(r["params_total_b"])):.1f},{Y(_f(r["exact"])):.1f}' for i, r in enumerate(s))
        out.append(f'<path d="{path}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
        # label placement: points whose x sits within 30px of a neighbour form a
        # cluster; inside a cluster labels go below / right / above in turn
        groups: list[list[int]] = []
        for i, r in enumerate(s):
            x = X(_f(r["params_total_b"]))
            if groups and x - X(_f(s[groups[-1][-1]]["params_total_b"])) < 30:
                groups[-1].append(i)
            else:
                groups.append([i])
        place: dict[int, str] = {}
        for g in groups:
            for k, i in enumerate(sorted(g, key=lambda i: _f(s[i]["exact"]))):
                place[i] = ("below", "right", "above")[k % 3] if len(g) > 1 else "below"
        for r in s:
            x, a = X(_f(r["params_total_b"])), _f(r["exact"])
            lo, hi = _f(r["exact_ci95_low"]), _f(r["exact_ci95_high"])
            if lo is not None and hi is not None:
                out.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{Y(hi):.1f}" y2="{Y(lo):.1f}" stroke="{col}" stroke-width="1.5"/>')
                out.append(f'<line x1="{x-3:.1f}" x2="{x+3:.1f}" y1="{Y(hi):.1f}" y2="{Y(hi):.1f}" stroke="{col}" stroke-width="1.5"/>')
                out.append(f'<line x1="{x-3:.1f}" x2="{x+3:.1f}" y1="{Y(lo):.1f}" y2="{Y(lo):.1f}" stroke="{col}" stroke-width="1.5"/>')
            shape = "moe" if _f(r["params_active_b"]) and _f(r["params_active_b"]) < _f(r["params_total_b"]) else "dense"
            if shape == "moe":
                out.append(f'<rect x="{x-5:.1f}" y="{Y(a)-5:.1f}" width="10" height="10" fill="{col}" stroke="{SURFACE}" stroke-width="2"/>')
            else:
                out.append(f'<circle cx="{x:.1f}" cy="{Y(a):.1f}" r="5" fill="{col}" stroke="{SURFACE}" stroke-width="2"/>')
            if fmt == "table":
                label = r["model"].split("/")[-1].replace("-instruct", "").replace("-it", "").replace("-2507", "")
                where = place[s.index(r)]
                y_lo = Y(lo) if lo is not None else Y(a) + 6
                y_hi = Y(hi) if hi is not None else Y(a) - 6
                # a label that would sit on a baseline goes above the point instead
                if where == "below" and any(abs((y_lo + 13) - Y(b)) < 9 for b in (majority, chance)):
                    where = "above"
                if where == "below":
                    out.append(f'<text x="{x:.1f}" y="{y_lo+13:.1f}" text-anchor="middle" fill="{INK2}" font-size="10">{label}</text>')
                elif where == "right":
                    out.append(f'<text x="{x+10:.1f}" y="{Y(a)+4:.1f}" text-anchor="start" fill="{INK2}" font-size="10">{label}</text>')
                else:
                    out.append(f'<text x="{x-10:.1f}" y="{y_hi-5:.1f}" text-anchor="end" fill="{INK2}" font-size="10">{label}</text>')
    # legend
    lx = W - R - 300
    ly = Y(0.34)
    for i, (fmt, col) in enumerate(SERIES.items()):
        y = ly + i * 18
        out.append(f'<line x1="{lx}" x2="{lx+22}" y1="{y}" y2="{y}" stroke="{col}" stroke-width="2"/>')
        out.append(f'<circle cx="{lx+11}" cy="{y}" r="4" fill="{col}"/>')
        out.append(f'<text x="{lx+30}" y="{y+4}" fill="{INK}">chart as {fmt}{" (3 epochs)" if fmt == "table" else " (1 epoch)"}</text>')
    out.append(f'<text x="{lx}" y="{ly+2*18+4:.1f}" fill="{INK2}" font-size="11">bars: 95% Wilson CI over 400 items. circle dense, square MoE</text>')
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else sorted(RESULTS.glob("*_curve_pinned.csv"))[-1]
    rows = load(path)
    majority = 0.408  # ADDENDUM.md: share of "1" in the pinned set
    chance = 1 / 6
    svg = render(rows, majority, chance)
    out = path.with_suffix(".svg")
    out.write_text(svg, encoding="utf-8", newline="\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
