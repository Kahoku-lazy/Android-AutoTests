# Setup & Configuration — Android-AutoTests

## 启动

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
python manage.py migrate
python run.py start                          # 一键启动 Django + Vite
python run.py stop / restart / status        # 管理
```

## 重启验证

```bash
python run.py status            # 期望 3 服务 ONLINE
curl http://localhost:8766/api/ # JSON
curl -o /dev/null -w "%{http_code}" http://localhost:5173        # 200
redis-cli ping                  # PONG
```

## 常见问题

| 现象 | 解决 |
|------|------|
| AgentScope 无法启动 | `redis-server --daemonize yes`（AgentScope 在 Django 进程内，依赖 Redis） |
| 端口占用 | `netstat -ano \| findstr 8766` 查进程后 kill |
| AI 对话无响应 | 检查 `logs/backend.log`，确认 Redis 连通 |
| 截图流断开 | `adb devices` 确认设备在线 |

## 代码格式化

```bash
python -m ruff format apps/ config/ gateway/ shared/ models/
cd frontend && npx prettier --write "src/**/*.{vue,js,css}"
```

## 文档门户与 Demo 端口约定

| 服务 | 端口 | 启动命令 |
|------|:--:|------|
| 文档门户 `dev_docs/index.html` | 9999 | `cd dev_docs && python3 -m http.server 9999 --bind 0.0.0.0` |
| 工作流 Demo `tests/workflow-demo/index.html` | 9998 | `cd tests/workflow-demo && python3 -m http.server 9998 --bind 0.0.0.0` |

- Demo 禁止 `file://` 打开（SVG `url(#id)` 在 file:// 下无法解析，节点阴影/箭头丢失）
- 禁止从项目根目录启动 HTTP 服务；必须从各自目录启动；端口不可互换

## 跨平台启动

- 后台拉起 CLI 服务（vite/webpack/watch）必加 `stdin=subprocess.DEVNULL`（否则父进程 TTY 关闭抛 `read EIO` 崩溃）
- 端口 kill 逻辑按 `sys.platform` 分支：Windows `netstat -ano`+`taskkill`；macOS/Linux `lsof -ti tcp:PORT -sTCP:LISTEN | kill -9`
