# Setup & Configuration — Android-AutoTests

## 启动

```bash
pip install -r requirements.txt
cd frontend && npm install && cd ..
python manage.py migrate
python agentscope_service/rag/init_kb.py   # 首次运行，初始化 RAG 知识库
python run.py start                          # 一键启动 Django + AgentScope + Vite
python run.py stop / restart / status        # 管理
```

## 重启验证

```bash
python run.py status            # 期望 4 服务 ONLINE
curl http://localhost:8765/api/ # JSON
curl -o /dev/null -w "%{http_code}" http://localhost:8000/docs  # 200
curl -o /dev/null -w "%{http_code}" http://localhost:5173        # 200
redis-cli ping                  # PONG
```

## 常见问题

| 现象 | 解决 |
|------|------|
| AgentScope 无法启动 | `redis-server --daemonize yes` |
| 端口占用 | `netstat -ano \| findstr 8765` 查进程后 kill |
| AI 对话无响应 | 检查 `logs/agentscope.log`，确认 Redis 连通 |
| 截图流断开 | `adb devices` 确认设备在线 |

## 代码格式化

```bash
python -m ruff format apps/ agentscope_service/ config/ gateway/ shared/ models/
cd frontend && npx prettier --write "src/**/*.{vue,js,css}"
```
