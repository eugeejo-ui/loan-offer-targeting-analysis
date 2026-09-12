"""Shared chart style: dataviz reference palette (light surface), Korean font, headline and source placement."""
from __future__ import annotations

import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from config import OUT_DIR, ROOT
from segments import CHANNEL_LABELS, ZERO_BAND

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
CHANNELS = [CHANNEL_LABELS[("New credit", True)], CHANNEL_LABELS[("New credit", False)],
            CHANNEL_LABELS[("Limit raise", False)]]

# 표시용 이름 — 데이터의 라벨은 그대로 두고 화면에서만 읽기 쉬운 말로 바꾼다.
# 금액 등급은 구간 상한으로 정한다(라벨 문자열 순서에 기대지 않는다).
AMOUNT_TIERS = [(6_500, "소액"), (10_000, "중소액"), (15_500, "중액"), (25_000, "고액")]
TOP_TIER = "초고액"
CHANNEL_DISPLAY = {"신규·A_Submitted 있음": "신규(표식 있음)", "신규·A_Submitted 없음": "신규(표식 없음)",
                   "한도 증액": "한도 증액"}
GOAL_DISPLAY = {"Car": "자동차 구입", "Home improvement": "주택 개량", "Existing loan takeover": "대출 대환",
                "Remaining debt home": "주택 잔여 대출", "Extra spending limit": "추가 한도",
                "Caravan / Camper": "레저 차량", "용도 불명": "용도 미기재",
                "기타": "소수 용도 묶음", "기타 소수 용도": "소수 용도 묶음"}
ALL_GOALS = "용도 전체"  # 용도 축으로 쪼개지지 않은 세그먼트


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
    """금액 등급명. 구간 상한이 어느 눈금 이하인지로 정한다 — 라벨 문자열 순서에 기대지 않는다."""
    if band == ZERO_BAND:
        return ZERO_BAND
    _, hi = (float(x) for x in re.findall(r"[\d.]+", band))
    for ceiling, name in AMOUNT_TIERS:
        if hi <= ceiling:
            return name
    return TOP_TIER


def pretty_segment(segment: str) -> str:
    """화면에 쓰는 세그먼트 이름: 금액 등급 · 접수 경로 · 대출 용도."""
    band, channel, *goal = segment.split(" | ")
    purpose = GOAL_DISPLAY.get(goal[0], goal[0]) if goal else ALL_GOALS
    return " · ".join([_band_label(band), CHANNEL_DISPLAY.get(channel, channel), purpose])


def channel_of(segment: str) -> str:
    return segment.split(" | ")[1]
