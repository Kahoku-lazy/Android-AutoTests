"""采集当前手机页面：截图 + 层级原始 XML + manifest。

不依赖平台代码：设备发现走 adb，连接与取数走 uiautomator2，解析走本 skill 内联的算法副本。
输出目录：<workdir>/overlay_<包名>_<Activity>_n<元素数>[/_vN]
同名目录已存在且层级内容不同时自动加 _v2 / _v3… 后缀，绝不覆盖别的页面。
"""

import argparse
import json
import re
from pathlib import Path

import _device
from vendor.hierarchy import parse_hierarchy_xml
from vendor.xpath import trim_hierarchy


def slugify(package: str, activity: str) -> str:
    raw = "%s_%s" % ((package or "unknown").split(".")[-1], (activity or "unknown").rsplit(".", 1)[-1])
    return re.sub(r"[^A-Za-z0-9_]", "_", raw)[:56]


def capture(serial: str, workdir: Path, label: str = "") -> dict:
    serial = _device.pick_serial(serial)
    d = _device.connect(serial)
    cur = _device.app_current(d)
    w, h = _device.resolution(d)
    # 先截图后取层级：保证框与画面同源，间隔尽量短
    shot_img = _device.screenshot_image(d)
    raw = _device.dump_raw_xml(d, pretty=True)

    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")

    all_nodes = parse_hierarchy_xml(raw)
    kept_ids = {id(e) for e in trim_hierarchy(all_nodes)}
    nodes = [n for n in all_nodes if n["class_name"]]

    prefix = ("%s_" % label) if label else ""
    name = "overlay_%s%s_n%d" % (prefix, slugify(cur.get("package", ""), cur.get("activity", "")), len(nodes))
    base = Path(workdir) / name
    outdir = base
    if outdir.is_dir():
        prev = outdir / "window_dump.xml"
        same = prev.is_file() and prev.read_text(encoding="utf-8") == raw
        if not same:
            i = 2
            while base.with_name(base.name + "_v%d" % i).is_dir():
                i += 1
            outdir = base.with_name(base.name + "_v%d" % i)
    outdir.mkdir(parents=True, exist_ok=True)

    shot = outdir / "screen.png"
    shot_img.save(str(shot))
    xml_path = outdir / "window_dump.xml"
    xml_path.write_text(raw, encoding="utf-8", newline="\n")

    info = {
        "outdir": str(outdir).replace("\\", "/"),
        "screenshot": str(shot).replace("\\", "/"),
        "xml": str(xml_path).replace("\\", "/"),
        "serial": serial,
        "screen": [w, h],
        "package": cur.get("package", ""),
        "activity": cur.get("activity", ""),
        "total_elements": len(nodes),
        "kept_in_snapshot": len(kept_ids & {id(n) for n in nodes}),
        "independence": "本 skill 自采自解，未使用平台代码",
    }
    (outdir / "manifest.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return info


def main() -> None:
    ap = argparse.ArgumentParser(description="采集当前手机页面：截图 + 层级原始 XML + manifest")
    ap.add_argument("--serial", default="", help="设备序列号；缺省要求恰好一台在线设备")
    ap.add_argument("--workdir", default="", help="输出根目录；缺省=项目根下 temps/")
    ap.add_argument("--label", default="", help="输出目录前缀（便于按页面命名区分）")
    args = ap.parse_args()

    workdir = Path(args.workdir) if args.workdir else default_workdir()
    print(json.dumps(capture(args.serial, workdir, args.label), ensure_ascii=False, indent=1))


def default_workdir() -> Path:
    """临时产物根目录：项目根（含 manage.py）下的 temps/；找不到就落到当前目录。"""
    here = Path(__file__).resolve()
    for cand in [here] + list(here.parents):
        if (cand / "manage.py").is_file():
            d = cand / "temps"
            d.mkdir(parents=True, exist_ok=True)
            return d
    d = Path.cwd() / "temps"
    d.mkdir(parents=True, exist_ok=True)
    return d


if __name__ == "__main__":
    main()
