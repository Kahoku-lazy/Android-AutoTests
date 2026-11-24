from __future__ import annotations

import os
import subprocess
import sys

from dataclasses import dataclass

from .config import IS_WIN

DB_LOOPBACK = {"127.0.0.1", "localhost", "::1"}
CONNECT_TIMEOUT_SECONDS = 3
SERVICE_START_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class DbConfig:
    engine: str
    host: str
    port: int
    user: str
    password: str
    name: str
    service: str

    @classmethod
    def from_env(cls) -> "DbConfig":
        return cls(
            engine=os.environ.get("DB_ENGINE", "mysql").strip().lower(),
            host=os.environ.get("DB_HOST", "127.0.0.1").strip(),
            port=int(os.environ.get("DB_PORT", "3306")),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            name=os.environ.get("DB_NAME", "android_autotests"),
            service=os.environ.get("DB_SERVICE_NAME", "MySQL" if IS_WIN else "mysql").strip(),
        )


def is_loopback(host: str) -> bool:
    return host.strip().lower() in DB_LOOPBACK


def reachable(cfg: DbConfig) -> tuple[bool, str]:
    if cfg.engine == "sqlite":
        return True, ""
    try:
        import MySQLdb

        conn = MySQLdb.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            passwd=cfg.password,
            db=cfg.name,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )
        conn.close()
        return True, ""
    except Exception as exc:  # noqa: BLE001 - 任何连接失败都转成可读摘要
        return False, " ".join(str(exc).split())[:220]


def status_line() -> str:
    cfg = DbConfig.from_env()
    if cfg.engine == "sqlite":
        return "SQLite  (DB_ENGINE=sqlite)"
    ok, _ = reachable(cfg)
    return f"{cfg.host}:{cfg.port}  {'ONLINE' if ok else 'OFFLINE'}"


def start_local_service(cfg: DbConfig) -> tuple[bool, str]:
    service = cfg.service
    if IS_WIN:
        command = ["sc.exe", "start", service]
    elif sys.platform == "darwin":
        command = ["brew", "services", "start", service]
    else:
        command = ["systemctl", "start", service]
    try:
        proc = subprocess.run(
            command, capture_output=True, text=True, timeout=SERVICE_START_TIMEOUT_SECONDS
        )
    except Exception as exc:  # noqa: BLE001 - 命令不存在/超时都按启动失败处理
        return False, str(exc)
    output = " ".join(((proc.stdout or "") + (proc.stderr or "")).split())
    if proc.returncode == 0 or "already" in output.lower():
        return True, output
    return False, output


def elevation_hint(cfg: DbConfig) -> str:
    service = cfg.service
    if IS_WIN:
        return f"net start {service}   （以管理员身份运行）"
    if sys.platform == "darwin":
        return f"brew services start {service}"
    return f"sudo systemctl start {service}"


def ensure(cfg: DbConfig, allow_autostart: bool) -> bool:
    ok, detail = reachable(cfg)
    if ok:
        print(f"  Database         : {cfg.host}:{cfg.port}  ONLINE")
        return True

    print(f"  Database         : {cfg.host}:{cfg.port}  OFFLINE（{detail or '连接失败'}）")
    if not is_loopback(cfg.host):
        print("  Database         : 远程数据库不可达，请检查网络与服务；不会尝试启动远程库。")
        return False

    hint = elevation_hint(cfg)
    if not allow_autostart:
        print(f"  Database         : 已禁用自动启动（DB_AUTOSTART=0）。请先启动：{hint}")
        return False

    print(f"  Database         : 尝试启动本机服务 {cfg.service} ...")
    started, output = start_local_service(cfg)
    if started and reachable(cfg)[0]:
        print(f"  Database         : {cfg.host}:{cfg.port}  ONLINE（已启动）")
        return True
    if output:
        print(f"  Database         : 启动失败：{output[:200]}")
    print(f"  Database         : 请手动启动后重试：{hint}")
    return False


def cleanup_idle_connections(cfg: DbConfig) -> None:
    if cfg.engine == "sqlite":
        return
    try:
        import MySQLdb

        conn = MySQLdb.connect(
            host=cfg.host,
            port=cfg.port,
            user=cfg.user,
            passwd=cfg.password,
            db=cfg.name,
            connect_timeout=CONNECT_TIMEOUT_SECONDS,
        )
        cur = conn.cursor()
        cur.execute(
            "SELECT ID FROM information_schema.PROCESSLIST "
            "WHERE USER = %s AND DB = %s AND COMMAND = 'Sleep' AND TIME > 5",
            (cfg.user, cfg.name),
        )
        ids = [row[0] for row in cur.fetchall()]
        for pid in ids:
            try:
                cur.execute(f"KILL {pid}")
            except Exception:  # noqa: BLE001 - 连接可能在 SELECT 与 KILL 之间自行关闭：跳过这一条
                pass
        if ids:
            print(f"  MySQL cleanup: closed {len(ids)} idle connection(s)")
        cur.close()
        conn.close()
    except Exception as exc:  # noqa: BLE001 - 清理是 best-effort，失败留下可诊断线索即可
        print(f"  MySQL cleanup skipped: {exc}")
