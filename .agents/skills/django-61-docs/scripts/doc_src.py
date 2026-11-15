"""读取 Django 文档的 reST 源（Sphinx `_sources`），支持精确 grep。

为什么不用 web_fetch：文档页很长，抓取常在中途被截断；而 `_sources/*.txt` 是构建源，
无导航噪声、行号稳定，适合"引用某一句"和"确认某段到底怎么写"。

用法示例::

    python doc_src.py ref/checks
    python doc_src.py ref/checks --grep "database tag" -C 3
    python doc_src.py topics/db/fetch-modes --head 40
    python doc_src.py ref/settings --grep "SILENCED_SYSTEM_CHECKS"
    python doc_src.py --list ref/models
    python doc_src.py ref/checks --version 6.0 --grep "cc_delim"

设计约束：
1. 只用标准库（本机站点包出问题时也能跑）。
2. 版本必须显式，默认 6.1；`--version` 可切 6.0 做对照，避免"以为在查 6.1"。
3. 找不到页面时给出可执行的下一步（`--list <上级目录>`），而不是只报 404。
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_VERSION = "6.1"
DEFAULT_LANG = "en"
DOC_HOST = "docs.djangoproject.com"
MAX_PLAIN_LINES = 400


def build_url(path: str, version: str, lang: str) -> str:
    """把 `ref/checks` 这类路径拼成 `_sources` 的 reST 源地址。"""
    return f"https://{DOC_HOST}/{lang}/{version}/_sources/{path}.txt"


def normalize_path(raw: str) -> str:
    """接受 `ref/checks`、`/ref/checks/`、`ref/checks.txt` 或整条 URL，统一成 `ref/checks`。"""
    text = raw.strip()
    if text.startswith(("http://", "https://")):
        url_path = urllib.parse.urlparse(text).path.strip("/")
        parts = [p for p in url_path.split("/") if p]
        # 丢掉语言段与版本段（形如 en / 6.1），其余才是文档相对路径
        if len(parts) >= 2 and re.fullmatch(r"\d+\.\d+|dev|stable|latest", parts[1]):
            parts = parts[2:]
        text = "/".join(parts)
    text = text.strip("/")
    if text.endswith(".txt"):
        text = text[: -len(".txt")]
    if text.endswith(".html"):
        text = text[: -len(".html")]
    return text


def fetch(url: str) -> str:
    """取回文本；失败时抛出带下一步建议的 RuntimeError。"""
    request = urllib.request.Request(url, headers={"User-Agent": "django-61-docs-skill"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code} 取不到 {url}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"网络错误 {exc.reason}（地址 {url}）") from exc


def list_pages(directory: str, version: str, lang: str) -> int:
    """打印目录下有哪些页：直接读该目录 index 的 toctree。"""
    for candidate in (f"{directory}/index", directory):
        try:
            text = fetch(build_url(candidate, version, lang))
        except RuntimeError:
            continue
        entries = _toctree_entries(text) or _bare_lines(text)
        print(f"# source: {build_url(candidate, version, lang)}")
        for entry in entries:
            print(entry)
        return 0
    print(
        f"列不出 {directory}：index 不存在。试 --list 上一级目录，或直接给具体页路径。",
        file=sys.stderr,
    )
    return 2


def _toctree_entries(text: str) -> list[str]:
    """抽出 `.. toctree::` 块里缩进的那些页名。"""
    lines = text.splitlines()
    entries: list[str] = []
    in_tree = False
    for line in lines:
        if line.lstrip().startswith(".. toctree::"):
            in_tree = True
            continue
        if in_tree:
            if not line.strip():
                continue
            if line.startswith((" ", "\t")):
                entry = line.strip()
                if not entry.startswith(":"):
                    entries.append(entry)
            else:
                in_tree = False
    return entries


def _bare_lines(text: str) -> list[str]:
    """没 toctree 时的兜底：列出缩进且像路径的行。"""
    return [ln.strip() for ln in text.splitlines() if re.fullmatch(r"\s+[\w./\-]+", ln)]


def grep(text: str, pattern: str, context: int, label: str) -> int:
    """按行打印命中（带行号），返回命中数。"""
    regex = re.compile(pattern, re.IGNORECASE)
    lines = text.splitlines()
    hits = 0
    printed: set[int] = set()
    for index, line in enumerate(lines):
        if not regex.search(line):
            continue
        hits += 1
        start = max(0, index - context)
        end = min(len(lines), index + context + 1)
        for cursor in range(start, end):
            if cursor in printed:
                continue
            printed.add(cursor)
            mark = ">" if cursor == index else " "
            print(f"{label}:{cursor + 1}:{mark} {lines[cursor]}")
        if end < len(lines):
            print("--")
    return hits


def main(argv: list[str] | None = None) -> int:
    """入口：解析参数并输出文档源文本。"""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # 控制台 GBK 时中文不乱码

    parser = argparse.ArgumentParser(description="读取 Django 文档 reST 源（_sources）")
    parser.add_argument(
        "path", nargs="?", help="文档相对路径，如 ref/checks 或 topics/db/fetch-modes"
    )
    parser.add_argument(
        "--version", default=DEFAULT_VERSION, help=f"文档版本，默认 {DEFAULT_VERSION}"
    )
    parser.add_argument("--lang", default=DEFAULT_LANG, help="语言段，默认 en（_sources 永远英文）")
    parser.add_argument("--grep", help="按正则过滤（忽略大小写）")
    parser.add_argument("-C", "--context", type=int, default=2, help="grep 上下文行数，默认 2")
    parser.add_argument("--head", type=int, help="只打印前 N 行")
    parser.add_argument("--tail", type=int, help="只打印后 N 行")
    parser.add_argument("--list", metavar="DIR", help="列出该目录下有哪些页")
    args = parser.parse_args(argv)

    if args.list:
        return list_pages(normalize_path(args.list), args.version, args.lang)
    if not args.path:
        parser.error("需要给一个文档路径，或用 --list <目录>")

    path = normalize_path(args.path)
    url = build_url(path, args.version, args.lang)
    try:
        text = fetch(url)
    except RuntimeError as exc:
        print(f"{exc}\n下一步：python doc_src.py --list <上一级目录>", file=sys.stderr)
        return 2

    label = f"{args.lang}/{args.version}/{path}.txt"
    if args.grep:
        hits = grep(text, args.grep, args.context, label)
        if not hits:
            print(
                f"未命中 {args.grep!r}（已搜 {len(text.splitlines())} 行，源 {url}）",
                file=sys.stderr,
            )
            return 1
        return 0

    lines = text.splitlines()
    start = 0
    if args.head:
        end = min(args.head, len(lines))
    elif args.tail:
        start = max(0, len(lines) - args.tail)
        end = len(lines)
    else:
        end = min(len(lines), MAX_PLAIN_LINES)
        if end < len(lines):
            print(
                f"# 已截断到前 {MAX_PLAIN_LINES} 行（共 {len(lines)} 行）；"
                f"用 --grep / --head / --tail 精读",
                file=sys.stderr,
            )

    print(f"# source: {url}")
    for offset in range(start, end):
        # 行号始终是源文件里的真实行号，--tail 时也不能从 1 重新数
        print(f"{label}:{offset + 1}: {lines[offset]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
