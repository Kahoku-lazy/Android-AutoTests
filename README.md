<div align="center">

# 🐾 Android-AutoTests

**AI 驱动的 Android UI 自动化测试平台**

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0.x-green.svg)](https://www.djangoproject.com/)
[![Vue](https://img.shields.io/badge/Vue-3.4-brightgreen.svg)](https://vuejs.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-2.0.9%2B-orange.svg)](https://docs.agentscope.io/)
![Theme](https://img.shields.io/badge/theme-Doodle%20Craft-f5a623.svg)

</div>

---

## 📖 项目简介

> 面向 Android 测试工程师的 AI 自动化平台：把用例写成文档，把任务交给 AI 双角色（**执行 + 验收**）跑完，结果回到**任务事件时间线**与**测试报告**，全过程可回看、可取证。

### 价值主张

| 维度 | 传统方式 | Android-AutoTests |
|------|---------|-------------------|
| **用例编写** | 写脚本 / 录制回放 | 项目 → 目录 → 文件 → 用例 → 步骤 五层文档式用例，只写「操作 / 预期」 |
| **执行** | 人盯设备 | 一键下发任务：执行角色操作设备，验收角色用**截图 + 设备日志关键词**判定 |
| **失败定位** | 翻日志 | 任务事件时间线（模型调用 / 工具调用 / 判决）+ 步骤截图缩略图 + 日志证据；失败会进 BUG 单 |
| **设备管理** | 手工 adb | USB / WiFi 接入、占用锁、心跳巡检、同设备串行 / 异设备并行 |
| **观测** | 多份日志 | 后端 / 智能体 / 设备 / 串口 四组日志 + 仪表盘趋势与模型费用 |

### 产品边界

**本期范围**：Android 8.0+ UI 自动化 · USB + WiFi ADB · JWT 认证 · 文档式用例 · 设备执行 SOP（执行 + 验收）与用例编写 SOP（规划 + 编写 + 验收）· 知识库助手实时语音 · 设备日志取证 · MySQL / SQLite + Redis · 任务事件、报告与 BUG 单

**非本期**：iOS、Web、API 自动化 · 设备云租用 · 多团队隔离 · OAuth / SSO · AI 自我修复失败用例 · 分布式执行集群

模型与工具**不由页面配置**。设备执行和用例编写的模型、密钥、工具包都写死在 `engines/agents`：DeepSeek Flash，密钥只读环境变量 `DEEPSEEK_API_KEY`。阿里百炼（`DASHSCOPE_API_KEY`）只服务知识库助手的实时语音，不参与设备 SOP。

---

## 🏗️ 架构概览

```
Vue SPA :5173 ──HTTP(/api,/media)──▶ Vite 代理 ──▶ Daphne :8766 (ASGI)
         └──WS(/ws)──▶ Vite 代理 ──▶ /ws/knowledge-assistant/   （仅知识库助手）
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
                       │  AgentScope（Django 进程内，SOP 写死在引擎）       │
                       │  设备执行：executor 操作设备 → verifier 截图+查日志  │
                       │  用例编写：planner → writer → verifier             │
                       │  模型 / 工具 / 密钥：engines/agents + DEEPSEEK_API_KEY │
                       └────────────────────────┬────────────────────────┘
                                                │
                          纯 adb 点击/滑动/截图/启停；u2 仅按需补 xpath 与非 ASCII 输入
                                     Android 设备 ＋ 设备日志（默认 TCP :7005）
```

| 层 | 技术 | 说明 |
|----|------|------|
| **前端** | Vue 3.4 + Vite 5 + Element Plus + Pinia | 10 个业务模块，Doodle Craft 手绘主题，唯一 HTTP 出口 `frontend/src/shared/api-client.ts` |
| **后端** | Django 6.0.x（锁定 `Django==6.0.6`）+ DRF + Daphne | 12 个 App、21 张业务表；契约基线 `openspec/openapi.yaml`（当前 71 条 path、93 个 operation） |
| **AI 引擎** | AgentScope ≥ 2.0.9，跑在 Django 进程内 | 角色在 `engines/agents/role/`。平台只传任务与 YAML，**不注入**模型、密钥或工具清单 |
| **设备控制** | ADB 为主 | `AndroidControl` 继承纯 adb 控制；uiautomator2 只在 xpath 查找和非 ASCII 输入时按需连接。上层不得直接 import `uiautomator2` |
| **数据** | MySQL（默认）/ SQLite + Redis | 自有表前缀 `ai_ bug_ cm_ dp_ rg_ sl_ task_ wf_`。Redis 承载 JWT 吊销与 Channels layer |
| **实时性** | 任务走 HTTP 轮询 | 唯一 WebSocket 生产点是知识库助手 `/ws/knowledge-assistant/`（单连接，不走 channel layer）。任务进度不得复用这条通道 |

Django 版本锁在 6.0.x：6.1 的模型字段检查会在没有数据库时连 MySQL，CI 的 `manage.py check` 会因此失败。

### 模块地图

侧栏 10 个页面与 12 个 Django App 对应关系如下。`accounts` 复用 Django `auth_user`；`dashboard` 与 `knowledge_assistant` 无业务表。

| 模块 | 表前缀 | 数据表 | 核心能力 |
|------|--------|--------|---------|
| **登录鉴权** `accounts` | `auth_` | 复用 `auth_user` | 登录 · 注册 · 刷新 · 登出 · 当前身份；JWT 双令牌 + Redis 吊销 |
| **仪表盘** `dashboard` | — | — | KPI · 执行趋势 · 任务结果 · 模型用量与费用 · 活动时间线 |
| **设备管理** `device_pool` | `dp_` | 2 | 扫描 · 连接 · 断开 · 激活 · 占用锁 · 心跳 · 释放 |
| **用例管理** `case_manager` | `cm_` | 5 | 项目 → 目录 → 文件 → 用例 → 步骤；移动 / 批量删 |
| **AI 助手** `ai_assistant` | `ai_` | 1（`ai_agents`） | 智能体身份（名称 / 头像 / 标签 / 描述）与任务类型。页面不再编辑模型线路 |
| **用量账本** `usage_ledger` | `ai_` | 1（`ai_usage_records`） | 每次模型调用一条明细；无独立页面，仪表盘读取 |
| **任务清单** `task_list` | `task_` | 5 | 提交 / 重跑 / 取消 · 事件与用量 · 任务流程报告 · 截图缩略图 |
| **测试报告** `report_generator` | `rg_` | 2 | 报告列表 · 任务报告 · 用例细分 · 下载与在线预览 |
| **页面流** `workflow` | `wf_` | 3 | 原型 · 目录 · JSON 文档；VueFlow 画布编排与导入导出 |
| **串口日志** `serial_log` | `sl_` | 1 | 端口监听开关 · 当前日志只读 · 关键词对照表 |
| **BUG 单** `bug_manager` | `bug_` | 1 | 任务失败的分类台账；删任务不删单 |
| **知识库助手** `knowledge_assistant` | — | — | 实时语音。HTTP 只提供就绪状态，音频走 WebSocket |

### 一次任务是怎么跑的

智能体记录只决定**归属和任务类型**（`device_control` 设备执行 / `case_authoring` 用例编写）。`backend/apps/task_list/engine_adapter.py` 不再读取 `route_configs`，也不再构造 `ModelConfig`。

1. **建用例**：用例管理工作台里写「项目 → 目录 → 文件 → 用例 → 步骤（操作 / 预期）」。用例编写类任务改为上传需求文档，由编写 SOP 产出文档。
2. **下发任务**：任务清单页（`/tasks`）选择已有智能体、目标设备、附件与用例标题后提交。同一设备串行，不同设备并行。
3. **装配**：平台把用例物化成临时 YAML，起后台线程调用 `engines.agents.workflow.platform_run.run_platform_sop`。模型、工具、提示词在引擎内写死：`build_executor()` / `build_verifier()` 使用 `DeepSeekModelConfig.FLASH`（`deepseek-flash`）和 `DEEPSEEK_API_KEY`。
4. **执行 + 验收**：执行角色按步骤操作设备（最多 60 轮）；验收角色截图、查设备日志关键词，判过 / 不过（最多 30 轮）。用例编写任务走规划 / 编写 / 验收，不操作设备，密钥同样来自 `DEEPSEEK_API_KEY`。
5. **落库与回看**：过程事件写入任务事件表（含 token 与费用）。步骤截图压成长边 720px 的 WebP，落在 `DATA_DIR/task_media/<任务 id>/<sha256>.webp`。任务详情回放时间线，报告页按用例汇总，失败进入 BUG 单。

换模型只改 `engines/agents/role/agents.py`（以及用例编写的 `engines/agents/role/case_roles.py`）和 `engines/agents/config/models.py`。不要在 Django 模型或前端把密钥再传一遍。备用模型由 `AGENT_FALLBACK_MODEL` 控制，默认关闭；没有特殊要求不要回退到 Pro。

---

## 🚀 环境配置

### 前置依赖

与 CI（`.github/workflows/ci-phase1.yml`）对齐：

| 依赖 | 版本要求 | 检查命令 |
|------|---------|---------|
| Python | 3.13（`ruff.toml` 的 `target-version = "py313"`） | `python --version` |
| Node.js | 20 | `node --version` |
| MySQL | 默认引擎；也可 `DB_ENGINE=sqlite` | 客户端能连上 `DB_HOST` |
| Redis | 本机 `redis-server`，默认 6379 | `redis-cli ping` |
| ADB | 在 `PATH` 中 | `adb version` |

### 安装

```bash
git clone https://github.com/Kahoku-lazy/Android-AutoTests.git
cd Android-AutoTests

python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cd frontend && npm install && cd ..

cp .env.example .env
# 至少改这几项：DJANGO_SECRET_KEY、DB_*、DEEPSEEK_API_KEY
# 要用知识库助手再填 DASHSCOPE_API_KEY；不填时该页显示「未就绪」，不影响其它模块

python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@local','admin123')
"
```

`admin` / `admin123` 只用于本机引导。共享或生产环境请改掉，不要把口令写进仓库。

`.env.example` 里的 `AI_TOOL_GATEWAY_TOKEN` 没有运行时读取方（`/api/ai/tools/*` 已退役），留空即可。

数据库默认 MySQL（`DB_ENGINE=mysql`）。改成 `DB_ENGINE=sqlite` 时，库文件是仓库根目录的 `db.sqlite3`，不是 `data/` 下面那个历史路径。

### 启动

```bash
python run.py start      # Redis :6379 + Daphne(:8766) + Vite(:5173)
python run.py stop       # 停后端前先排空运行中任务；不停止 Redis
python run.py restart
python run.py status     # 三个服务是否 ONLINE
python run.py logs       # 各服务日志尾部
python run.py check      # 本地质量门禁（与 CI 同一批检查，不跑全量回归）
```

也可以只操作其中一个：`python run.py start backend`。后端端口由 `SERVER_PORT` 控制，默认 8766；前端固定 5173。`run.py stop` 等待运行中任务结束，上限 `STOP_DRAIN_TIMEOUT`（默认 180 秒），超时后强制停。

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | `http://localhost:5173` | Vite。`/api`、`/media`、`/ws` 代理到后端 |
| 后端 API | `http://localhost:8766/api/` | REST JSON，统一 `{status, data}` 信封 |
| API 文档 | `http://localhost:8766/api/swagger/` | drf-spectacular；Swagger 静态资源随包分发 |
| 管理后台 | `http://localhost:8766/admin/` | Django Admin（Jazzmin） |
| AI 引擎 | 无独立端口 | AgentScope 在 Daphne 进程内运行 |
| 知识库语音 | `ws://localhost:5173/ws/knowledge-assistant/` | 浏览器连 Vite，由 Vite 转到 Daphne；query 带 access token |

---

## 🗂️ 目录结构

| 目录 | 作用 |
|------|------|
| `backend/` | Django 项目：`config/`（settings、ASGI、env）、`apps/`（12 个 App）、`gateway/`（JWT 与 WebSocket 路由）、`shared/`（JWT、响应信封、schema）、`models/`（跨模块枚举） |
| `engines/agents/` | SOP 唯一装配处：`role/` 角色与模型、`tools/` + `tools_config.py` 工具、`prompts/` 提示词、`workflow/` 单次运行、`messaging/` 事件与费用、`middleware/`、`rag/`、`realtime_vocie/` 知识库语音 |
| `engines/device/` | Android 设备连接与 adb 控制。业务代码只经 `engines.device.action` |
| `engines/uart_log/` · `engines/vision/` | 串口采集 · OCR（`ocr_page` 默认不装配给角色） |
| `frontend/` | Vue SPA。业务在 `src/modules/`（10 个模块），共享件与设计令牌在 `src/shared/` |
| `utils/` | `logs.py` 四组运行日志，以及质量门禁、架构统计等开发脚本。业务代码可以 import `utils.logs`，其余脚本用 `python utils/xxx.py` 调用 |
| `tests/` | 测试资产都在这里。入口：`python -m pytest -c tests/pytest.ini` |
| `openspec/` | 能力规格 `specs/`、变更 `changes/`、OpenAPI 基线 `openapi.yaml` |
| `dev_docs/ARCH_PRD/` | 需求总纲与架构设计 |
| `dev_docs/DEV_TEST/` | 设计方案、分析报告、接口说明 |
| `data/` | **运行时数据根**，已 gitignore。截图、上传、任务媒体、头像、RAG 索引都在这里。可用环境变量 `DATA_DIR` 指到仓库外的磁盘 |
| `temps/` | **临时沙箱**，已 gitignore。探针、调试截图、门禁产物放这里。可以整目录清空 |
| `logs/` | 运行日志：`backend.log` · `frontend.log` · `redis.log` · `agents/agent_events.log` · `device.log` · `serial.log` · `serial_logs/` |

### `temps/` 与 `data/` 的边界

| | `temps/` | `data/`（或 `DATA_DIR`） |
|--|----------|--------------------------|
| 是什么 | 生成物沙箱 | 平台运行时媒体与用户数据 |
| 能否删除 | 可以整目录清空，不影响源码 | 删了会丢掉截图、上传文件、任务缩略图、RAG 索引 |
| 能否当真相源 | 不能。不要把要提交的代码、规格或用例放进来 | 不能进 Git。要长期保留的业务事实在数据库里，文件只是媒体 |

任务缩略图、上传附件、设备截图目录都落在 `DATA_DIR`（默认仓库根 `data/`：`task_media/`、`uploads/`、`screenshots/`）。调试时随手生成的文件放 `temps/`。

---

## 📐 开发约定

**请求链路**：前端模块 `api.ts` → `djangoClient`（`/api`）→ Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status, data}`）→ ORM。

**分层纪律**：`urls.py`（路径真相源）→ View/ViewSet（只分发）→ Serializer（契约）→ `api.py`（唯一写库口）→ ORM。跨 App 可以读 Model，写必须走对方 `api.py`。

**智能体纪律**：改执行 / 验收的模型、工具、提示词，只动 `engines/agents`。Django 不把 `ai_agents.route_configs` 或页面上的密钥传给 SOP。`engines/agents` 不得 import `backend.apps.*`。

**功能开发**走 OpenSpec 四步：explore → propose → apply → archive。规格在 `openspec/`。

**硬约束**：

1. `/api/` 路径一律以 `/` 结尾（`APPEND_SLASH = False`，缺斜杠是确定的 404）。
2. 响应信封 `{status, data}`；错误 `{status, message}` + 对应 HTTP 状态码；JSON 字段 snake_case。
3. 新表前缀先登记到 `utils/gen_arch_stats.py` 的 `TABLE_PREFIX`。当前自有前缀：`ai_ bug_ cm_ dp_ rg_ sl_ task_ wf_`。
4. 前端只有一个 HTTP 出口（`frontend/src/shared/api-client.ts`），业务模块不得另起 axios 实例或裸 `fetch`。
5. 上层不得直接 import `uiautomator2`，设备操作一律经 `engines.device`。
6. 前端 UI 默认遵循 Doodle Craft：设计令牌只在 `frontend/src/shared/styles/tokens.css` 登记，不写颜色 / 字号字面量。
7. 临时文件进 `temps/`，运行时媒体进 `data/`（或 `DATA_DIR`）。两者都不要提交。

**版本控制**（见根目录 `AGENTS.md`）：

- 长期分支只有 `Kahoku`。Conventional Commits：`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。
- 一次提交只做一件事。逐文件 `git add`，不要 `git add -A`。禁止对 `Kahoku` 强推。
- 提交前跑 `python run.py check`。推送后确认 `ci-phase1.yml` 的 6 个 job 全绿。

---

## ✅ 质量门禁

```bash
python run.py check      # 本地门禁，阻塞项失败则退出码 1
python -m pytest -c tests/pytest.ini   # 全量用例；check 不会跑这个
```

- 检查清单以 `utils/check_gates.py` 为唯一真相源（当前 24 项：22 个阻塞项；`cred-default-pwd` 与 `inline-style` 只告警，不影响退出码）。
- 覆盖：Django system check、ruff（平台范围与 `engines/`）、pytest **收集**（不执行用例）、OpenAPI 契约（生成 + 校验 + 与 `openspec/openapi.yaml` 一致）、OpenAPI 覆盖（业务路径必须全部入基线）、前端 vitest / vite build / eslint / vue-tsc / prettier、硬编码凭据扫描、模块边界、Vue 文件体积、伪造数据、内联样式与静默吞异常。
- 改接口必须同步 `openspec/openapi.yaml`，否则门禁失败。
- CI 为 `.github/workflows/ci-phase1.yml` 的 6 个 job：`backend-check` · `frontend-check` · `static-checks` · `security-scan` · `boundary-check` · `frontend-quality`。推送到 `Kahoku`，以及指向 `Kahoku` 的 pull request，都会跑这套检查。

---

## 📚 参考

| 文档 | 位置 | 说明 |
|------|------|------|
| 需求总纲 | `dev_docs/ARCH_PRD/PRD-平台总需求.md` | 功能定位、用户旅程、模块职责 |
| 架构设计 | `dev_docs/ARCH_PRD/ARCH-平台架构设计.md` | 运行时拓扑、分层、数据模型。与本 README 冲突时，以代码和本 README 的引擎装配说明为准 |
| 能力规格 | `openspec/specs/` | 每个能力的可验收需求与场景 |
| 变更记录 | `openspec/changes/archive/` | 已归档变更 |
| 开发规范 | 根目录 `AGENTS.md`，以及 `backend/`、`frontend/`、`engines/` 下的 `AGENTS.md` | 分层、模块防火墙、提交与 CI |
| 门禁清单 | `utils/check_gates.py` | 检查项与判定口径 |
| 环境变量样例 | `.env.example` | 数据库、Redis、JWT、DeepSeek、知识库助手、可选的模型重试与 RAG |

### 外部引用

| 项目 | 链接 |
|------|------|
| AgentScope 2.0 | <https://docs.agentscope.io/versions/2.0.3/zh/> |
| Element Plus | <https://element-plus.org/> |
| Vue Flow | <https://vueflow.dev/> |
| ECharts | <https://echarts.apache.org/> |
