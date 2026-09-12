"""효율 계산기 — 시간당 비용과 순마진 비중을 바꿔 가며 세그먼트의 부호와 순위를 본다.

실행:

    .venv\\Scripts\\python -m streamlit run app/calculator_app.py

계산은 analysis/calculator.py가 한다. 이 파일은 입력 위젯과 표시만 맡는다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))

import streamlit as st

from calculator import (INPUT_CSV, allocation_compare, breakeven_margin_shares, load_meta, load_segments,
                        segment_economics, summarise)

st.set_page_config(page_title="효율 계산기", layout="wide")
st.title("대출 오퍼 효율 계산기")
st.caption("접수 시점 정보만으로 나눈 세그먼트 39개에 대해, 알 수 없는 두 값(시간당 비용·순마진 비중)을 바꿔 가며 "
           "기대값의 부호와 배분 순서의 차이를 본다. 예측 도구가 아니라 규칙표 계산기다.")

if not INPUT_CSV.exists():
    st.error(f"입력 파일이 없다: {INPUT_CSV}\n\n"
             "`analysis/00_build_cache.py`부터 번호 순서대로 실행해 산출물을 만든 뒤 다시 열면 된다.")
    st.stop()

table, meta = load_segments(), load_meta()
reference_cost = float(meta["reference_cost_eur_per_hour"])

with st.sidebar:
    st.header("가정")
    cost = st.number_input("시간당 비용 (유로)", min_value=1.0, max_value=1000.0, value=reference_cost, step=1.0,
                           help=f"참조값 {reference_cost} — 출처: {meta['reference_cost_source']}")
    margin_pct = st.slider("총이자 중 순마진 비중 (%)", min_value=0.0, max_value=30.0, value=5.0, step=0.1,
                           help="이자 총액 가운데 조달비용·손실을 뺀 뒤 남는 몫의 비중")
    st.caption("두 값은 로그에 없다. 그래서 값을 넣는 대신 바꿔 가며 본다.")

margin_share = margin_pct / 100
priced = segment_economics(table, cost, margin_share)
totals = summarise(priced)
breakeven = breakeven_margin_shares(table, cost)

st.subheader("이 가정에서의 결과")
left, middle, right = st.columns(3)
left.metric("적자 세그먼트", f"{totals['negative_segments']} / {len(table)}")
middle.metric("적자 세그먼트의 신청 비중", f"{totals['negative_case_share']:.1%}")
right.metric("적자 세그먼트의 공수 비중", f"{totals['negative_effort_share']:.1%}")

st.write(f"순마진 비중이 **{breakeven['first_positive']:.2%}** 를 넘으면 첫 세그먼트가 흑자가 되고, "
         f"**{breakeven['all_positive']:.2%}** 를 넘으면 39개 모두 흑자가 된다. "
         f"두 값의 배율은 {breakeven['all_positive'] / breakeven['first_positive']:.1f}배이고, 시간당 비용을 바꿔도 변하지 않는다.")

st.subheader("세그먼트")
st.caption("η 순으로 정렬했다. 순위는 시간당 비용과 순마진 비중에 관계없이 같다 — 두 값은 모든 세그먼트에 같은 방식으로 곱해진다.")
view = priced.sort_values("eta", ascending=False)
st.dataframe(
    view[["segment", "n", "p", "r_mean", "e_mean", "eta", "eta_I", "required_margin_share", "ev_per_case", "ev_total"]]
    .rename(columns={"segment": "세그먼트", "n": "신청 수", "p": "성사율", "r_mean": "평균 대출금액(유로)",
                     "e_mean": "평균 공수(시간)", "eta": "효율 η", "eta_I": "이자 기준 η_I",
                     "required_margin_share": "필요 최소 순마진 비중", "ev_per_case": "신청당 기대값(유로)",
                     "ev_total": "세그먼트 합계(유로)"}),
    hide_index=True, width="stretch",
    column_config={
        "성사율": st.column_config.NumberColumn(format="%.3f"),
        "평균 대출금액(유로)": st.column_config.NumberColumn(format="%.0f"),
        "평균 공수(시간)": st.column_config.NumberColumn(format="%.3f"),
        "효율 η": st.column_config.NumberColumn(format="%.0f"),
        "이자 기준 η_I": st.column_config.NumberColumn(format="%.0f"),
        "필요 최소 순마진 비중": st.column_config.NumberColumn(format="%.2f%%"),
        "신청당 기대값(유로)": st.column_config.NumberColumn(format="%.1f"),
        "세그먼트 합계(유로)": st.column_config.NumberColumn(format="%.0f"),
    },
)

st.subheader("같은 공수, 다른 배분")
budget = st.slider("투입 공수 (전체 공수 대비, %)", min_value=10, max_value=100, value=50, step=5)
allocation = allocation_compare(table, budget / 100)
by_eta, by_p = st.columns(2)
by_eta.metric("효율 순서", f"{allocation['volume_by_eta'] / 1e6:,.1f}백만 유로")
by_p.metric("성사율 순서", f"{allocation['volume_by_success_rate'] / 1e6:,.1f}백만 유로",
            delta=f"{-allocation['gain']:.1%}")
st.caption("관측된 세그먼트 평균으로 계산한 가상 배분이다. 개입 효과가 아니다. "
           "공수를 옮겼을 때 세그먼트의 성사율이 그대로라는 보장은 없다.")

st.divider()
st.caption(f"입력: `{INPUT_CSV.name}` · 세그먼트 {meta['segments']}개 · 주 조합 R = {meta['primary_combo']['R']}, "
           f"E = {meta['primary_combo']['E']} · {meta['note']}")
