import argparse
import os
import subprocess
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPS = ROOT / "temps"


def prepare_temp() -> Path:
    path = TEMPS / "pw-tmp"
    path.mkdir(parents=True, exist_ok=True)
    os.environ["TEMP"] = str(path)
    os.environ["TMP"] = str(path)
    os.environ["TMPDIR"] = str(path)
    return path


def prepare_browsers() -> Path | None:
    local = TEMPS / "pw-browsers"
    if os.environ.get("PLAYWRIGHT_BROWSERS_PATH"):
        return Path(os.environ["PLAYWRIGHT_BROWSERS_PATH"])
    if not local.is_dir():
        return None
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(local)
    return local


def install_browsers() -> int:
    prepare_temp()
    prepare_browsers()
    sys.stdout.write(
        f"[e2e] 安装 chromium 到 {os.environ.get('PLAYWRIGHT_BROWSERS_PATH') or '默认目录'}\n"
    )
    return subprocess.call([sys.executable, "-m", "playwright", "install", "chromium"], cwd=ROOT)


def run_pytest(extra: list[str]) -> int:
    temp = prepare_temp()
    browsers = prepare_browsers()
    sys.stdout.write(f"[e2e] TEMP={temp}\n")
    if browsers is None:
        sys.stdout.write("[e2e] PLAYWRIGHT_BROWSERS_PATH 未设置，使用 Playwright 默认目录\n")
    else:
        sys.stdout.write(f"[e2e] PLAYWRIGHT_BROWSERS_PATH={browsers}\n")
    command = [sys.executable, "-m", "pytest", "-c", "tests/pytest.ini", "-m", "e2e", *extra]
    return subprocess.call(command, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="在本机跑 e2e：把临时目录与浏览器目录指到 temps/ 下"
    )
    parser.add_argument(
        "--install", action="store_true", help="先安装 chromium 到 temps/pw-browsers"
    )
    parser.add_argument("pytest_args", nargs="*", help="透传给 pytest 的参数")
    args = parser.parse_args()
    if args.install:
        return install_browsers()
    return run_pytest(args.pytest_args)


if __name__ == "__main__":
    sys.exit(main())
