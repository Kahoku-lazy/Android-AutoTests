"""采集当前手机页面：截图 + UI XML dump + manifest（只读设备，不落库）。

输出目录：<workdir>/overlay_<包名>_<Activity>_n<元素数>[/_vN]
同名目录已存在且 dump 内容不同时自动加 _v2 / _v3… 后缀，绝不覆盖别的页面。
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _bootstrap

_bootstrap.setup_django()

from algorithms.hierarchy import parse_hierarchy_xml
from algorithms.xpath import trim_hierarchy
from apps.device_pool.models import Device
from engines.device.android.u2 import U2Engine


def slugify(package: str, activity: str) -> str:
    raw = "%s_%s" % ((package or "unknown").split(".")[-1], (activity or "unknown").rsplit(".", 1)[-1])
    return re.sub(r"[^A-Za-z0-9_]", "_", raw)[:56]


def resolve_serial(explicit: str) -> str:
    if explicit:
        return explicit
    dev = Device.objects.filter(status="ONLINE").order_by("serial").first()
    if dev is None:
        raise SystemExit("未指定 --serial，且设备表里没有 ONLINE 设备；请先连接设备")
    return dev.serial


def capture(serial: str, workdir: Path, label: str = "") -> dict:
    dev = Device.objects.filter(serial=serial).first()
    addr = (dev.connection_addr if dev else "") or serial

    engine = U2Engine()
    engine.connect(serial, addr)
    try:
        cur = engine.app_current() or {}
        w, h = engine.get_resolution()
        # 先截图后 dump：保证框与画面同源，间隔尽量短
        shot_img = engine.u2.screenshot()
        raw = engine.u2.dump_hierarchy(compressed=False, pretty=True)
    finally:
        engine.disconnect()

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
        "screen": [w, h],
        "package": cur.get("package", ""),
        "activity": cur.get("activity", ""),
        "total_elements": len(nodes),
        "kept_in_snapshot": len(kept_ids & {id(n) for n in nodes}),
    }
    (outdir / "manifest.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    return info


def main() -> None:
    ap = argparse.ArgumentParser(description="采集当前手机页面：截图 + UI XML dump + manifest")
    ap.add_argument("--serial", default="", help="设备序列号；缺省取第一个 ONLINE 设备")
    ap.add_argument("--workdir", default="", help="输出根目录；缺省=项目根下 temps/")
    ap.add_argument("--label", default="", help="输出目录前缀（便于按页面命名区分）")
    args = ap.parse_args()

    workdir = Path(args.workdir) if args.workdir else _bootstrap.default_workdir()
    info = capture(resolve_serial(args.serial), workdir, args.label)
    print(json.dumps(info, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
