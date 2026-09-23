"""端到端步骤报告 — 每一步一张带标注的截图，最后汇总成一个 HTML。

为什么自己画标注：Playwright 没有「带标注的截图」这类 API，而往被测页面里注入高亮层会污染页面
本身（截图里会多出不属于产品的元素，还可能挡住所点的按钮）。所以统一走「先截图、再用 Pillow 画注」：
目标矩形 + 动作点/方向 + 序号徽标 + 顶部说明条 —— 看图片就知道这一步点了哪里、输了什么。

产物：tests/reports/e2e/index.html + tests/reports/e2e/shots/*.jpg（都在 gitignore 的 tests/reports/ 下，
属可随时重新生成的产物）。报告里图片按列宽缩放显示，点击可看大图。
"""

from __future__ import annotations

import functools
import html
import importlib.metadata
import io
import os
import platform
import re
import shutil
import time

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

DEFAULT_OUT_DIR = Path("tests/reports/e2e")
THUMB_WIDTH = 1100  # 写进报告的图片最大宽度：既要看得清，也要报告不臃肿
JPEG_QUALITY = 82

# ── 配色与报告规范同源（.agents/skills/html-report · animal-island-ui）──
INK = "#794f27"
PAPER = "#f8f8f0"
TEAL = "#19c8b9"
RED = "#e05a5a"
YELLOW = "#f5c31c"
BROWN = "#794f27"

MARK_COLORS = {"click": RED, "fill": TEAL, "assert": TEAL, "press": YELLOW, "scroll": BROWN}

_FONT_CANDIDATES = (
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
)


@functools.lru_cache(maxsize=16)
def _font(size: int):
    """中文字体：系统字体逐个探测，全失败才退回 PIL 位图字体（中文会显示成方块）。"""
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _clip(text: str, limit: int = 26) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


@dataclass
class Mark:
    """截图上的一个标注：这一步对「哪里」做了什么。"""

    kind: str
    label: str = ""
    bbox: tuple | None = None  # (x1, y1, x2, y2)
    point: tuple | None = None  # (x, y) 动作点
    scroll: tuple | None = None  # (dx, dy) 滚动量


def _draw_tag(draw, anchor, text, color, font, scale):
    """在目标矩形上方贴一个实心标签；贴到顶就改画在矩形内侧。"""
    x, y = anchor
    width = draw.textlength(text, font=font)
    height = int(font.size * 1.7)
    pad = int(8 * scale)
    rect = (x, y - height - pad, x + width + pad * 2, y - pad)
    if rect[1] < 0:
        rect = (x, y + pad, x + width + pad * 2, y + pad + height)
    draw.rounded_rectangle(rect, radius=int(8 * scale), fill=color)
    draw.text((rect[0] + pad, rect[1] + height * 0.18), text, font=font, fill=PAPER)


