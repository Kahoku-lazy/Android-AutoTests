"""
实时屏幕镜像 — 只读显示手机屏幕内容，不对设备做任何操作

用法:
  python -m utils.live_screen R5CT62RH88F              # 自动选后端
  python -m utils.live_screen R5CT62RH88F --backend adb
  python -m utils.live_screen R5CT62RH88F --scale 0.4  # 指定缩放
  python -m utils.live_screen --list                   # 列出已连接设备

按键:
  q / ESC  退出        f  切换 适应窗口 / 原始 1:1
  h        HUD 开关    s  保存当前帧到 temps/

后端说明（取帧耗时实测，1080x2340）:
  uiautomator2 ~210ms/帧 (约 4~5 FPS)   adb screencap ~470ms/帧 (约 2 FPS)
"""

import argparse
import shutil
import subprocess
import sys
import time

from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = REPO_ROOT / "temps"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


# ═══════════════════════════════════════════
# 基础工具
# ═══════════════════════════════════════════


def _fix_console_encoding() -> None:
    """Windows 控制台默认 GBK，中文/特殊字符会炸，统一改 UTF-8 并逐行刷新"""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
        except (AttributeError, ValueError):
            pass


def adb_path() -> str:
    found = shutil.which("adb")
    if found:
        return found
    try:
        import adbutils

        bundled = adbutils.adb_path()
        if bundled and Path(bundled).exists():
            return bundled
    except Exception:  # noqa: BLE001 - 仅为兜底查找 adb，任何失败都不致命
        pass
    return "adb"


