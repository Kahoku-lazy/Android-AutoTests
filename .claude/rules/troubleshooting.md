# Troubleshooting — Android-AutoTests

> AI 问题诊断规则：遇到报错时先查本文速查表，命中则按标准流程诊断。
> 来源：报错诊断手册 + 元素定位截图流故障手册

---

## 诊断工作流（AI 自动执行）

```
用户报告问题
  ↓
Step 0: 关键词匹配 §一 速查表
  ├── 命中 → 跳转到对应章节，按步骤排查
  └── 未命中 ↓
Step 1: 收集信息
  ├── 前端问题 → 检查浏览器 Console + Network 面板
  ├── 后端问题 → 查 logs/backend.log
  └── 设备问题 → adb devices + GET /api/devices
Step 2: 定位根因 → 输出诊断结果 + 修复步骤
Step 3: 修复后验证 → 确认问题消失
```

---

## 一、速查表（关键词 → 诊断章节）

| 关键词/症状 | 跳转 | 优先级 |
|-----------|------|:--:|
| `MsgPackSerializer` / `abstract methods` / WS 500 | §2.1 | 🔴 |
| 截图流空白 / `正在连接截图流…` / `No device signal` | §2.2 | 🔴 |
| `Port already in use` / 端口占用 | §3.3 | 🟠 |
| `no devices` / `adb` / ADB 无设备 | §3.1 | 🟠 |
| `ConnectError` / `uiautomator2` | §3.2 | 🟠 |
| 页面白屏 / `Failed to fetch dynamically imported module` | §4.1 | 🟠 |
| `ModuleNotFoundError` / import 失败 | §3.4 | 🟡 |
| `no such table` / 表不存在 | §3.5 | 🟡 |
| `database is locked` / SQLite 锁 | §3.6 | 🟡 |
| API 500 / 后端崩溃 | §4.2 | 🟠 |
| API 404 / 路由未找到 | §4.3 | 🟡 |
| WebSocket 连不上 / 101 握手失败 | §2.2 | 🔴 |
| AgentScope 无法启动 | §4.4 | 🟠 |
| AI 对话无响应 | §4.4 | 🟠 |
| 前端数据与 DB 不一致 | §4.5 | 🟡 |

---

## 二、截图流故障（最高频 🔴）

### 2.1 MsgPackSerializer → WebSocket HTTP 500

**症状**：元素定位左侧空白，Network 面板 `/ws/screenshot` 返回 500。

**诊断**：
```bash
grep -i "MsgPackSerializer\|abstract methods" logs/backend.log
```

**根因**：`config/settings.py` 中 `CHANNEL_LAYERS.CONFIG.serializer_format` 为 `msgpack`，但 Python 环境不兼容。

**修复**：
```python
# config/settings.py → CHANNEL_LAYERS.CONFIG
'serializer_format': 'json',  # 禁止改回 msgpack
```

```bash
python run.py restart
```

### 2.2 截图流不显示（通用诊断 5 步）

按优先级依次排查：

```
1. 服务状态
   python run.py status → Django :8766 必须 ONLINE

2. WebSocket 握手
   grep "MsgPackSerializer\|abstract methods" logs/backend.log
   → 命中 → §2.1
   → 未命中 → 继续

3. ADB 设备
   adb devices → 至少一台 status=device

4. 当前设备激活
   curl http://localhost:8766/api/devices → data.current 非空

5. REST 截图兜底
   curl http://localhost:8766/api/elements/screenshot → ok:true
```

**前端检查**：
```bash
# WS URL 是否走代理（不能直连 :8766）
grep -r ":8766/ws" frontend/src/
# 如果命中 → 应改为 wsUrl('/ws/screenshot')，走 Vite proxy
```

**前端验证**：浏览器 DevTools → Network → WS → `/ws/screenshot` 状态码 101，持续收到 `screenshot` 帧。

### 2.3 截图首帧慢

**已修复**：`ScreenshotView.vue` onMounted 时调用 `GET /api/elements/screenshot` 兜底。如果仍慢 → 检查 u2 截图耗时（`device.screenshot_b64()` 应在 500ms 内）。

---

## 三、设备与 ADB

### 3.1 `adb: no devices`

```bash
adb kill-server && adb start-server
# 检查 USB 线 + 手机"允许 USB 调试"弹窗
```

**AI 无法修复**，提示用户检查硬件连接。

### 3.2 `uiautomator2.exceptions.ConnectError`

```bash
python -m uiautomator2 init  # 安装 ATX agent 到设备
```

