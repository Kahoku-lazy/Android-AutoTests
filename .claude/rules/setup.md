# Setup & Configuration — Android-AutoTests

## 启动方式

```bash
cd Android-AutoTests

# 安装依赖
pip install -r requirements.txt
cd frontend && npm install && cd ..

# 数据库初始化（首次运行）
python manage.py migrate
# 创建管理员（替换为实际用户名/邮箱/密码）
# python manage.py createsuperuser

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
期望：4 个服务均为 `ONLINE`（Redis/Django/AgentScope/Vue）。

### 2. 各服务健康检查

> 运行 `python run.py status` 确认 4 个服务 ONLINE。各服务详细健康检查见 `troubleshooting.md` 第七节。

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

| 参数 | 环境变量 | 获取方式 |
|------|---------|---------|
| `DEVICE_SERIAL` | `DEVICE_SERIAL` | `adb devices` 或 `.env` 文件 |
| `SCREENSHOT_INTERVAL` | `SCREENSHOT_INTERVAL` | `.env` 文件，默认 0.5s |
| `DB_ENGINE` | `DB_ENGINE` | `config/settings.py`，默认 `mysql` |
| `REDIS_URL` | `REDIS_URL` | `.env` 文件，默认 `redis://localhost:6379/0` |
| 服务端口 | — | `run.py` 顶部 `PORTS` 字典 |
| Django Admin | — | 通过 `manage.py createsuperuser` 创建，凭据存入 `auth_user` 表 |

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
