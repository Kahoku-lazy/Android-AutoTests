# Setup & Configuration — Android-AutoTests

## 启动方式

```bash
cd Android-AutoTests

# 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 数据库初始化（首次运行）
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.create_superuser('admin','admin@local','admin123') if not User.objects.filter(username='admin').exists() else None"

# 知识库初始化（AI 助手 RAG，首次运行）
python agentscope_service/rag/init_kb.py

# 一键启动（Django + AgentScope + Vite）
python run.py start

# 管理
python run.py stop       # 停止
python run.py restart    # 重启
python run.py status     # 状态
python run.py logs       # 日志
```

## 重启后验证

重启完成后必须确认 4 个服务全部正常运行：

### 1. 进程状态

```bash
python run.py status
```

期望输出：4 个服务均为 `ONLINE`：
```
  Redis            (:6379)  ONLINE
  Django backend   (:8765)  ONLINE
  AgentScope AI    (:8000)  ONLINE
  Vue frontend     (:5173)  ONLINE
```

### 2. 各服务健康检查

```bash
# Django API 根路径
curl -s http://localhost:8765/api/ | python -m json.tool

# AgentScope 文档页
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs

# Vue 前端首页
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173

# Redis 连接
redis-cli ping
```

期望：Django 返回 JSON，其余返回 `200`，Redis 返回 `PONG`。

### 3. 常见问题排查

| 现象 | 可能原因 | 解决 |
|------|----------|------|
| AgentScope 无法启动 | Redis 未运行 | `redis-server --daemonize yes` |
| Django 无法启动 | 端口 8765 被占用 | `netstat -ano \| findstr 8765` 查进程后 kill |
| 前端白屏 | Vite 未编译完成 | 等待 3-5 秒刷新，或查看 `logs/frontend.log` |
| AI 对话无响应 | AgentScope 挂了 | 检查 `logs/agentscope.log`，确认 Redis 连通 |
| 截图流断开 | 设备 ADB 断开 | `adb devices` 确认设备在线 |

```bash
# 离线工具（独立使用，不需要服务器）
python tools/dump_ui.py          # dump UI 层级 → ui_data.json + screenshot.png
python tools/generate_html.py    # 生成自包含 phone_ui.html 检查器
```

## 配置参数

| 参数 | 默认值 | 环境变量 |
|------|--------|---------|
| `DEVICE_SERIAL` | `RF8N21MSW7A` | `DEVICE_SERIAL` |
| `SCREENSHOT_INTERVAL` | `0.5`s | `SCREENSHOT_INTERVAL` |
| `DB_ENGINE` | `sqlite` | `DB_ENGINE` (mysql 切换) |
| `REDIS_URL` | `redis://localhost:6379/0` | `REDIS_URL` |
| `AGENTSCOPE_PORT` | `8000` | `AGENTSCOPE_PORT` |
| `JWT_ACCESS_TTL` | `3600` (1h) | `JWT_ACCESS_TTL` |
| Django Admin | `/admin/` | admin / admin123 |

## 代码格式化

统一代码风格，保证 Edit 工具精确匹配。每次提交前执行：

```bash
# Python 后端
python -m ruff format apps/ agentscope_service/ config/ gateway/ shared/ models/

# Vue/JS/CSS 前端
cd frontend && npx prettier --write "src/**/*.{vue,js,css}"
```

> **规则**：改完代码 → 格式化 → 再提交。这能消除缩进/引号/换行差异，让 Edit 工具的 `old_string` 匹配率接近 100%。

| 路径 | 目标 |
|------|------|
| `/api` `/ws` | `:8765` (Django) |
| `/agentscope` `/agentscope-stream` | `:8000` (AgentScope) |

## 前端

Element Plus 按需引入（unplugin-vue-components），Vite proxy 转发。
