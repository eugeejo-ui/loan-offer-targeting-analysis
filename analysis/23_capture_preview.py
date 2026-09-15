"""링크 미리보기 이미지 — 대시보드 첫 화면을 1200x627(링크드인 권장 1.91:1)로 캡처한다.

Edge 또는 Chrome의 headless 모드를 쓴다. 브라우저 화면(주소창·탭)은 들어가지 않는다.
캡처한 뒤 22_build_dashboard.py를 한 번 더 실행하면 이미지 크기가 og 태그에 들어간다.

Run from the project root, after 22_build_dashboard.py:

    .venv\\Scripts\\python analysis/23_capture_preview.py
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from config import OUT_DIR
from dashboard import png_size

VIEWPORT = (1200, 627)
SCALE = 2  # 고해상도 화면에서도 선명하게 보이도록 2배로 찍는다
TARGET = OUT_DIR / "dashboard"

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


def main() -> None:
    page = TARGET / "index.html"
    if not page.exists():
        raise SystemExit("outputs/dashboard/index.html이 없습니다. 22_build_dashboard.py를 먼저 실행하십시오.")
    out = TARGET / "preview.png"
    # 사용 중인 브라우저 프로필과 충돌하지 않도록 임시 프로필을 쓴다
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run([
            find_browser(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            f"--user-data-dir={profile}", f"--window-size={VIEWPORT[0]},{VIEWPORT[1]}",
            f"--force-device-scale-factor={SCALE}", "--virtual-time-budget=5000",
            f"--screenshot={out}", page.resolve().as_uri() + "?preview",
        ], check=True, timeout=180, capture_output=True)
    size = png_size(out)
    if size is None:
        raise SystemExit("캡처 파일이 생성되지 않았습니다.")
    print(f"wrote {out} {size[0]}x{size[1]} ({out.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    main()
