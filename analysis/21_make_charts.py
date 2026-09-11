"""Charts where a picture explains faster than a table — chosen per finding, not one per phase.

Run from the project root, after the phase scripts:

    .venv\\Scripts\\python analysis/21_make_charts.py
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FuncFormatter, MultipleLocator, PercentFormatter

from charts import (BASE, CHANNELS, GRAY, INK, INK2, MUTED, SERIES, SURFACE, channel_of, footnote, headline,
                    pretty_segment, save, setup)
from config import OUT_DIR
from efficiency import targeting_curve
from loader import load_population
from process import cancel_after_last_sent

THOUSANDS = FuncFormatter(lambda v, _: f"{v:,.0f}")


def _channel_scatter(ax, table: pd.DataFrame, x: str, y: str) -> None:
    channel = table.index.map(channel_of)
    for color, name in zip(SERIES, CHANNELS):
        part = table[channel == name]
        ax.scatter(part[x], part[y], s=48, color=color, edgecolor=SURFACE, linewidth=1.5,
                   label=name, zorder=3)


def _two_line(segment: str) -> str:
    parts = pretty_segment(segment).split(" · ")
    head, tail = " · ".join(parts[:2]), " · ".join(parts[2:])
    return f"{head}\n{tail}" if tail else head


def _callout(ax, table: pd.DataFrame, segment: str, x: str, y: str, at: tuple[float, float]) -> None:
    """Label placed in empty space (axes fraction) with a leader line, so neighbouring labels never stack."""
    ax.annotate(_two_line(segment), (table.loc[segment, x], table.loc[segment, y]), xytext=at,
                textcoords="axes fraction", va="bottom", fontsize=8, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.7, shrinkA=2, shrinkB=4))


def cancel_gap() -> str:
    ev, _ = load_population()
    cancel = cancel_after_last_sent(ev).dropna(subset=["gap_days"])
    summary = pd.read_csv(OUT_DIR / "p1_cancel_gap_summary.csv", index_col=0)["value"]
    days = cancel["gap_days"].clip(upper=60)
    system = cancel["cancel_by_system"].astype(bool)
    bins = np.arange(0, 62, 1)

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(top=0.76, bottom=0.17)
    ax.hist([days[system], days[~system]], bins=bins, stacked=True, rwidth=0.8,
            color=[SERIES[0], SERIES[1]], label=["시스템 처리 취소", "직원 처리 취소"], zorder=3)
    peak = np.histogram(days, bins=bins)[0].max()
    ax.annotate(f"29~32일: 취소의 {summary['share_within_29_32_days']:.0%}\n"
                f"그중 시스템 처리 {summary['system_share_within_rule']:.1%}",
                xy=(31, peak * 0.95), xytext=(40, peak * 0.7), fontsize=9, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_xlabel("마지막 오퍼 발송부터 취소까지 (일)")
    ax.set_ylabel("취소 건수")
    ax.yaxis.set_major_formatter(THOUSANDS)
    ax.set_xlim(0, 61)
    fig.legend(loc="upper right", bbox_to_anchor=(0.99, 0.88), ncol=2)
    headline(fig, "취소는 마지막 오퍼 발송 30일 뒤에 집중된다",
             "고객이 30일간 응답하지 않으면 시스템이 자동 취소 · 취소 케이스의 소요시간은 은행 처리가 아닌 이 규칙에 따라 결정")
    footnote(fig, "출처: outputs/p1_cancel_gap_summary.csv · 오퍼가 발송된 취소 9,593건 · 60일 이상은 60일 구간에 합산")
    return save(fig, "p1_cancel_gap.png")


def rate_vs_eta() -> str:
    t = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")
    align = pd.read_csv(OUT_DIR / "p5_rank_alignment.csv").set_index("combo").loc["amount_effort"]

    fig, ax = plt.subplots(figsize=(9, 5.6))
    fig.subplots_adjust(top=0.80, bottom=0.12)
    ax.axvline(t["p"].median(), color=BASE, lw=0.8, zorder=1)
    ax.axhline(t["eta"].median(), color=BASE, lw=0.8, zorder=1)
    _channel_scatter(ax, t, "p", "eta")
    # rank_gap = rank_p − rank_eta: the largest gaps sit up-left (efficient, low rate), the smallest down-right.
    for seg, at in zip(t.nlargest(2, "rank_gap").sort_values("p").index, [(0.03, 0.76), (0.33, 0.76)]):
        _callout(ax, t, seg, "p", "eta", at)
    for seg, at in zip(t.nsmallest(2, "rank_gap").sort_values("p").index, [(0.63, 0.15), (0.84, 0.30)]):
        _callout(ax, t, seg, "p", "eta", at)
    ax.text(0.99, 0.02, "성사율↑ · 효율↓", transform=ax.transAxes, ha="right", fontsize=9, color=MUTED)
    ax.text(0.01, 0.97, "성사율↓ · 효율↑", transform=ax.transAxes, ha="left", va="top", fontsize=9, color=MUTED)
    ax.set_xlabel("성사율")
    ax.set_ylabel("효율 η (공수 1시간당 기대 대출금액, 유로)")
    ax.xaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    ax.yaxis.set_major_formatter(THOUSANDS)
    fig.legend(loc="upper right", bbox_to_anchor=(0.99, 0.86), ncol=3)
    headline(fig, "성사율이 높은 세그먼트와 효율이 높은 세그먼트는 일치하지 않는다",
             f"세그먼트 39개의 성사율 순위와 효율 순위 간 상관 ρ = {align['rho_p_eta']:.2f} "
             f"(90% 구간 {align['rho_ci_lo']:.2f}~{align['rho_ci_hi']:.2f})")
    footnote(fig, "출처: outputs/p5_segment_efficiency.csv, p5_rank_alignment.csv · 가로·세로 선은 중앙값 · "
                  "라벨이 붙은 점은 두 순위 차이가 가장 큰 세그먼트")
    return save(fig, "p5_rate_vs_eta.png")


def targeting() -> str:
    t = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")
    compare = pd.read_csv(OUT_DIR / "p5_targeting_compare.csv").set_index("effort_budget_share").loc[0.5]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.subplots_adjust(top=0.78, bottom=0.13)
    for order, color, name in [("eta", SERIES[0], "효율 η 높은 순"), ("p", SERIES[1], "성사율 높은 순")]:
        curve = targeting_curve(t, order)
        xs = np.concatenate([[0.0], curve["effort_share"].to_numpy()]) * 100
        ys = np.concatenate([[0.0], curve["volume"].to_numpy()]) / 1e6
        ax.plot(xs, ys, color=color, lw=2, label=name, zorder=3)
    eta_v, p_v = compare["volume_by_eta"] / 1e6, compare["volume_by_success_rate"] / 1e6
    ax.axvline(50, color=BASE, lw=0.8, zorder=1)
    ax.scatter([50, 50], [eta_v, p_v], s=48, color=[SERIES[0], SERIES[1]], edgecolor=SURFACE, linewidth=1.5, zorder=4)
    ax.annotate(f"{eta_v:,.1f} (성사율 순서 대비 +{compare['eta_order_gain']:.1%})", (50, eta_v), xytext=(-8, 6),
                textcoords="offset points", ha="right", fontsize=9, color=INK2)
    ax.annotate(f"{p_v:,.1f}", (50, p_v), xytext=(8, -12), textcoords="offset points", fontsize=9, color=INK2)
    ax.set_xlabel("투입 공수 (전체 공수 대비)")
    ax.set_ylabel("기대 대출 규모 (백만 유로)")
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, None)
    ax.legend(loc="lower right")
    headline(fig, "같은 공수를 효율 순서로 배분하면 대출 규모가 13% 늘어난다",
             "공수 예산 50% 지점에서 효율 순서와 성사율 순서 비교 · 관측된 세그먼트 평균으로 계산한 가상 배분")
    footnote(fig, "출처: outputs/p5_targeting_compare.csv · 세그먼트 39개 · 배분 순서의 가치 비교(개입 효과 아님)")
    return save(fig, "p5_targeting_curve.png")


def multi_offer() -> str:
    groups = pd.read_csv(OUT_DIR / "p6_group_summary.csv")
    g = groups[groups["definition"] == "d1_later"].set_index("group").loc[["single", "multi_same", "multi_later"]]
    diffs = pd.read_csv(OUT_DIR / "p6_stratified_diff.csv")
    d = diffs[(diffs["grouping"] == "group_d1_later") & (diffs["metric"] == "reached_pending")].set_index("comparison")
    names = ["단일 오퍼", "복수 오퍼\n같은 상담", "복수 오퍼\n나중 상담"]

    fig, (left, right) = plt.subplots(1, 2, figsize=(9, 4.6))
    fig.subplots_adjust(top=0.74, bottom=0.16, wspace=0.35)
    x = np.arange(3)
    for ax, col, fmt, title in [(left, "p", lambda v: f"{v:.1%}", "성사율"),
                                (right, "e_mean", lambda v: f"{v:.2f}시간", "신청당 공수")]:
        ax.bar(x, g[col], width=0.4, color=SERIES, zorder=3)
        for xi, v in zip(x, g[col]):
            ax.annotate(fmt(v), (xi, v), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=9, color=INK2)
        ax.set_xticks(x, names)
        ax.set_title(title, loc="left", fontsize=10, color=INK2)
        ax.grid(axis="x", visible=False)
    left.yaxis.set_major_formatter(PercentFormatter(1.0, decimals=0))
    left.set_ylim(0, 0.8)
    right.set_ylim(0, 1.0)
    same = d.loc["multi_same - single", "stratified_diff"] * 100
    later = d.loc["multi_later - single", "stratified_diff"] * 100
    headline(fig, "복수 오퍼의 성사율 우위는 '나중 상담'에서만 나타난다",
             f"세그먼트 층화 후 단일 오퍼 대비 성사율 차이는 같은 상담 {same:+.1f}%p, 나중 상담 {later:+.1f}%p"
             " (고객이 남아 있어야 생기므로 상한)")
    footnote(fig, "출처: outputs/p6_group_summary.csv, p6_stratified_diff.csv · 상담 구분은 D1(생성 간격 1일 초과) 기준 · "
                  "D2(첫 오퍼 발송 후 추가)에서도 방향 동일")
    return save(fig, "p6_multi_offer.png")


def failure_effort() -> str:
    f = pd.read_csv(OUT_DIR / "p7_failure_effort.csv", index_col="failure_type")
    total = f["effort_total"].sum()
    rows = [("denied", "거절"), ("auto_cancel", "30일 자동 취소"), ("manual_cancel", "수동 취소")]
    before = np.array([f.loc[k, "effort_before"] for k, _ in rows]) / total * 100
    after = np.array([f.loc[k, "effort_after"] for k, _ in rows]) / total * 100
    y = np.arange(len(rows))[::-1]

    fig, ax = plt.subplots(figsize=(9, 4.4))
    fig.subplots_adjust(top=0.74, bottom=0.16, left=0.16)
    # Emphasis form: the after-sent part is what contact policy acts on; the before part recedes to gray.
    ax.barh(y, before, height=0.4, color=GRAY, edgecolor=SURFACE, linewidth=2, label="첫 오퍼 발송 전", zorder=3)
    ax.barh(y, after, left=before, height=0.4, color=SERIES[0], edgecolor=SURFACE, linewidth=2, label="첫 오퍼 발송 후", zorder=3)
    for yi, b, a in zip(y, before, after):
        for start, width, ink in [(0, b, INK), (b, a, "#ffffff")]:
            if width >= 2.5:
                ax.text(start + width / 2, yi, f"{width:.1f}%", ha="center", va="center", fontsize=9, color=ink)
        ax.text(b + a + 0.3, yi, f"합계 {b + a:.1f}%", va="center", fontsize=9, color=INK2)
    ax.annotate("접촉 정책이 다룰 수 있는 부분", (before[1] + after[1] / 2, y[1] - 0.2), xytext=(0, -18),
                textcoords="offset points", ha="center", fontsize=9, color=INK2,
                arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.8))
    ax.set_yticks(y, [name for _, name in rows])
    ax.set_xlabel("전체 공수 대비")
    ax.xaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_major_formatter(PercentFormatter(100, decimals=0))
    ax.set_xlim(0, 20)
    ax.grid(axis="y", visible=False)
    fig.legend(loc="upper right", bbox_to_anchor=(0.99, 0.84), ncol=2)
    auto_before = f.loc["auto_cancel", "effort_before"] / f.loc["auto_cancel", "effort_total"]
    denied_after = f.loc["denied", "effort_after"] / f.loc["denied", "effort_total"]
    headline(fig, "실패 신청에 공수의 34%가 투입되고 접촉 정책의 감축 여지는 3.5%다",
             f"자동 취소 공수의 {auto_before:.0%}는 첫 오퍼 발송 전에 이미 투입 · "
             f"거절 공수의 {denied_after:.0%}는 발송 후 투입")
    footnote(fig, f"출처: outputs/p7_failure_effort.csv · 공수 = 활동별 p99 캡 작업시간, 총 {total:,.1f}시간")
    return save(fig, "p7_failure_effort.png")


def eta_vs_bank_wait() -> str:
    h = pd.read_csv(OUT_DIR / "p8_segment_holder.csv", index_col=0)
    checks = pd.read_csv(OUT_DIR / "p8_intervention_checks.csv")
    rho = float(checks.loc[checks["check"].str.startswith("2"), "value"].iloc[0])
    active = float(checks.loc[checks["check"].str.startswith("3"), "value"].iloc[0])

    fig, ax = plt.subplots(figsize=(9, 5.2))
    fig.subplots_adjust(top=0.78, bottom=0.12)
    _channel_scatter(ax, h, "eta", "bank_days_median")
    for seg in [h["eta"].idxmax(), h["bank_days_median"].idxmax()]:
        ax.annotate(pretty_segment(seg), (h.loc[seg, "eta"], h.loc[seg, "bank_days_median"]), xytext=(-8, 6),
                    textcoords="offset points", ha="right", fontsize=8, color=INK2)
    ax.set_xlabel("효율 η (공수 1시간당 기대 대출금액, 유로)")
    ax.set_ylabel("은행 보유 일수 (중앙값)")
    ax.xaxis.set_major_formatter(THOUSANDS)
    ax.set_ylim(0, None)
    fig.legend(loc="upper right", bbox_to_anchor=(0.99, 0.86), ncol=3)
    headline(fig, "효율이 높은 세그먼트일수록 은행 처리 대기시간이 증가한다",
             f"ρ(효율, 은행 보유 일수) = {rho:+.2f} · 은행 보유 시간 중 실제 작업 비중은 {active:.1%}, 나머지는 대기")
    footnote(fig, "출처: outputs/p8_segment_holder.csv, p8_intervention_checks.csv · 세그먼트 39개 · 영업시간 미보정")
    return save(fig, "p8_eta_vs_bank_wait.png")


def ab_duration() -> str:
    a = pd.read_csv(OUT_DIR / "p9_ab_sample_sizes.csv")
    a = a[~a["experiment"].str.contains("diluted")].reset_index(drop=True)
    source = {"observed, stratified D1 (Phase 6)": "D1 관측값", "observed, stratified D2 (Phase 6)": "D2 관측값",
              "design minimum": "설계 최솟값", "design": "설계값"}
    names = [("첫 상담 단일 오퍼" if e.startswith("first") else "접촉 정책")
             + f" · {d * 100:+.1f}%p ({source[s]})" for e, d, s in zip(a["experiment"], a["delta"], a["delta_source"])]
    feasible = a["verdict"] == "feasible"
    y = np.arange(len(a))[::-1]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    fig.subplots_adjust(top=0.76, bottom=0.14, left=0.33)
    ax.barh(y[feasible], a.loc[feasible, "months_needed"], height=0.5, color=SERIES[0], label="6개월 내 가능", zorder=3)
    ax.barh(y[~feasible], a.loc[~feasible, "months_needed"], height=0.5, color=GRAY, label="6개월 초과", zorder=3)
    for yi, m, n in zip(y, a["months_needed"], a["n_per_arm"]):
        ax.text(m + 0.8, yi, f"{m:.1f}개월 (군당 {n:,}건)", va="center", fontsize=8.5, color=INK2)
    ax.axvline(6, color=INK2, lw=1, zorder=2)
    ax.text(6.4, y.max() + 0.45, "6개월 기준", fontsize=8.5, color=INK2)
    ax.set_yticks(y, names)
    ax.set_xlabel("필요 기간 (개월)")
    ax.set_xlim(0, 80)
    ax.grid(axis="y", visible=False)
    fig.legend(loc="upper right", bbox_to_anchor=(0.99, 0.84), ncol=2)
    flows = a.groupby(a["experiment"].str.startswith("first"))["eligible_per_month"].first()
    headline(fig, "접촉 정책은 6개월 내 A/B 검증이 가능하나 첫 상담 단일 오퍼는 어렵다",
             f"단일 오퍼 규칙의 실제 영향 대상은 월 {flows[True]:,}건, 접촉 정책 대상은 월 {flows[False]:,}건 "
             "(α 0.05 양측, 검정력 0.8, 1:1)")
    footnote(fig, "출처: outputs/p9_ab_sample_sizes.csv · 효과 크기는 설계 파라미터(추정치 아님) · "
                  "단일 오퍼를 전체 신청에 배정하면 효과가 희석돼 327.6개월(그림 제외)")
    return save(fig, "p9_ab_duration.png")


def main() -> None:
    setup()
    for make in (cancel_gap, rate_vs_eta, targeting, multi_offer, failure_effort, eta_vs_bank_wait, ab_duration):
        print(make())


if __name__ == "__main__":
    main()