def _draw_scroll(draw, size, mark, color, line, scale):
    """滚动方向箭头：画在视口中线，长度随滚动量增长。"""
    width, height = size
    center_x = width // 2
    _, dy = mark.scroll
    length = min(int(abs(dy) * 1.6 + 140 * scale), int(height * 0.55))
    if dy >= 0:
        start = (center_x, height // 2 - length // 2)
        end = (center_x, height // 2 + length // 2)
    else:
        start = (center_x, height // 2 + length // 2)
        end = (center_x, height // 2 - length // 2)
    draw.line((start, end), fill=color, width=line * 2)
    head = int(18 * scale)
    direction = 1 if end[1] > start[1] else -1
    draw.polygon(
        [
            (end[0], end[1]),
            (end[0] - head, end[1] - head * direction),
            (end[0] + head, end[1] - head * direction),
        ],
        fill=color,
    )


def _draw_caption(draw, size, index, caption, font, failed):
    """顶部说明条：第几步 + 做了什么（光看图也能读懂）。"""
    width, _ = size
    text = f"步骤 {index} · {'失败 · ' if failed else ''}{_clip(caption, 46)}"
    available = width - font.size * 1.8
    while draw.textlength(text, font=font) > available and len(text) > 6:
        text = text[:-2] + "…"
    bar = int(font.size * 2.3)
    draw.rectangle((0, 0, width, bar), fill=(121, 79, 39, 232))
    draw.text((int(font.size * 0.9), bar * 0.24), text, font=font, fill=PAPER)


def annotate(
    png: bytes, index: int, caption: str, marks: list, failed: bool = False
) -> Image.Image:
    """把动作标注与说明条画到截图上。"""
    image = Image.open(io.BytesIO(png)).convert("RGB")
    draw = ImageDraw.Draw(image, "RGBA")
    # 说明条与标注按图宽等比缩放：局部小图不能套用整屏的字号，否则说明条会盖住被断言的元素
    scale = max(0.6, image.width / 1280)
    line = max(3, int(4 * scale))
    font = _font(max(15, int(21 * scale)))
    small = _font(max(13, int(18 * scale)))

    for mark in marks:
        color = RED if failed else MARK_COLORS.get(mark.kind, TEAL)
        if mark.bbox:
            x1, y1, x2, y2 = (int(v) for v in mark.bbox)
            pad = int(6 * scale)
            draw.rounded_rectangle(
                (x1 - pad, y1 - pad, x2 + pad, y2 + pad),
                radius=int(10 * scale),
                outline=color,
                width=line,
            )
            if mark.label:
                _draw_tag(draw, (x1 - pad, y1 - pad), mark.label, color, small, scale)
        if mark.point:
            cx, cy = (int(v) for v in mark.point)
            radius = int(9 * scale)
            draw.ellipse(
                (cx - radius, cy - radius, cx + radius, cy + radius),
                fill=color,
                outline=PAPER,
                width=max(2, int(3 * scale)),
            )
            reach = int(24 * scale)
            draw.line((cx - reach, cy, cx + reach, cy), fill=color, width=max(2, int(2 * scale)))
            draw.line((cx, cy - reach, cx, cy + reach), fill=color, width=max(2, int(2 * scale)))
        if mark.scroll:
            _draw_scroll(draw, image.size, mark, color, line, scale)

    _draw_caption(draw, image.size, index, caption, font, failed)
    return image


def _target(locator):
    """动作前测得的元素矩形与中心点（截图为动作后，原地动作两者一致）。"""
    box = locator.bounding_box()
    if not box:
        return None, None
    bbox = (box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"])
    point = (box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    return bbox, point


def _shift(marks: list, clip: dict | None) -> list:
    """局部截图要把标注坐标平移到裁剪坐标系。"""
    if not clip:
        return marks
    ox, oy = clip["x"], clip["y"]
    return [
        Mark(
            m.kind,
            m.label,
            None
            if m.bbox is None
            else (m.bbox[0] - ox, m.bbox[1] - oy, m.bbox[2] - ox, m.bbox[3] - oy),
            None if m.point is None else (m.point[0] - ox, m.point[1] - oy),
            m.scroll,
        )
        for m in marks
    ]


@dataclass
class Step:
    index: int
    caption: str
    duration: float = 0.0
    shot: str | None = None
    status: str = "ok"  # ok / failed
    detail: str = ""
    crop: bool = False


@dataclass
class CaseRecord:
    code: str
    title: str
    nodeid: str
    steps: list = field(default_factory=list)
    status: str = "unknown"  # passed / failed / unknown
    duration: float = 0.0
    error: str = ""

    @property
    def slug(self) -> str:
        return re.sub(r"[^0-9a-zA-Z]+", "_", self.nodeid).strip("_").lower()[:70]


class StepReport:
    """一次会话内的步骤报告：收集用例 → 落盘图片 → 渲染单个 HTML。"""

    def __init__(self, out_dir: Path | str = DEFAULT_OUT_DIR):
        self.out_dir = Path(out_dir)
        self.shots_dir = self.out_dir / "shots"
        self.cases: list = []
        self.started = datetime.now()

    def reset(self) -> None:
        if self.out_dir.exists():
            shutil.rmtree(self.out_dir)
        self.shots_dir.mkdir(parents=True, exist_ok=True)
        self.cases = []

    def register(self, case: CaseRecord) -> None:
        self.cases.append(case)

    def save_image(self, image: Image.Image, slug: str, index: int) -> str:
        """缩放并存成 JPEG，返回相对 index.html 的路径。"""
        if image.width > THUMB_WIDTH:
            ratio = THUMB_WIDTH / image.width
            image = image.resize((THUMB_WIDTH, int(image.height * ratio)), Image.LANCZOS)
        name = f"{slug}_{index:02d}.jpg"
        image.save(self.shots_dir / name, "JPEG", quality=JPEG_QUALITY, optimize=True)
        return f"shots/{name}"

    # ── 渲染 ──

    def render(self) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        passed = sum(1 for c in self.cases if c.status == "passed")
        failed = sum(1 for c in self.cases if c.status == "failed")
        total_steps = sum(len(c.steps) for c in self.cases)
        total_shots = sum(1 for c in self.cases for s in c.steps if s.shot)

        parts = [
            "<!doctype html>",
            '<html lang="zh-CN">',
            "<head>",
            '<meta charset="utf-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1">',
            "<title>登录模块端到端测试报告 · Android-AutoTests</title>",
            _FONTS,
            f"<style>{_CSS}</style>",
            "</head>",
            "<body>",
        ]

        parts.append('<header class="page">')
        parts.append("<h1>登录模块 · 端到端测试报告</h1>")
        parts.append(
            '<div class="meta">Playwright 真实浏览器 · 每步一张带标注的截图 · 点击图片可看大图</div>'
        )
        parts.append('<div class="kpis">')
        for label, value in (
            ("用例", len(self.cases)),
            ("通过", passed),
            ("失败", failed),
            ("步骤", total_steps),
            ("截图", total_shots),
        ):
            parts.append(f'<div class="kpi"><b>{value}</b><span>{label}</span></div>')
        parts.append("</div>")
        parts.append('<div class="legend">')
        for color, text in (
            (RED, "点击"),
            (TEAL, "输入 / 断言"),
            (YELLOW, "按键 / 长按"),
            (BROWN, "滚动"),
        ):
            parts.append(
                f'<span class="legend-item"><i style="background:{color}"></i>{text}</span>'
            )
        parts.append("</div>")
        parts.append('<div class="env">')
        for key, value in self._env().items():
            parts.append(
                f'<span class="env-item"><b>{html.escape(key)}</b>{html.escape(str(value))}</span>'
            )
        parts.append("</div>")
        parts.append("</header>")

        if self.cases:
            parts.append('<nav class="toc">')
            for i, case in enumerate(self.cases, 1):
                parts.append(f'<a href="#case-{i}">{html.escape(case.code)}</a>')
            parts.append("</nav>")

        parts.append("<main>")
        for i, case in enumerate(self.cases, 1):
            parts.extend(_case_html(case, i))
        parts.append("</main>")

        parts.append('<div class="lightbox" id="lightbox">')
        parts.append('<img alt="步骤截图大图">')
        parts.append(
            '<div class="lb-bar"><span class="lb-cap"></span>'
            '<a target="_blank" rel="noopener">打开原图</a>'
            "<span>点击空白处或按 ESC 关闭</span></div>"
        )
        parts.append("</div>")
        parts.append(f"<script>{_SCRIPT}</script>")
        parts.append("</body>")
        parts.append("</html>")

        path = self.out_dir / "index.html"
        path.write_text("".join(parts), encoding="utf-8")
        return path

    def _env(self) -> dict:
        return {
            "前端": os.environ.get("TEST_FRONTEND_URL", "http://localhost:5173"),
            "后端": os.environ.get("TEST_BASE_URL", "http://localhost:8766"),
            "浏览器": "Chromium（Playwright）",
            "Python": platform.python_version(),
            "Playwright": _package_version("playwright"),
            "生成时间": self.started.strftime("%Y-%m-%d %H:%M:%S"),
        }


def _package_version(name: str) -> str:
    try:
        return importlib.metadata.version(name)
    except importlib.metadata.PackageNotFoundError:
        return "n/a"


def _case_html(case: CaseRecord, order: int) -> list:
    badge_class, badge_text = {
        "passed": ("ok", "通过"),
        "failed": ("fail", "失败"),
    }.get(case.status, ("unknown", "未执行"))
    out = [f'<section class="case" id="case-{order}">']
    out.append('<div class="case-head">')
    out.append(f'<span class="code">{html.escape(case.code)}</span>')
    out.append(f"<h2>{html.escape(case.title)}</h2>")
    out.append(f'<span class="badge {badge_class}">{badge_text}</span>')
    out.append(f'<span class="dur">{case.duration:.1f}s</span>')
    out.append("</div>")
    out.append(f'<div class="nodeid">{html.escape(case.nodeid)}</div>')
    if case.error:
        out.append(f'<pre class="err">{html.escape(case.error)}</pre>')
    out.append('<ol class="steps">')
    for step in case.steps:
        out.append('<li class="step">')
        out.append('<div class="step-head">')
        out.append(
            f'<span class="idx{" idx--fail" if step.status != "ok" else ""}">{step.index}</span>'
        )
        out.append(f'<span class="cap">{html.escape(step.caption)}</span>')
        out.append(f'<span class="dur">{step.duration:.2f}s</span>' if step.duration else "")
        out.append("</div>")
        if step.detail:
            out.append(f'<pre class="err">{html.escape(step.detail)}</pre>')
        if step.shot:
            cls = "shot shot--crop" if step.crop else "shot"
            alt = html.escape(f"步骤 {step.index} · {step.caption}")
            out.append(
                f'<a class="{cls}" href="{step.shot}" data-full="{step.shot}" data-caption="{alt}">'
            )
            out.append(f'<img src="{step.shot}" loading="lazy" alt="{alt}">')
            out.append("</a>")
        out.append("</li>")
    out.append("</ol>")
    out.append("</section>")
    return out


class StepRecorder:
    """用例级记录器：动作仍由 Playwright 原生 API 完成，这里负责标注与留痕。"""

    def __init__(self, page, case: CaseRecord, report: StepReport):
        self.page = page
        self.case = case
        self.report = report

    # ── 只留痕的动作 ──

    def shot(self, caption: str) -> None:
        """整屏截图，无坐标标注 —— 用于「打开页面」「跳转完成」这类状态。"""
        self._record(caption, [])

    def inspect(self, locator, caption: str, pad: float = 24) -> None:
        """元素局部放大截图 —— 断言用，比整屏更容易看清按钮态与文案。

        顶部多留 56px 给说明条，避免它压住被断言的元素本身。
        """
        box = locator.bounding_box()
        if not box:
            self._record(caption, [])
            return
        top_pad = pad + 56
        clip = {
            "x": max(0.0, box["x"] - pad),
            "y": max(0.0, box["y"] - top_pad),
            "width": min(box["width"] + pad * 2, 1280 - max(0.0, box["x"] - pad)),
            "height": box["height"] + pad + top_pad,
        }
        bbox = (box["x"], box["y"], box["x"] + box["width"], box["y"] + box["height"])
        self._record(caption, [Mark("assert", "", bbox)], clip=clip)

    # ── 带标注的动作 ──

    def click(self, locator, caption: str, *, force: bool = False, timeout: float | None = None):
        bbox, point = _target(locator)
        marks = [Mark("click", "点击", bbox, point)]
        started = time.time()
        locator.click(force=force, timeout=timeout)
        self._record(caption, marks, time.time() - started)

    def fill(self, locator, value: str, caption: str, *, secret: bool = False) -> None:
        bbox, point = _target(locator)
        label = (
            "清空输入"
            if not value
            else f"输入：{'•' * min(len(value), 12) if secret else _clip(value, 22)}"
        )
        marks = [Mark("fill", label, bbox, point)]
        started = time.time()
        locator.fill(value)
        self._record(caption, marks, time.time() - started)

    def press(self, locator, key: str, caption: str) -> None:
        bbox, point = _target(locator)
        marks = [Mark("press", f"按键：{key}", bbox, point)]
        started = time.time()
        locator.press(key)
        self._record(caption, marks, time.time() - started)

    def long_press(self, locator, milliseconds: int, caption: str) -> None:
        bbox, point = _target(locator)
        if point is None:
            raise AssertionError(f"长按目标不可见，无法定位：{caption}")
        marks = [Mark("press", f"按住 {milliseconds / 1000:.1f} 秒", bbox, point)]
        started = time.time()
        self.page.mouse.move(point[0], point[1])
        self.page.mouse.down()
        self.page.wait_for_timeout(milliseconds)
        self.page.mouse.up()
        self._record(caption, marks, time.time() - started)

    def scroll(self, dx: int, dy: int, caption: str) -> None:
        started = time.time()
        self.page.mouse.wheel(dx, dy)
        self.page.wait_for_timeout(300)
        self._record(caption, [Mark("scroll", "", scroll=(dx, dy))], time.time() - started)

    def fail(self, caption: str, detail: str = "") -> None:
        """由 pytest 钩子在用例失败时调用，补一张失败现场截图。"""
        self._record(caption, [], status="failed", detail=detail)

    # ── 内部 ──

    def _record(
        self,
        caption: str,
        marks: list,
        elapsed: float = 0.0,
        status: str = "ok",
        detail: str = "",
        clip: dict | None = None,
    ) -> Step:
        index = len(self.case.steps) + 1
        png = self.page.screenshot(clip=clip) if clip else self.page.screenshot()
        image = annotate(png, index, caption, _shift(marks, clip), failed=(status != "ok"))
        shot = self.report.save_image(image, self.case.slug, index)
        step = Step(
            index=index,
            caption=caption,
            duration=elapsed,
            shot=shot,
            status=status,
            detail=detail,
            crop=clip is not None,
        )
        self.case.steps.append(step)
        return step


_REPORT: StepReport | None = None


def get_report() -> StepReport:
    """进程内单例：夹具与会话钩子共用同一个报告对象。"""
    global _REPORT
    if _REPORT is None:
        _REPORT = StepReport(Path(os.environ.get("E2E_REPORT_DIR", DEFAULT_OUT_DIR)))
    return _REPORT


_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@500;700;900&family=Noto+Sans+SC:wght@500;700&display=swap" rel="stylesheet">'
)

_CSS = """
:root{--paper:#f8f8f0;--card:rgb(247,243,223);--ink:#794f27;--body:#725d42;--muted:#9f927d;--line:#c4b89e;--teal:#19c8b9;--red:#e05a5a;--green:#6fba2c;--yellow:#f5c31c}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--body);font-family:Nunito,'Noto Sans SC',-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;font-weight:500;letter-spacing:.01em;line-height:1.6}
header.page{background:var(--card);border-bottom:3px solid var(--line);padding:26px 32px}
h1{margin:0 0 6px;color:var(--ink);font-weight:900;font-size:30px;letter-spacing:.02em}
.meta{color:var(--muted);font-size:14px}
.kpis{display:flex;gap:14px;margin-top:16px;flex-wrap:wrap}
.kpi{background:var(--paper);border:2px solid var(--line);border-radius:18px;padding:8px 20px;transition:transform .25s cubic-bezier(.4,0,.2,1)}
.kpi:hover{transform:translateY(-2px)}
.kpi b{display:block;font-size:22px;color:var(--ink);font-weight:900}
.kpi span{font-size:13px;color:var(--muted)}
.legend{display:flex;gap:18px;margin-top:14px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.legend-item{display:inline-flex;align-items:center;gap:6px}
.legend-item i{width:14px;height:14px;border-radius:4px;display:inline-block}
.env{display:flex;gap:18px;margin-top:12px;flex-wrap:wrap;font-size:13px;color:var(--muted)}
.env-item b{color:var(--ink);margin-right:6px}
nav.toc{background:var(--card);border:2px solid var(--line);border-radius:18px;padding:12px 20px;margin:22px 32px 0;display:flex;gap:16px;flex-wrap:wrap}
nav.toc a{color:var(--body);text-decoration:none;font-size:14px;font-weight:700}
nav.toc a:hover{color:var(--ink);text-decoration:underline}
main{padding:22px 32px 60px;max-width:1200px}
section.case{background:var(--card);border:2px solid var(--line);border-radius:18px;padding:16px 22px 8px;margin-bottom:22px;transition:transform .25s cubic-bezier(.4,0,.2,1)}
section.case:hover{transform:translateY(-2px)}
.case-head{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.case-head h2{margin:0;font-size:19px;color:var(--ink);font-weight:700}
.code{background:var(--teal);color:var(--paper);border-radius:50px;padding:3px 14px;font-weight:900;font-size:13px}
.badge{border-radius:50px;padding:3px 14px;font-size:13px;font-weight:700;border:2px solid}
.badge.ok{color:#3f7a12;border-color:var(--green);background:rgba(111,186,44,.14)}
.badge.fail{color:#a63a3a;border-color:var(--red);background:rgba(224,90,90,.14)}
.badge.unknown{color:var(--muted);border-color:var(--line)}
.nodeid{font-family:'SF Mono','Cascadia Code',Consolas,monospace;font-size:12px;color:var(--muted);margin-top:4px}
.dur{margin-left:auto;color:var(--muted);font-size:12px}
ol.steps{list-style:none;margin:12px 0 0;padding:0}
li.step{border-top:2px dashed var(--line);padding:14px 0 16px}
.step-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.idx{width:26px;height:26px;border-radius:50%;background:var(--teal);color:var(--paper);font-weight:900;font-size:13px;display:inline-flex;align-items:center;justify-content:center;border:2px solid #11a89b}
.idx--fail{background:var(--red);border-color:#a63a3a}
.cap{color:var(--ink);font-weight:700;font-size:15px}
.err{color:#a63a3a;background:rgba(224,90,90,.12);border:2px solid var(--red);border-radius:12px;padding:8px 12px;font-family:'SF Mono',Consolas,monospace;font-size:12px;white-space:pre-wrap;margin:10px 0 0}
.shot{margin-top:10px;display:inline-block}
.shot img{display:block;width:720px;max-width:100%;height:auto;border:2px solid var(--line);border-radius:12px;cursor:zoom-in;background:var(--paper)}
.shot--crop img{width:auto;max-width:460px}
.lightbox{position:fixed;inset:0;background:rgba(61,52,40,.84);display:none;flex-direction:column;align-items:center;justify-content:center;gap:12px;padding:24px;z-index:50}
.lightbox.open{display:flex}
.lightbox img{max-width:96vw;max-height:82vh;border:3px solid var(--paper);border-radius:12px}
.lb-bar{display:flex;gap:18px;align-items:center;color:var(--paper);font-size:14px;flex-wrap:wrap;justify-content:center}
.lb-bar a{color:var(--teal);font-weight:700}
@media(max-width:860px){main{padding:18px}.shot img{max-width:100%}}
"""

_SCRIPT = """
(function(){
  var lb=document.getElementById('lightbox');
  if(!lb) return;
  var img=lb.querySelector('img'), cap=lb.querySelector('.lb-cap'), link=lb.querySelector('a');
  document.querySelectorAll('a.shot').forEach(function(a){
    a.addEventListener('click',function(e){
      e.preventDefault();
      img.src=a.getAttribute('data-full');
      cap.textContent=a.getAttribute('data-caption');
      link.href=a.getAttribute('data-full');
      lb.classList.add('open');
    });
  });
  function close(){lb.classList.remove('open');img.removeAttribute('src');}
  lb.addEventListener('click',function(e){if(e.target===lb||e.target.className==='lb-bar')close();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')close();});
})();
"""