### 3.3 端口占用

```bash
# 查占用进程
netstat -ano | findstr 8766    # Windows
lsof -i :8766                   # macOS/Linux
# 杀进程
taskkill /PID {PID} /F          # Windows
kill {PID}                       # macOS/Linux
```

**AI 触发条件**：`python run.py start` 报端口冲突时，先查进程再建议 kill。

---

## 四、Django / 后端

### 3.4 `ModuleNotFoundError`

```bash
pip install -r requirements.txt
# 确认目标模块目录有 __init__.py
ls apps/{module_name}/__init__.py
```

### 3.5 `no such table`

```bash
python manage.py makemigrations {app_name}
python manage.py migrate
```

### 3.6 SQLite `database is locked`

临时方案：重启 Django。长期：迁移 MySQL。
```bash
python run.py restart
```

---

## 五、前端

### 4.1 页面白屏

**诊断流程**：
```
1. 检查模块是否加载
   curl -s -o /dev/null -w "%{http_code}" http://localhost:5173/src/modules/{name}/index.vue
   → 非 200 → npm run build 语法错 → 修复后重试

2. 检查 API 是否正常
   curl http://localhost:8766/api/{module}/ → ok:true?

3. Console 报错
   - Unexpected token → 括号/花括号配对
   - is not defined → 缺少 import
   - Cannot read properties of undefined → API 返回结构变化
```

### 4.2 API 500

```bash
# 查看 Django 错误日志
tail -100 logs/backend.log

# 临时开启 DEBUG 看详细栈
# config/settings.py → DEBUG = True → restart
```

常见原因：u2 操作异常 / DB 写入失败 / JSON 解析失败。

### 4.3 API 404

```bash
# 确认路由已注册
python manage.py show_urls | grep {keyword}

# 检查 config/urls.py 是否有 include('apps.{name}.urls')
```

### 4.4 AI 对话故障

```bash
# Redis 是否运行
redis-cli ping → PONG

# Django 日志
tail -50 logs/backend.log

# 重启
python run.py restart
```

AI 对话无响应常见原因：
- Redis 未运行 → AgentScope 无法启动（AgentScope 在 Django 进程内，依赖 Redis）
- Django 挂了 → 检查 `logs/backend.log`
- 模型 API Key 失效 → 检查 `ai_agents` 表中 `api_key` 是否有效

### 4.5 前端数据与 DB 不一致

**根因**：数据来源铁律违反 — 前端用了硬编码数据而非 API 返回。

**检查**：
```bash
# 搜索前端硬编码数据
grep -rn "ref(\[{.*id:" frontend/src/modules/
# 命中 → 改为从 API 获取
```

---

## 六、WebSocket 通用诊断

### WS 握手失败 → HTTP 500

1. `logs/backend.log` 搜 `MsgPackSerializer` → 命中则修 `serializer_format: 'json'`
2. 检查 `config/asgi.py` 是否使用 ASGI 模式（非 WSGI）
3. 检查 `gateway/routing.py` 中路由是否注册

### WS 连上但无数据

1. 设备是否激活 → `GET /api/devices` 确认 `current`
2. 截图 Consumer `channel_layer_alias = None` 是否设置
3. 阻塞操作是否用 `run_in_executor`

### WS URL 构建规则

```javascript
// ✅ 正确：走 Vite 代理，同源
import { wsUrl } from '@/shared/ws-url.js'
const url = wsUrl('/ws/screenshot')

// ❌ 错误：直连后端端口
const url = `ws://localhost:8766/ws/screenshot`
```

---

## 七、服务健康检查

→ 见 `setup.md` 重启验证章节。

---

## 八、相关文件索引

| 文档 | 路径 | 说明 |
|------|------|------|
| 报错诊断手册 | `dev_docs/05-开发与测试/平台级/报错诊断手册.md` | 完整版，含代码示例 |
| 截图流故障手册 | `dev_docs/05-开发与测试/元素定位/截图流故障手册.md` | 截图流专档 |
| 启动配置 | `.claude/rules/setup.md` | 启动命令、健康检查 |
| 前端规则 | `.claude/rules/frontend.md` | 白屏诊断、数据链路 |
| 后端规则 | `.claude/rules/backend.md` | API 错误处理 |
| 安全规则 | `.claude/rules/security.md` | 凭据保护 |

---

## 变更记录

| 版本 | 日期 | 变更摘要 |
|------|------|----------|
| v1.0 | 2026-07-03 | 融合报错诊断手册 + 截图流故障手册，面向 AI 的诊断规则 |
