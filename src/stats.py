"""One place for the interval arithmetic. Used by the in-log metrics and by
analyze, so the CI in the viewer and the CI in the results file are the same
number computed the same way.

Wilson score interval on a proportion. n is the number of *items*, not items
times epochs: repeats of one item are not independent trials, so a run with
three epochs over 400 items gets the interval for n = 400 around its mean.
"""

from __future__ import annotations

import math

Z95 = 1.959963984540054


def wilson(p: float, n: int, z: float = Z95) -> tuple[float, float]:
    """Return (low, high) for proportion p observed over n trials."""
    if n <= 0:
        return (float("nan"), float("nan"))
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
