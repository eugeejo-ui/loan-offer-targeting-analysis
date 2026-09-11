"""Shared chart style: dataviz reference palette (light surface), Korean font, headline and source placement."""
from __future__ import annotations

import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import OUT_DIR, ROOT
from segments import ZERO_BAND

CHART_DIR = OUT_DIR / "charts"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASE = "#c3c2b7"
GRAY = BASE  # de-emphasis for the emphasis form (one hue + gray)
# The first three reference slots are the only ones validated all-pairs (scatter); never cycle past them.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a"]
CHANNELS = ["신규·A_Submitted", "신규·표식 없음", "한도 증액"]


def setup() -> None:
    plt.rcParams.update({
        "font.family": "Malgun Gothic",
        "axes.unicode_minus": False,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "savefig.dpi": 150,
        "axes.edgecolor": BASE,
        "axes.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "grid.linestyle": "-",
        "axes.labelcolor": INK2,
        "axes.labelsize": 9.5,
        "xtick.color": BASE,
        "ytick.color": BASE,
        "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.frameon": False,
        "legend.fontsize": 9,
        "legend.labelcolor": INK2,
        "text.color": INK,
    })


def headline(fig, title: str, subtitle: str) -> None:
    """Title states the finding; subtitle carries the number behind it."""
    fig.text(0.02, 0.975, title, fontsize=13, weight="bold", color=INK, va="top")
    fig.text(0.02, 0.915, subtitle, fontsize=9.5, color=INK2, va="top", wrap=True)


def footnote(fig, text: str) -> None:
    fig.text(0.02, 0.015, text, fontsize=7.5, color=MUTED, va="bottom", wrap=True)


def save(fig, name: str) -> str:
    CHART_DIR.mkdir(parents=True, exist_ok=True)
    path = CHART_DIR / name
    fig.savefig(path)
    plt.close(fig)
    return str(path.relative_to(ROOT))


def _band_label(band: str) -> str:
    if band == ZERO_BAND:
        return "0(미기재)"
    lo, hi = (float(x) for x in re.findall(r"[\d.]+", band))
    if lo != round(lo):  # qcut nudges the lowest edge below the minimum
        return f"{hi:,.0f} 이하"
    if hi >= 10 * lo:  # the top band runs to the data maximum; its upper edge says nothing
        return f"{lo:,.0f} 초과"
    return f"{lo:,.0f}~{hi:,.0f}"


def pretty_segment(segment: str) -> str:
    band, *rest = segment.split(" | ")
    return " · ".join([_band_label(band), *rest])


def channel_of(segment: str) -> str:
    return segment.split(" | ")[1]
