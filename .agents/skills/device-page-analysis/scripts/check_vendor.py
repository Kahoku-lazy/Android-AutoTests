"""内联算法副本与平台来源文件的摘要比对 — 防 skill 与平台算法层静默漂移。

用法：python check_vendor.py

平台树不存在时跳过（本 skill 可独立运行，不强制依赖平台）。
退出码：0 = 一致或已跳过，1 = 有副本需要同步。
"""

import hashlib
import re
import sys
from pathlib import Path

# 头部由内联时写入，形如：
#   来源：algorithms/hierarchy.py
#   来源文件 sha256 前 12 位：03bad697bd45
_HEADER = re.compile(r"来源：(.+?)\n来源文件 sha256 前 12 位：([0-9a-f]{12})")


def find_platform_root(start: Path):
    """向上找平台根：同时含 manage.py 与 algorithms/ 的目录。"""
    for cand in [start] + list(start.parents):
        if (cand / "manage.py").is_file() and (cand / "algorithms").is_dir():
            return cand
    return None


def main() -> int:
    vendor_dir = Path(__file__).resolve().parent / "vendor"
    root = find_platform_root(Path(__file__).resolve())
    if root is None:
        print("未找到平台树（无 manage.py + algorithms/），跳过内联副本对拍")
        return 0

    stale = []
    for path in sorted(vendor_dir.glob("*.py")):
        if path.name == "__init__.py":
            continue
        match = _HEADER.search(path.read_text(encoding="utf-8"))
        if match is None:
            stale.append(path.name)
            print("%s: 缺少来源摘要头" % path.name)
            continue
        source_rel, recorded = match.group(1), match.group(2)
        source = root / source_rel
        if not source.is_file():
            stale.append(path.name)
            print("%s: 来源文件不存在 %s" % (path.name, source_rel))
            continue
        actual = hashlib.sha256(source.read_text(encoding="utf-8").encode("utf-8")).hexdigest()[:12]
        if actual == recorded:
            print("%s: 与 %s 一致（%s）" % (path.name, source_rel, actual))
        else:
            stale.append(path.name)
            print("%s: 与 %s 不一致（记录 %s，实际 %s）→ 需按来源重新内联" % (path.name, source_rel, recorded, actual))

    if stale:
        print("需要同步的内联副本：" + ", ".join(stale))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
