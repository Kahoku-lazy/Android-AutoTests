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
