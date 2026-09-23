"""三步一条命令：采集 → 分层配图 → 生成 HTML 报告。"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap
import build_layers
import capture_page
import make_report_html


def pick_title(args) -> str:
    if args.title_file:
        return Path(args.title_file).read_text(encoding="utf-8").strip()
    if args.title:
        return args.title
    return "设备页面元素分层分析"


def main() -> None:
    ap = argparse.ArgumentParser(description="采集当前页面 → 两级分层配图 → ECharts HTML 报告")
    ap.add_argument("--serial", default="", help="设备序列号；缺省取第一个 ONLINE 设备")
    ap.add_argument("--workdir", default="", help="采集输出根目录；缺省=项目根下 temps/")
    ap.add_argument("--label", default="", help="采集目录前缀")
    ap.add_argument("--page-dir", default="", help="跳过采集，直接对已有页面目录出图与报告")
    ap.add_argument("--out", default="", help="报告输出路径；缺省=<页面目录>/report.html")
    ap.add_argument("--title", default="", help="报告标题；中文建议改用 --title-file")
    ap.add_argument("--title-file", default="", help="UTF-8 文本文件，内容作为报告标题（推荐）")
    ap.add_argument("--img-width", type=int, default=380, help="预览图宽度（默认 380）")
    ap.add_argument("--quality", type=int, default=76, help="JPEG 质量（默认 76）")
    args = ap.parse_args()

    _bootstrap.setup_django()

    captured = None
    if args.page_dir:
        page_dir = Path(args.page_dir)
        if not (page_dir / "window_dump.xml").is_file():
            raise SystemExit("--page-dir 里没有 window_dump.xml：%s" % page_dir)
    else:
        workdir = Path(args.workdir) if args.workdir else _bootstrap.default_workdir()
        captured = capture_page.capture(capture_page.resolve_serial(args.serial), workdir, args.label)
        page_dir = Path(captured["outdir"])

    built = build_layers.build(page_dir, page_dir)
    title = pick_title(args)
    out = Path(args.out) if args.out else page_dir / "report.html"
    report = make_report_html.build_html(page_dir, out, title, args.img_width, args.quality)

    print(json.dumps({
        "page_dir": str(page_dir).replace("\\", "/"),
        "captured": captured,
        "total_elements": built["total_elements"],
        "by_level1": built["summary_short"] if "summary_short" in built else built["by_level1"],
        "images": built["images"],
        "report": report,
        "title": title,
    }, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
