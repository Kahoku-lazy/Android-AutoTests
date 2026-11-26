from __future__ import annotations

import argparse
import shutil
import urllib.error
import urllib.request
import zipfile

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "frontend" / "public" / "fonts" / "harmonyos-sans"
CACHE = ROOT / "temps" / "cache" / "harmonyos-sans-v2.zip"
SOURCE = "https://developer.huawei.com/images/download/next/HarmonyOS-Sans-v2.zip"
WEIGHTS = ("Regular", "Semibold", "Bold")
MIN_BYTES = 8_000_000
MIN_ARCHIVE_BYTES = 40_000_000


def target_files() -> list[Path]:
    return [TARGET / f"HarmonyOS_SansSC_{weight}.ttf" for weight in WEIGHTS]


def fonts_ready() -> bool:
    return all(path.exists() and path.stat().st_size >= MIN_BYTES for path in target_files())


def download_archive() -> Path:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    if CACHE.exists() and CACHE.stat().st_size >= MIN_ARCHIVE_BYTES:
        print(f"复用已下载的发行包：{CACHE}")
        return CACHE
    print(f"下载 HarmonyOS Sans（约 59MB）：{SOURCE}")
    with urllib.request.urlopen(SOURCE, timeout=180) as response, CACHE.open("wb") as handle:
        shutil.copyfileobj(response, handle)
    if CACHE.stat().st_size < MIN_ARCHIVE_BYTES:
        raise OSError(f"发行包体积异常：{CACHE.stat().st_size} 字节")
    return CACHE


def extract_weights(archive: Path) -> list[Path]:
    TARGET.mkdir(parents=True, exist_ok=True)
    wanted = {path.name: path for path in target_files()}
    with zipfile.ZipFile(archive) as bundle:
        for member in bundle.namelist():
            name = member.rsplit("/", 1)[-1]
            if name not in wanted:
                continue
            with bundle.open(member) as source, wanted[name].open("wb") as sink:
                shutil.copyfileobj(source, sink)
    return target_files()


def manual_hint(missing: list[Path]) -> str:
    names = "、".join(path.name for path in missing)
    return (
        f"缺少字体文件：{names}\n"
        f"手动方式：下载 {SOURCE}，解压后把 HarmonyOS Sans/HarmonyOS_SansSC/ 下的三档 TTF 放到 {TARGET}\n"
        "页面会自动回退到系统字体，构建与测试不受影响。"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="按需取用 HarmonyOS Sans 三档原始 TTF（不入库）")
    parser.add_argument("--soft", action="store_true", help="取用失败时只警告，退出码仍为 0")
    args = parser.parse_args()

    if fonts_ready():
        print(f"字体已就位：{TARGET}")
        return 0

    missing: list[Path]
    try:
        missing = [
            path
            for path in extract_weights(download_archive())
            if not path.exists() or path.stat().st_size < MIN_BYTES
        ]
    except (urllib.error.URLError, TimeoutError, OSError, zipfile.BadZipFile) as exc:
        print(f"取用字体失败：{exc.__class__.__name__}: {exc}")
        missing = target_files()

    if missing:
        hint = manual_hint(missing)
        if args.soft:
            print(f"WARN {hint}")
            return 0
        print(f"ERROR {hint}")
        return 1

    print(f"字体已就位：{TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
