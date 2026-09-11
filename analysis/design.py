"""Experiment design helpers for the measurement requirements (Phase 9)."""
from __future__ import annotations

import math
from statistics import NormalDist


def ab_sample_size(p_base: float, delta: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Cases per arm to detect a change from p_base to p_base + delta
    (two-sided two-proportion z-test, equal arms)."""
    p1, p2 = p_base, p_base + delta
    p_bar = (p1 + p2) / 2
    z_a = NormalDist().inv_cdf(1 - alpha / 2)
    z_b = NormalDist().inv_cdf(power)
    n = (z_a * math.sqrt(2 * p_bar * (1 - p_bar))
         + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / delta ** 2
    return math.ceil(n)
