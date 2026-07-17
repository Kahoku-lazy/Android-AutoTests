---
name: run-py-cross-platform
description: run.py 启动脚本原为 Windows-first，在 macOS 上 kill_port 失效且前端 EIO 崩溃
metadata: 
  node_type: memory
  type: project
  originSessionId: cb149e00-79b9-47cd-8c23-7cb3d75ace4e
---

run.py 原本是 Windows-first 设计，在 macOS(darwin) 上有两个致命 Bug（2026-07-09 修复）：

1. **kill_port 用 Windows 命令**：`netstat -ano` + `taskkill`。mac 上 `taskkill` 不存在、监听态是 `LISTEN` 非 `LISTENING`。导致 stop/restart 无法真正释放端口。已改为按 `sys.platform` 分支：非 Windows 用 `lsof -ti tcp:PORT -sTCP:LISTEN | kill -9`。

2. **前端 Vite 崩溃 `read EIO`**：`npx vite --host` 默认交互模式，readline 绑定继承的 stdin，父进程 TTY 关闭后抛 `Unhandled 'error' ... read EIO` 崩溃 → 5173 OFFLINE。**修复：所有 subprocess.Popen 加 `stdin=subprocess.DEVNULL`**（后台服务通用做法）。

另外 MYSQL_ENV 里的 `DB_PASSWORD` 曾硬编码明文，已改 `os.environ.get("DB_PASSWORD","")`，只从 .env 注入（`_load_dotenv()` 在 MYSQL_ENV 定义前执行，顺序正确）。

**How to apply**: 后台拉起任何 CLI 服务（vite/webpack/watch 类）必加 `stdin=subprocess.DEVNULL`；写平台管理脚本时 kill 端口逻辑要按 `sys.platform` 分支。见 [[hardcoded-credentials]] [[full-stack-verification-workflow]]。