def adb_devices(adb: str) -> list[tuple[str, str, str]]:
    """返回 [(serial, state, 描述), ...]"""
    try:
        proc = subprocess.run([adb, "devices", "-l"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"[错误] 无法执行 adb: {exc}")
        return []
    rows: list[tuple[str, str, str]] = []
    for line in proc.stdout.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            rows.append((parts[0], parts[1], " ".join(parts[2:])))
    return rows


def print_devices(adb: str) -> None:
    rows = adb_devices(adb)
    if not rows:
        print("未发现任何设备。请确认 USB 已连接且已开启 USB 调试。")
        return
    print(f"已连接设备（{len(rows)}）:")
    for serial, state, desc in rows:
        flag = "OK " if state == "device" else "-- "
        print(f"  {flag}{serial}  [{state}]  {desc}")


def screen_size() -> tuple[int, int]:
    """桌面分辨率，用于计算默认窗口尺寸；失败退回保守值"""
    try:
        import tkinter

        root = tkinter.Tk()
        root.withdraw()
        size = (root.winfo_screenwidth(), root.winfo_screenheight())
        root.destroy()
        return size
    except Exception:  # noqa: BLE001 - 无 GUI/无 tkinter 时用保守值即可
        return (1280, 800)


# ═══════════════════════════════════════════
# 取帧后端（均为只读）
# ═══════════════════════════════════════════


class AdbFrameSource:
    """adb exec-out screencap -p：不依赖 atx-agent，纯读取"""

    name = "adb screencap"

    def __init__(self, adb: str, serial: str) -> None:
        self._cmd = [adb, "-s", serial, "exec-out", "screencap", "-p"]

    def grab(self) -> np.ndarray | None:
        try:
            proc = subprocess.run(self._cmd, capture_output=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            return None
        raw = proc.stdout
        if proc.returncode != 0 or not raw.startswith(PNG_MAGIC):
            return None
        frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
        return frame

    def close(self) -> None:
        return None


class U2FrameSource:
    """uiautomator2 截图：帧率更高，但会连接/拉起 atx-agent"""

    name = "uiautomator2"

    def __init__(self, serial: str) -> None:
        import uiautomator2 as u2

        self._device = u2.connect(serial)

    def grab(self) -> np.ndarray | None:
        try:
            frame = self._device.screenshot(format="opencv")
        except Exception:  # noqa: BLE001 - 设备掉线等异常统一当作丢帧
            return None
        if frame is None:
            return None
        frame = np.asarray(frame)
        return frame if frame.ndim == 3 else None

    def close(self) -> None:
        return None


def build_source(backend: str, adb: str, serial: str):
    if backend in ("auto", "u2"):
        try:
            source = U2FrameSource(serial)
            print("[后端] uiautomator2（约 4~5 FPS）")
            return source
        except Exception as exc:  # noqa: BLE001 - 连接失败即降级到 adb
            print(f"[警告] uiautomator2 连接失败：{exc}")
            if backend == "u2":
                return None
    source = AdbFrameSource(adb, serial)
    print("[后端] adb exec-out screencap（约 2 FPS）")
    return source


# ═══════════════════════════════════════════
# 显示
# ═══════════════════════════════════════════


def text_width(text: str, scale: float, thickness: int) -> int:
    (width, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    return width


def draw_hud(frame: np.ndarray, lines: list[str]) -> None:
    """就地写 HUD；cv2 只能渲染 ASCII，勿传中文

    窗口通常被缩放到 0.3~0.5 倍，字号需按帧宽放大，否则显示出来看不清；
    放大后再按最长行反算收缩系数，保证右侧不被裁掉。
    """
    frame_width = frame.shape[1]
    scale = max(0.6, frame_width / 640.0)
    thickness = max(2, int(round(scale * 2)))
    padding = int(round(16 * scale))
    available = frame_width - 2 * padding
    longest = max(text_width(line, scale, thickness) for line in lines)
    if longest > available:
        scale *= available / longest * 0.99
        thickness = max(2, int(round(scale * 2)))
        padding = int(round(16 * scale))
    line_height = int(round(40 * scale))
    # 贴左下角显示：避开手机自身的状态栏（时间/电量），只压住底部手势条
    y = frame.shape[0] - padding - line_height * (len(lines) - 1) - int(round(10 * scale))
    for idx, text in enumerate(lines):
        color = (0, 0, 255) if idx == 0 and text.startswith("NO SIGNAL") else (0, 255, 0)
        cv2.putText(
            frame,
            text,
            (padding, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            (0, 0, 0),
            thickness + 3,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            text,
            (padding, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            scale,
            color,
            thickness,
            cv2.LINE_AA,
        )
        y += line_height


def fit_size(width: int, height: int) -> tuple[int, int]:
    """按桌面高度 85% 计算适配尺寸"""
    _, screen_height = screen_size()
    ratio = min(1.0, max(0.2, screen_height * 0.85 / height))
    return max(1, int(width * ratio)), max(1, int(height * ratio))


def run_viewer(args: argparse.Namespace) -> int:
    adb = adb_path()
    if args.list:
        print_devices(adb)
        return 0

    serial = args.serial
    if not serial:
        print("[错误] 缺少设备串号。用法：python -m utils.live_screen <手机ID>")
        print_devices(adb)
        return 1

    states = {row[0]: row[1] for row in adb_devices(adb)}
    if serial not in states:
        print(f"[错误] 未发现设备 {serial}")
        print_devices(adb)
        return 1
    if states[serial] != "device":
        print(f"[错误] 设备 {serial} 状态为 {states[serial]}，不是 device（未授权或离线）")
        return 1

    source = build_source(args.backend, adb, serial)
    if source is None:
        return 1

    print(f"[设备] {serial}  等待首帧 ...")
    frame = None
    for _ in range(40):
        frame = source.grab()
        if frame is not None:
            break
        time.sleep(0.25)

    if frame is None:
        print("[错误] 取不到画面，请确认屏幕已点亮且设备未被其他程序独占")
        source.close()
        return 1

    height, width = frame.shape[:2]
    window = args.title or f"Live Screen | {serial}"
    start_w, start_h = (
        (max(1, int(width * args.scale)), max(1, int(height * args.scale)))
        if args.scale
        else fit_size(width, height)
    )
    cv2.namedWindow(window, cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)
    cv2.resizeWindow(window, start_w, start_h)
    print(
        f"[画面] {width}x{height}  后端 {source.name}  窗口 {start_w}x{start_h}\n"
        f"[按键] q/ESC 退出 · f 适应/1:1 · h 隐藏信息 · s 保存当前帧"
    )

    show_hud = not args.no_hud
    full_size = False
    fps = 0.0
    fails = 0
    saved_dir = TEMP_DIR

    try:
        while True:
            began = time.perf_counter()
            fresh = source.grab()
            if fresh is not None:
                frame = fresh
                fails = 0
                height, width = frame.shape[:2]  # 手机旋转时同步刷新
            else:
                fails += 1
            elapsed = time.perf_counter() - began
            instant = 1.0 / elapsed if elapsed > 0 else 0.0
            fps = instant if fps == 0 else fps * 0.8 + instant * 0.2

            canvas = frame.copy() if show_hud else frame
            if show_hud:
                lines = [f"{serial}  {width}x{height}  {fps:4.1f} FPS"]
                if fails:
                    lines.insert(0, f"NO SIGNAL  ({fails} failed)")
                lines.append(f"{source.name}  {time.strftime('%Y-%m-%d %H:%M:%S')}")
                draw_hud(canvas, lines)

            cv2.imshow(window, canvas)
            if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
                break

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord("h"):
                show_hud = not show_hud
            elif key == ord("f"):
                full_size = not full_size
                if full_size:
                    cv2.resizeWindow(window, width, height)
                else:
                    cv2.resizeWindow(window, *fit_size(width, height))
            elif key == ord("s"):
                saved_dir.mkdir(parents=True, exist_ok=True)
                stamp = time.strftime("%Y%m%d_%H%M%S")
                target = saved_dir / f"live_screen_{serial}_{stamp}.png"
                ok = cv2.imwrite(str(target), frame)
                print(f"[保存] {'OK' if ok else '失败'} {target}")
    except KeyboardInterrupt:
        print("\n[退出] 用户中断")
    finally:
        source.close()
        cv2.destroyAllWindows()

    print(f"[退出] 最后帧率 {fps:.1f} FPS")
    return 0


def main() -> int:
    _fix_console_encoding()
    parser = argparse.ArgumentParser(
        prog="python -m utils.live_screen",
        description="实时显示手机屏幕内容（只读，不操作设备）",
    )
    parser.add_argument("serial", nargs="?", help="手机 ID / adb 串号，例如 R5CT62RH88F")
    parser.add_argument(
        "--backend",
        choices=["auto", "u2", "adb"],
        default="auto",
        help="取帧后端：auto 优先 uiautomator2，失败降级 adb（默认 auto）",
    )
    parser.add_argument("--scale", type=float, help="窗口缩放比例，如 0.5；默认按桌面高度自适应")
    parser.add_argument("--title", help="窗口标题（默认 Live Screen | <串号>）")
    parser.add_argument("--no-hud", action="store_true", help="不叠加帧率/串号等信息")
    parser.add_argument("--list", action="store_true", help="列出已连接设备后退出")
    args = parser.parse_args()
    return run_viewer(args)


if __name__ == "__main__":
    sys.exit(main())
