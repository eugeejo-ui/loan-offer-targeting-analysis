"""대시보드 화면 캡처 — 링크 미리보기 이미지와 README용 화면을 만든다.

Edge 또는 Chrome의 headless 모드를 쓴다. 브라우저 화면(주소창·탭)은 들어가지 않는다.

- preview   : 링크 미리보기(og:image). 1200x627(링크드인 권장 1.91:1), 캡처 전용 ?preview 모드
- core      : README용 핵심 결론 구역
- calculator: README용 계산기 구역

인자 없이 실행하면 README용 화면만 찍는다. 미리보기는 이미 공유된 링크의 이미지를 바꾸므로
`preview`를 명시했을 때만 다시 찍는다. 미리보기를 다시 찍었다면 22_build_dashboard.py를 한 번 더
실행해 이미지 크기를 og 태그에 반영한다.

Run from the project root, after 22_build_dashboard.py:

    .venv\\Scripts\\python analysis/23_capture_screens.py              # core, calculator
    .venv\\Scripts\\python analysis/23_capture_screens.py preview      # 링크 미리보기
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from config import OUT_DIR, ROOT
from dashboard import png_size

DASHBOARD = OUT_DIR / "dashboard"
ASSETS = ROOT / "docs" / "assets"

# 이름: (가로, 세로, 배율, 쿼리, 저장 경로)
SHOTS = {
    "preview": (1200, 627, 2, "?preview", DASHBOARD / "preview.png"),
    "core": (1440, 780, 2, "?shot=core", ASSETS / "dashboard-core.png"),
    "calculator": (1440, 900, 2, "?shot=calculator", ASSETS / "dashboard-calculator.png"),
}
DEFAULT = ["core", "calculator"]

CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
]


def find_browser() -> str:
    for path in CANDIDATES:
        if path.exists():
            return str(path)
    for name in ("msedge", "google-chrome", "chromium", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("Edge 또는 Chrome을 찾지 못했습니다. CANDIDATES에 경로를 추가하십시오.")


def capture(browser: str, page: Path, name: str) -> None:
    width, height, scale, query, out = SHOTS[name]
    out.parent.mkdir(parents=True, exist_ok=True)
    # 사용 중인 브라우저 프로필과 충돌하지 않도록 임시 프로필을 쓴다
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([
            browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            f"--user-data-dir={profile}", f"--window-size={width},{height}",
            f"--force-device-scale-factor={scale}", "--virtual-time-budget=8000",
            f"--screenshot={out}", page.resolve().as_uri() + query,
        ], check=True, timeout=180, capture_output=True)
    size = png_size(out)
    if size is None:
        raise SystemExit(f"{name}: 캡처 파일이 생성되지 않았습니다.")
    print(f"{name:10} {out.relative_to(ROOT)} {size[0]}x{size[1]} ({out.stat().st_size / 1024:,.0f} KB)")


def main(names: list[str]) -> None:
    page = DASHBOARD / "index.html"
    if not page.exists():
        raise SystemExit("outputs/dashboard/index.html이 없습니다. 22_build_dashboard.py를 먼저 실행하십시오.")
    unknown = [n for n in names if n not in SHOTS]
    if unknown:
        raise SystemExit(f"알 수 없는 대상: {unknown}. 선택 가능: {sorted(SHOTS)}")
    browser = find_browser()
    for name in names:
        capture(browser, page, name)


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
