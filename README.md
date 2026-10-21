<div align="center">

# 🐾 Android-AutoTests

**AI 驱动的 Android UI 自动化测试平台**

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2%2B-green.svg)](https://www.djangoproject.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-2.0-orange.svg)](https://docs.agentscope.io/)
![Theme](https://img.shields.io/badge/theme-Doodle%20Craft-f5a623.svg)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

</div>

---

## 📖 项目简介

> 面向 Android 测试工程师的 AI 自动化平台：把用例写成文档，把任务交给 AI 双角色（**执行 + 验收**）跑完，结果回到**任务事件时间线**与**测试报告**，全过程可回看、可取证。

### 价值主张

| 维度 | 传统方式 | Android-AutoTests |
|------|---------|-------------------|
| **用例编写** | 写脚本 / 录制回放 | 项目 → 目录 → 文件 → 用例 → 步骤 五层文档式用例，只写「操作 / 预期」 |
| **执行** | 人盯设备 | 一键下发任务：执行角色操作设备，验收角色用**截图 + 串口日志关键词**判定 |
| **失败定位** | 翻日志 | 任务事件时间线（模型调用 / 工具调用 / 判决）+ 步骤截图缩略图 + 日志证据 |
| **设备管理** | 手工 adb | USB / WiFi 接入、占用锁、心跳巡检、同设备串行 / 异设备并行 |
| **观测** | 多份日志 | 后端 / 智能体 / 设备 / 串口 四组日志 + 仪表盘趋势与模型费用 |

### 产品边界

**✅ 本期范围**：Android 8.0+ UI 自动化 · USB + WiFi ADB · JWT 认证 · 文档式用例 · AI SOP 双角色执行（DeepSeek / 阿里百炼）· 设备日志取证 · SQLite / MySQL + Redis · 在线任务事件与报告

**❌ 非本期**：iOS、Web、API 自动化（Web / API 能力已退役）· 设备云租用 · 多团队隔离 · OAuth / SSO · AI 自我修复失败用例 · 分布式执行集群

---

## 🏗️ 架构概览

```
Vue SPA :5173 ──HTTP(/api)──▶ Vite 代理 ──▶ Daphne :8766 (ASGI)
                                                │
                                  JWTAuthenticationMiddleware
                                                │
                                        DRF View / ViewSet
                                                │
                                          api.py（唯一写库口）
                                                │
                                    MySQL / SQLite ＋ Redis
                                                │
                       ┌────────────────────────┴────────────────────────┐
                       │  AgentScope 2.0（同进程跑 SOP）                   │
                       │  executor 操作设备 → verifier 截图 + 查日志判定     │
                       └────────────────────────┬────────────────────────┘
                                                │ adb（uiautomator2 仅探测）
                                     Android 设备 ＋ 串口日志 :7005
```

| 层 | 技术 | 说明 |
|----|------|------|
| **前端** | Vue 3.4 + Vite 5 + Element Plus | 8 个业务模块，Doodle Craft 手绘主题，唯一 HTTP 出口 `shared/api-client.ts` |
| **后端** | Django 4.2+ + DRF + Daphne(ASGI) | 9 个 App、19 张表、7 组表前缀、65 条业务路径（OpenAPI 66 条 / 86 operations） |
| **AI 引擎** | AgentScope 2.0（Django 进程内） | SOP 双角色：`executor` 执行 + `verifier` 验收；11 个工具（含默认不装配的 OCR） |
| **设备控制** | ADB（uiautomator2 仅探测与取 info） | 截图 / 点击 / 长按 / 滑动 / 输入 / 启停应用 / hierarchy |
| **数据** | SQLite（开发）/ MySQL（生产）+ Redis | `ai_ cm_ dp_ rg_ sl_ task_ wf_` 七组前缀；Redis 承载 JWT 吊销与 Channels layer |
| **实时性** | HTTP 轮询 | 当前**没有** WebSocket / SSE 生产点（`backend/gateway/routing.py` 的 `websocket_urlpatterns` 为空表） |

### 模块地图

| 模块 | 表前缀 | 数据表 | 核心能力 |
|------|--------|--------|---------|
| **登录鉴权** | 无（复用 `auth_user`） | — | 登录 · 注册 · 刷新 · 登出 · 当前身份；JWT 双令牌 + Redis 吊销 |
| **仪表盘** | 无（只读聚合） | — | KPI · 执行趋势 · 任务结果 · 模型用量与费用 · 活动时间线 |
| **设备管理** | `dp_` | 2 | 扫描 · 连接 · 断开 · 激活 · 占用锁 · 心跳 · 释放 |
| **用例管理** | `cm_` | 5 | 项目 → 目录 → 文件 → 用例 → 步骤；移动 / 批量删 / 导入导出 |
| **AI 助手（智能体）** | `ai_` | 1 | 智能体配置 · 模型线路 · 一次性揭示密钥 |
| **任务清单** | `task_` | 5 | 任务提交 / 重跑 / 取消 · 事件与用量 · 任务流程报告 |
| **测试报告** | `rg_` | 2 | 报告列表 · 任务报告 · 用例细分 · 下载与在线预览 |
| **页面流** | `wf_` | 3 | 原型 · 目录 · JSON 文档；VueFlow 画布编排与导入导出 |
| **串口日志** | `sl_` | 1 | 端口监听开关 · 当前日志只读 · 关键词对照表 |

### 一次任务是怎么跑的

1. **建用例**：用例管理工作台里写「项目 → 文件夹 → 用例 → 步骤（操作 / 预期）」。
2. **下发任务**：任务清单页（`/tasks`）选智能体、目标设备、附件与用例标题，提交任务（同一设备串行、不同设备并行）。
3. **装配**：平台把用例物化成 YAML，从智能体配置读取 `executor` / `verifier` 的模型与密钥，起后台线程跑 SOP。
4. **执行 + 验收**：执行角色按步骤操作设备；验收角色截图、查串口日志关键词，判过 / 不过；被驳回则带上原因重试。
5. **落库与回看**：过程事件批量写入任务事件表（含 token 与费用），截图只存 720 缩略图；任务详情页回放时间线，报告页按用例汇总。

---

## 🚀 环境配置

### 前置依赖

| 依赖 | 版本要求 | 检查命令 |
|------|---------|---------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| Redis | 6.0+ | `redis-cli ping` |
| ADB | 任意 | `adb version` |

### 安装

```bash
git clone https://github.com/Kahoku-lazy/Android-AutoTests.git
cd Android-AutoTests

# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd frontend && npm install && cd ..

# 数据库初始化与管理员账号
python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User;
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@local','admin123')
"
```

`.env` 从 `.env.example` 起步：数据库、Redis、JWT 密钥、模型 API Key、设备日志来源都在这里配。

### 启动

```bash
python run.py start      # 依次拉起 Redis + Daphne(:8766) + Vite(:5173)
python run.py status     # 三个服务是否 ONLINE
python run.py logs       # 各服务日志尾部
python run.py check      # 本地质量门禁（与 CI 同一批检查）
```

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 🏠 前端 | `http://localhost:5173` | Vite dev server，改代码秒刷新 |
| 🔌 后端 API | `http://localhost:8766/api/` | REST JSON，统一 `{status, data}` 信封 |
| 📘 API 文档 | `http://localhost:8766/api/swagger/` | drf-spectacular（离线可用，资产随包分发） |
| ⚙️ 管理后台 | `http://localhost:8766/admin/` | Django Admin（Jazzmin 主题） |
| 🤖 AI 引擎 | 无独立端口 | AgentScope 在 Django 进程内运行 |

> 后端端口由环境变量 `SERVER_PORT` 控制（默认 8766），前端固定 5173。

---

## 🗂️ 目录结构

| 目录 | 作用 |
|------|------|
| `backend/` | Django 后端根：项目配置、业务 App、网关、共享基础设施、模板与静态资源 |
| `backend/config/` | Django settings / URLconf / ASGI / env 加载 |
| `backend/apps/` | 9 个 Django App：纯 API，写库统一走各 App 的 `api.py` |
| `backend/gateway/` | 网关中间件（JWT 鉴权、路由汇总） |
| `backend/shared/` | 跨 App 基础设施：JWT、DRF 认证、响应信封、schema、用户工具 |
| `backend/models/` | 跨模块共享的状态枚举与页面节点定义 |
| `backend/templates/` | Django 模板覆盖（当前为 Swagger UI 主题） |
| `backend/static/` | Django Admin / Swagger 静态资源 |
| `engines/` | 引擎层：`agents/`（SOP 角色、工具、事件）、`device/`（adb 引擎、日志总线）、`uart_log/`（串口采集）、`vision/`（OCR） |
| `frontend/` | Vue SPA：`src/modules/`（8 个业务模块）、`src/shared/`（共享件 / 令牌 / 请求出口） |
| `utils/` | 公共基础设施包：`logs`（日志库）+ 质量门禁、架构统计、实时投屏等**开发脚本**（`python utils/xxx.py` 调用，业务代码不 import） |
| `tests/` | 分层测试：`api/` · `graybox/` · `engines/` · `e2e/` · `arch/` |
| `openspec/` | 能力规格（`specs/`）与变更归档（`changes/`） |
| `logs/` | 运行期日志：`backend.log` · `agents/` · `device.log` · `serial.log` · `serial_logs/` |

---

## 📐 开发约定

**请求链路**：前端模块 `api.ts` → `djangoClient`（`/api`）→ Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status, data}`）→ ORM。

**分层纪律**：`urls.py`（路径真相源）→ View/ViewSet（只分发）→ Serializer（契约）→ `api.py`（唯一写库口）→ ORM。跨 App **读 Model 可以，写必须走对方 `api.py`**。

**硬约束**：

1. `/api/` 路径一律以 `/` 结尾（`APPEND_SLASH = False`，缺斜杠是确定的 404）。
2. 响应信封 `{status, data}`；错误 `{status, message}` + 对应 HTTP 状态码；JSON 字段 snake_case。
3. 表前缀只用在用集合：`ai_ cm_ dp_ rg_ sl_ wf_`。
4. 前端只有一个 HTTP 出口（`shared/api-client.ts`），业务模块不得另起 axios 实例或裸 `fetch`。
5. 上层不得直接 import `airtest` / `uiautomator2`，设备操作一律经引擎层。
6. 前端 UI 默认遵循 Doodle Craft 主题：设计令牌只在 `shared/styles/tokens.css` 登记，不写颜色 / 字号字面量。

---

## ✅ 质量门禁

```bash
python run.py check      # 本地全量门禁（与 CI 同一批检查）
```

- 检查清单与判定口径以 `utils/check_gates.py` 为唯一真相源（当前 24 项，含阻塞项与告警项；阻塞项失败退出码为 1）。
- 覆盖：Django system check、ruff（格式 + lint）、**pytest 收集门禁**、**OpenAPI 契约**（生成 + 校验 + 与基线一致）、**OpenAPI 覆盖**（业务路径必须全部已文档化）、前端 vitest / vite build / eslint / vue-tsc / prettier、硬编码凭据扫描、模块边界（跨 App import 与 ORM 直写）、Vue 文件体积、伪造数据与静默吞异常检查。
- 接口契约基线是 `openspec/openapi.yaml`（drf-spectacular 生成）：改接口必须同步更新，否则门禁失败。
- CI 为 `ci-phase1.yml` 的 6 个 job：`backend-check` · `frontend-check` · `static-checks` · `security-scan` · `boundary-check` · `frontend-quality`。

---

## 📚 参考

| 文档 | 位置 | 说明 |
|------|------|------|
| 需求总纲 | `PRD-平台总需求` | 功能定位、用户旅程、模块职责边界、子模块索引 |
| 架构设计 | `ARCH-平台架构设计` | 运行时拓扑、分层规则、数据模型、执行内核、技术债 |
| 能力规格 | `openspec/specs/` | 每个能力的可验收需求与场景（数量随归档增长，以目录为准） |
| 变更记录 | `openspec/changes/archive/` | 已归档变更（含 Why / 设计 / 任务） |
| 开发规范 | `AGENTS.md` 及各层 `AGENTS.md` | 行为准则、模块防火墙、提交与 CI 约定 |
| 门禁清单 | `utils/check_gates.py` | 检查项与判定口径的唯一真相源 |

### 外部引用

| 项目 | 链接 |
|------|------|
| AgentScope 2.0 | <https://docs.agentscope.io/versions/2.0.3/zh/> |
| Element Plus | <https://element-plus.org/> |
| Vue Flow | <https://vueflow.dev/> |
| ECharts | <https://echarts.apache.org/> |
