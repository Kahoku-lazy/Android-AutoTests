from __future__ import annotations

import gzip
import json
import re
import subprocess
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
BUDGETS = FRONTEND / "bundle-budgets.json"
NPX = "npx.cmd" if sys.platform == "win32" else "npx"

SCRIPT_RX = re.compile(r'src="(/assets/[^"]+\.js)"')
STYLE_RX = re.compile(r'href="(/assets/[^"]+\.css)"')
LINK_RX = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
HREF_RX = re.compile(r'href="([^"]+)"')
REL_RX = re.compile(r'rel="([^"]+)"')


def preload_scripts(html: str) -> list[str]:
    found: list[str] = []
    for tag in LINK_RX.findall(html):
        rel = REL_RX.search(tag)
        href = HREF_RX.search(tag)
        if rel is None or href is None:
            continue
        kinds = set(rel.group(1).split())
        if not kinds & {"modulepreload", "preload"}:
            continue
        target = href.group(1)
        if target.startswith("/assets/") and target.endswith(".js"):
            found.append(target)
    return found


def gzip_kb(path: Path, level: int) -> float:
    return round(len(gzip.compress(path.read_bytes(), level)) / 1024, 1)


def ensure_dist() -> None:
    if (DIST / "index.html").exists():
        return
    print("dist 不存在，先构建一次 …")
    result = subprocess.run([NPX, "vite", "build"], cwd=FRONTEND)
    if result.returncode != 0:
        raise SystemExit("构建失败，无法评估体积")
    if not (DIST / "index.html").exists():
        raise SystemExit("构建后仍找不到 frontend/dist/index.html")


def collect(level: int) -> dict:
    html = (DIST / "index.html").read_text(encoding="utf-8")
    scripts = SCRIPT_RX.findall(html)
    styles = STYLE_RX.findall(html)
    preloads = [rel for rel in preload_scripts(html) if rel not in scripts]
    if not scripts and not styles:
        raise SystemExit("在 dist/index.html 中找不到任何入口脚本或样式，检查构建产物")
    js_files = sorted(DIST.glob("assets/*.js"))
    if not js_files:
        raise SystemExit("在 dist/assets 中找不到任何 JS 产物，检查构建产物")
    sizes = [(gzip_kb(path, level), path.name) for path in js_files]
    largest_kb, largest_name = max(sizes)
    total_kb = round(sum(size for size, _ in sizes), 1)
    script_kb = round(sum(gzip_kb(DIST / rel.lstrip("/"), level) for rel in scripts), 1)
    preload_kb = round(sum(gzip_kb(DIST / rel.lstrip("/"), level) for rel in preloads), 1)
    entry_js = round(script_kb + preload_kb, 1)
    entry_css = round(sum(gzip_kb(DIST / rel.lstrip("/"), level) for rel in styles), 1)
    return {
        "entry_js_kb": entry_js,
        "entry_css_kb": entry_css,
        "largest_chunk_kb": largest_kb,
        "total_js_kb": total_kb,
        "largest_chunk": largest_name,
        "js_files": len(js_files),
        "entry_script_kb": script_kb,
        "entry_preload_kb": preload_kb,
        "entry_preload_files": len(preloads),
    }


def main() -> int:
    data = json.loads(BUDGETS.read_text(encoding="utf-8"))
    level = int(data.get("gzip_level", 9))
    budget = data["budget"]
    ensure_dist()
    actual = collect(level)

    print(f"{'指标':<20}{'实测':>10}{'预算':>10}   结论")
    failures: list[str] = []
    for key, limit in budget.items():
        value = actual[key]
        if value > limit:
            failures.append(
                f"{key}: 实测 {value} KB，预算 {limit} KB，超出 {round(value - limit, 1)} KB"
            )
        print(f"{key:<20}{value:>10}{limit:>10}   {'FAIL' if value > limit else 'ok'}")
    print(
        f"最大块：{actual['largest_chunk']}（{actual['largest_chunk_kb']} KB，共 {actual['js_files']} 个 JS 产物）"
    )
    print(
        f"入口 JS 构成：脚本 {actual['entry_script_kb']} KB + 首屏预载 {actual['entry_preload_kb']} KB"
        f"（{actual['entry_preload_files']} 个 modulepreload/preload）"
    )

    if failures:
        print("\n体积超预算：")
        for line in failures:
            print(f"  - {line}")
        print("说明：baseline/budget 见 frontend/bundle-budgets.json；调阈值需写明依据。")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
