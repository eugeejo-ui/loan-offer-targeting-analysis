"""대시보드 빌드 — 산출물을 읽어 `outputs/dashboard/`에 열 수 있는 한 페이지를 만든다.

이 폴더는 그대로 GitHub Pages에 배포된다(.github/workflows/pages.yml). 그래서 차트를 폴더 안에 복사하고,
링크 미리보기용 og 태그를 절대경로로 넣는다. 미리보기 이미지는 23_capture_screens.py가 만든다.

Run from the project root, after the phase scripts:

    .venv\\Scripts\\python analysis/22_build_dashboard.py
"""
from __future__ import annotations

import json
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

from calculator import allocation_compare, breakeven_margin_shares, load_segments, segment_economics, summarise
from config import OUT_DIR, ROOT
from dashboard import build_payload, english_summary, png_size, render_page

CHECK_MARGIN_SHARE = 0.05  # 화면 기본값과 같아야 한다
CHECK_BUDGET = 0.5

SOURCE = ROOT / "app" / "dashboard"
TARGET = OUT_DIR / "dashboard"
STATIC = ["styles.css", "dashboard.js"]
CHARTS = OUT_DIR / "charts"

# 배포 주소가 바뀌면 여기만 고친다. 링크 미리보기는 절대경로만 읽는다.
SITE = {
    "url": "https://eugeejo-ui.github.io/loan-offer-targeting-analysis/",
    "repo": "https://github.com/eugeejo-ui/loan-offer-targeting-analysis",
    "title": "Loan Offer Targeting — Where Conversion and Efficiency Disagree",
    "image": "preview.png",
    "image_alt": "Dashboard overview: conversion rate and effort efficiency across 39 loan application segments",
}


def read(name: str) -> pd.DataFrame:
    return pd.read_csv(OUT_DIR / name, encoding="utf-8-sig")


def main() -> None:
    effort = read("p2_effort_by_outcome.csv")
    frames = {
        "efficiency": read("p5_segment_efficiency.csv"),
        "alignment": read("p5_rank_alignment.csv"),
        "targeting": read("p5_targeting_compare.csv"),
        "mismatch": read("p5_mismatch.csv"),
        "groups": read("p6_group_summary.csv"),
        "failures": read("p7_failure_effort.csv"),
        "checks": read("p8_intervention_checks.csv"),
        "experiments": read("p9_ab_sample_sizes.csv"),
        "meta": json.loads((OUT_DIR / "p5_calculator_meta.json").read_text(encoding="utf-8")),
        "population": {
            "cases": int(effort["cases"].sum()),
            "success_cases": int(effort.loc[effort["outcome"] == "success", "cases"].iloc[0]),
            "success_rate": float(effort.loc[effort["outcome"] == "success", "cases"].iloc[0] / effort["cases"].sum()),
            "effort_hours": float(effort["total_hours"].sum()),
        },
    }

    payload = build_payload(frames)
    payload["built_on"] = date.today().isoformat()

    # 화면의 계산은 브라우저가 한다. 같은 입력에서 파이썬(analysis/calculator.py)과 값이 같은지
    # 페이지가 스스로 확인할 수 있도록 기준값을 함께 넣는다.
    reference_cost = float(frames["meta"]["reference_cost_eur_per_hour"])
    segments = load_segments()
    totals = summarise(segment_economics(segments, reference_cost, CHECK_MARGIN_SHARE))
    breakeven = breakeven_margin_shares(segments, reference_cost)
    allocation = allocation_compare(segments, CHECK_BUDGET)
    payload["reference_check"] = {
        "cost": reference_cost,
        "margin_share": CHECK_MARGIN_SHARE,
        "budget": CHECK_BUDGET,
        "negative_segments": totals["negative_segments"],
        "negative_case_share": totals["negative_case_share"],
        "negative_effort_share": totals["negative_effort_share"],
        "first_positive": breakeven["first_positive"],
        "all_positive": breakeven["all_positive"],
        "volume_by_eta": allocation["volume_by_eta"],
        "volume_by_success_rate": allocation["volume_by_success_rate"],
    }

    TARGET.mkdir(parents=True, exist_ok=True)
    (TARGET / "data.js").write_text(
        "window.DASHBOARD = " + json.dumps(payload, ensure_ascii=False, indent=1) + ";\n", encoding="utf-8")
    summary = english_summary(payload)
    preview = TARGET / SITE["image"]
    page = render_page((SOURCE / "template.html").read_text(encoding="utf-8"), summary, SITE, png_size(preview))
    (TARGET / "index.html").write_text(page, encoding="utf-8")
    for name in STATIC:
        shutil.copyfile(SOURCE / name, TARGET / name)
    (TARGET / "charts").mkdir(exist_ok=True)
    charts = sorted(CHARTS.glob("*.png"))
    for chart in charts:
        shutil.copyfile(chart, TARGET / "charts" / chart.name)

    print(f"segments={payload['segment_count']}  cases={payload['cases_in_segments']:,}  "
          f"population={payload['population']['cases']:,}  effort={payload['population']['effort_hours']:,.1f}h")
    print(f"wrote {TARGET / 'index.html'} (+ data.js, {', '.join(STATIC)}, charts/ x{len(charts)})")
    print(f"summary: {summary}")
    if png_size(preview) is None:
        print(f"WARNING: {preview.name} missing — run analysis/23_capture_screens.py preview, then build again")
    else:
        print(f"preview: {preview.name} {png_size(preview)[0]}x{png_size(preview)[1]}")


if __name__ == "__main__":
    main()
