<div align="center">

# 🐾 Android-AutoTests

**AI 驱动的 Android UI 自动化测试平台**

[![CI](https://github.com/Kahoku-lazy/Android-AutoTests/actions/workflows/ci-phase1.yml/badge.svg?branch=Kahoku)](https://github.com/Kahoku-lazy/Android-AutoTests/actions/workflows/ci-phase1.yml)
[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0.6-green.svg)](https://www.djangoproject.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org/)
[![AgentScope](https://img.shields.io/badge/AgentScope-2.0.12%2B-orange.svg)](https://docs.agentscope.io/)
![Theme](https://img.shields.io/badge/theme-Doodle%20Craft-f5a623.svg)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**中文** | [English](README.en.md)

</div>

---

## 📖 项目简介

> 面向 Android 测试工程师的 **AI Agent 平台**：**前端展示 · 后端通道与记账 · `engines/` 能力核心**。一个 Agent **角色** = **Model + Harness**。当前主场景：把已发布的工作流交给 SOP（**执行者动手 + 验收者核对**）跑完，结果回到**任务**与**测试报告**。这是首个落地场景，不是平台上限。平台总思路见根目录 `AGENTS.md`。

### 价值主张

| 维度 | 传统方式 | Android-AutoTests |
|------|---------|-------------------|
| **用例编写** | 写脚本 / 录制回放 | 项目 → 用例行 → 步骤。项目创建时锁定库类型（自动化 / 功能），行直接属于项目 |
| **执行** | 人盯设备 | 从已发布工作流下发任务：执行角色操作设备，验收角色只拿只读工具核对 |
| **失败定位** | 翻日志 | 任务结果带每步结论；HTML 报告落在 `logs/agents/backend_bridge/`；失败进入 BUG 单 |
| **设备管理** | 手工 adb | USB / WiFi 接入、占用锁、心跳巡检、同设备串行 / 异设备并行 |
| **观测** | 多份日志 | 仪表盘看趋势与模型费用；用量写入 `ai_usage_records`。运营可配模型、Agent 与用户 |

### 产品边界

**本期范围**：Android UI 自动化 · USB + WiFi ADB · JWT 认证 · 用例库（自动化 / 功能两库）· 已发布 SOP 工作流（设备执行 / 用例编写 / 需求拆解）· 平台助手对话 · 知识库只读检索与评测 · 运营后台（用户 / Agent / 模型）· MySQL / SQLite · 任务、报告台账与 BUG 单

**非本期**：iOS、Web、API 自动化的执行引擎 · 设备云租用 · 多团队隔离 · OAuth / SSO · AI 自我修复失败用例 · 分布式执行集群 · 实时语音（知识库助手 WebSocket 已下线，`websocket_urlpatterns` 为空）

模型与密钥**不在页面上填写明文**。运营在「模型配置」登记厂商、密钥环境变量名、协议、地址和模型名；密钥只从仓库根 `.env` 读取。当前三家：`DEEPSEEK_API_KEY`、`DASHSCOPE_API_KEY`、`OPENAI_API_KEY`。平台助手与已发布工作流在运行时读取这些配置，并把厂商、密钥名、地址、模型名显式传给 `create_agent`。没有模型短名，也没有写死的默认角色。

---

## 🏗️ 架构概览

```
Vue SPA :5173 ──HTTP(/api,/media)──▶ Vite 代理 ──▶ Daphne :8766 (ASGI)
                                                 │
                                   JWTAuthenticationMiddleware
                                                 │
                                         DRF View / ViewSet
                                                 │
                                           api.py（唯一写库口）
                                                 │
                                     MySQL / SQLite
                                                 │
              backend/apps/task_list  ──调用──▶  engines/backend_bridge
              （取运营配置、写任务 / 用量 / 事件）   │  平台角色唯一落点
                                                 ▼
                                        engines/ae_harness
                                        原语：create_agent、adb 工具、SOP、事件与报告
                                                 │
                           纯 adb 点击 / 滑动 / 截图 / 启停；坐标用 0~1 归一化值
                                      Android 设备
```

依赖只有一条：**backend →（注入）→ `engines/backend_bridge` → `engines/ae_harness`**。`device/`、`vision/`、`uart_log/` 是底座，不得反向依赖上面两层。`engines/` 禁止 `import apps.*` / `django.*`。`engines/agents/` 已退役，禁止恢复为包。

| 层 | 技术 | 说明 |
|----|------|------|
| **前端** | Vue 3.5（声明 `^3.4`）+ Vite 6 + Element Plus + Pinia + TypeScript 5.4 | 10 个业务模块，Doodle Craft 手绘主题。HTTP 经各模块 `api.ts` 进入 `frontend/src/shared/api-client.ts` |
| **后端** | Django 6.0.6 + DRF + Daphne | 12 个 App。自有业务表 33 张（另复用 Django `auth_user`）。契约基线 `openspec/openapi.yaml`，当前 81 条 path |
| **AI 引擎** | AgentScope ≥ 2.0.12，跑在 Daphne 进程内 | 原语在 `ae_harness`；平台装配在 `backend_bridge`。角色只经 `create_agent` 创建 |
| **设备控制** | ADB | 对外入口 `engines.device.action`。角色侧工具是 `ae_harness` 的 `build_adb_tools()`（16 个）与只读子集（5 个）。验收角色不得挂写操作 |
| **数据** | MySQL（默认）/ SQLite | 自有表前缀 `acc_ ai_ bug_ cm_ dp_ ks_ sl_ task_`。`report_generator` 已无业务表。JWT 吊销记录落库（`acc_token_revocations`）。平台无外部 KV：Redis 已退役，channel layer 用内存实现 |
| **实时性** | HTTP 轮询 | 没有 WebSocket 生产点。任务进度不得再接语音通道 |

Django 锁在 6.0.x：6.1 的模型字段检查会在没有数据库时连 MySQL，CI 的 `manage.py check` 会因此失败。

### 模块地图

侧栏页面与 Django App 的对应关系如下。`accounts` 复用 `auth_user`；`dashboard`、`ops_console`、`report_generator` 没有自有业务表。

| 模块 | 表前缀 | 数据表 | 核心能力 |
|------|--------|--------|---------|
| **登录鉴权** `accounts` | `acc_` | 1（另复用 `auth_user`） | 登录 · 注册 · 刷新 · 登出 · 当前身份；JWT 双令牌 + 落库吊销 |
| **仪表盘** `dashboard` | — | — | KPI · 执行趋势 · 任务结果 · 模型用量与费用 · 活动时间线 |
| **设备管理** `device_pool` | `dp_` | 2 | 扫描 · 连接 · 断开 · 激活 · 占用锁 · 心跳 · 释放 |
| **用例管理** `case_manager` | `cm_` | 6 | 项目锁定库类型；自动化 / 功能用例与步骤分表；个人视图 |
| **平台助手** `ai_assistant` | `ai_` | 13 | 模型配置、Agent 配置（执行者 / 验收者 / 规划者）、助手名片、SOP 工作流、测试对话与评测 |
| **用量账本** `usage_ledger` | `ai_` | 1（`ai_usage_records`） | 每次模型调用一条明细；无独立页面，仪表盘读取 |
| **任务清单** `task_list` | `task_` | 5 | 从已发布工作流提交 / 重跑 / 关闭；同设备排队，异设备并行 |
| **测试报告** `report_generator` | — | — | 只读台账：已生成的 SOP 报告与助手报告。正文不在本 App 下载 |
| **串口日志** `serial_log` | `sl_` | 2 | 端口监听开关 · 当前日志只读 · 关键词对照表 |
| **BUG 单** `bug_manager` | `bug_` | 1 | 任务失败的分类台账；删任务不删单 |
| **知识库** `knowledge_search` | `ks_` | 3 | 模块登记、只读检索、自动评测。索引与检索在 `ae_harness/knowledge` |
| **运营后台** `ops_console` | — | — | 用户停用 / 启用 / 重置密码 / 授权；Agent 配置与模型配置页面挂在这里 |

### 一次任务是怎么跑的

任务必须从**已发布工作流**提交（`POST /api/tasks/submit/` 要求 `workflow_id`）。工作流只存名称和名片编号；提示词、模型连接参数和工具勾选在运行时现读，不复制进任务表。

1. **配角色**：运营在「模型配置」「Agent 配置」登记连接参数与系统提示词，再做成助手名片，最后收成 SOP 工作流并发布。
2. **下发**：设备执行类工作流要选设备和用例来源（平台用例，或上传一份里程碑 YAML）。用例编写 / 需求拆解改为上传文档，不占设备。同一设备串行，不同设备并行。
3. **装配**：`task_runner` 在后台线程调用 `engines.backend_bridge`，一律走 `run_bound_sop`：提示词、模型连接参数和工具勾选在运行时从名片现读。编排实现只在 `ae_harness/workflow/sop`，平台侧不得再写一套循环。
4. **执行 + 验收**：执行者挂全量 adb 工具；验收者只挂只读工具，按步骤 YAML 里「必须达成的结果」判定。用例编写与需求拆解不操作设备。
5. **落库与回看**：终态、用量和失败步骤写回任务。HTML 报告与 JSONL 落在 `logs/agents/backend_bridge/`。报告页只做已生成报告的台账；失败进入 BUG 单。

换一条平台角色的模型，改运营库里的模型配置，不要把密钥再传到 Django 或前端。`create_agent` 只收调用方传入的连接参数，不再有模型短名。

---

## 🚀 环境配置

### 前置依赖

与 CI（`.github/workflows/ci-phase1.yml`）对齐：

| 依赖 | 版本要求 | 检查命令 |
|------|---------|---------|
| Python | 3.13 | `python --version` |
| Node.js | 20 | `node --version` |
| MySQL | 默认引擎；也可 `DB_ENGINE=sqlite` | `python run.py status` 的 Database 行；`start` 会检测并尝试启动本机服务，远程库只检测 |
| ADB | `python run.py setup` 安装到 `tools/platform-tools/`；也可用 `ADB_PATH` 指向已有 adb | `python run.py setup --check` |

> adb 起不来并报 `cannot open ...\adb.log: Permission denied` 时，是 adb 37 在部分 Windows 上写 daemon 日志被拒；
> 平台已自动把 `ANDROID_ADB_LOG_PATH` 指向 `NUL` 规避，无需手工处理。

### 安装

```bash
git clone https://github.com/Kahoku-lazy/Android-AutoTests.git
cd Android-AutoTests

python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate

pip install -r requirements.txt
cd frontend && npm install && cd ..

# 安装项目内 adb（官方 platform-tools；首次/换机时执行，唯一会联网的命令）
python run.py setup

cp .env.example .env
# 至少改：DJANGO_SECRET_KEY、DB_*，以及实际要用的密钥
# DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / OPENAI_API_KEY 按模型配置填写；不把密钥写进页面或仓库

python manage.py migrate
python manage.py shell -c "
from django.contrib.auth.models import User
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin','admin@local','admin123')
"
```

`admin` / `admin123` 只用于本机引导。共享或生产环境请改掉，不要把口令写进仓库。

数据库默认 MySQL（`DB_ENGINE=mysql`）。改成 `DB_ENGINE=sqlite` 时，库文件是仓库根目录的 `db.sqlite3`，不是 `data/` 下面那个历史路径。

### 启动

```bash
python run.py setup      # 首次/换机：安装项目内 platform-tools（唯一会联网的命令）
python run.py start      # 先检测数据库 → Daphne(:8766) + Vite(:5173)
python run.py stop       # 停后端前先排空运行中任务
python run.py restart
python run.py status     # 服务、数据库、adb 状态
python run.py logs       # 各服务日志尾部
python run.py check      # 本地质量门禁（与 CI 同一批检查，不跑全量回归）
```

`start` 会先用 `.env` 的 `DB_*` 真实连一次数据库：本机不可达时尝试启动服务（`DB_SERVICE_NAME`，失败会打印提权命令并中止）；远程库只检测不启动。库由外部管理或 CI 环境可用 `python run.py start --no-db` 跳过检查（`DB_AUTOSTART=0` 则只关自动启动、仍检测）。

也可以只操作其中一个：`python run.py start backend`。后端端口由 `SERVER_PORT` 控制，默认 8766；前端固定 5173。`run.py stop` 等待运行中任务结束，上限 `STOP_DRAIN_TIMEOUT`（默认 180 秒），超时后强制停。

### 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端 | `http://localhost:5173` | Vite。`/api`、`/media` 代理到后端 |
| 后端 API | `http://localhost:8766/api/` | REST JSON，统一 `{status, data}` 信封 |
| API 文档 | `http://localhost:8766/api/swagger/` | drf-spectacular；Swagger 静态资源随包分发 |
| 管理后台 | `http://localhost:8766/admin/` | Django Admin（Jazzmin） |
| AI 引擎 | 无独立端口 | AgentScope 在 Daphne 进程内运行 |

---

## 🗂️ 目录结构

| 目录 | 作用 |
|------|------|
| `backend/` | Django 项目：`config/`（settings、ASGI、env）、`apps/`（12 个 App）、`gateway/`（JWT；WebSocket 路由表当前为空）、`shared/`（JWT、响应信封、schema）、`models/`（跨模块枚举） |
| `engines/ae_harness/` | **Agent 原语**：`agents/`（`create_agent`）、`tools/`（adb 等）、`workflow/sop/`（SOP 抽象与步骤 YAML）、`event/`、`middleware/`、`knowledge/`（只读检索）。`assistant/` 只服务控制台调试，平台不得调用 |
| `engines/backend_bridge/` | **平台角色唯一落点**：在原语上装配执行者 / 验收者，跑 SOP，整理报告路径与用量。报告根目录 `logs/agents/backend_bridge/` |
| `engines/device/` | Android 设备连接与控制。业务代码只经 `engines.device.action` |
| `engines/uart_log/` · `engines/vision/` | 串口采集 · OCR。二者不得反向依赖 `backend_bridge` 或 `ae_harness` |
| `frontend/` | Vue SPA。业务在 `src/modules/`（10 个模块），共享件与设计令牌在 `src/shared/` |
| `utils/` | 运行日志，以及质量门禁、架构统计等开发脚本 |
| `tests/` | 测试资产都在这里。入口：`python -m pytest -c tests/pytest.ini` |
| `openspec/` | 能力规格 `specs/`、变更 `changes/`、OpenAPI 基线 `openapi.yaml` |
| `dev_docs/ARCH_PRD/` | 需求与架构文档 |
| `dev_docs/DEV_TEST/` | 设计方案、分析报告、接口说明 |
| `data/` | **运行时数据根**，已 gitignore。截图、上传、任务媒体都在这里。可用 `DATA_DIR` 指到仓库外 |
| `temps/` | **临时沙箱**，已 gitignore。探针、调试截图、门禁产物放这里。可以整目录清空 |
| `tools/platform-tools/` | **本地 adb**，已 gitignore。由 `python run.py setup` 安装；也可用 `ADB_PATH` 指向其它 adb |
| `logs/` | 运行日志。平台 Agent 报告在 `logs/agents/backend_bridge/` |

### `temps/` 与 `data/` 的边界

| | `temps/` | `data/`（或 `DATA_DIR`） |
|--|----------|--------------------------|
| 是什么 | 生成物沙箱 | 平台运行时媒体与用户数据 |
| 能否删除 | 可以整目录清空，不影响源码 | 删了会丢掉截图、上传文件、任务媒体 |
| 能否当真相源 | 不能。不要把要提交的代码、规格或用例放进来 | 不能进 Git。要长期保留的业务事实在数据库里，文件只是媒体 |

任务媒体、上传附件、设备截图目录都落在 `DATA_DIR`（默认仓库根 `data/`：`task_media/`、`uploads/`、`screenshots/`）。调试时随手生成的文件放 `temps/`。

---

## 📐 开发约定

**请求链路**：前端模块 `api.ts` → `djangoClient`（`/api`）→ Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status, data}`）→ ORM。

**分层纪律**：`urls.py`（路径真相源）→ View/ViewSet（只分发）→ Serializer（契约）→ `api.py`（唯一写库口）→ ORM。跨 App 可以读 Model，写必须走对方 `api.py`。

**智能体纪律**：平台角色只在 `engines/backend_bridge` 装配，原语只来自 `engines/ae_harness`。不得 `import engines.ae_harness.assistant`，不得直接 `Agent(...)`。系统提示词由调用方传入正文，来源是运营配置库。`engines/` 不得 import `backend.apps.*` 或 `django.*`。

**功能开发**走 OpenSpec 四步：explore → propose → apply → archive。规格在 `openspec/`。

**硬约束**：

1. `/api/` 路径一律以 `/` 结尾（`APPEND_SLASH = False`，缺斜杠是确定的 404）。
2. 响应信封 `{status, data}`；错误 `{status, message}` + 对应 HTTP 状态码；JSON 字段 snake_case。
3. 新表前缀先登记到 `utils/gen_arch_stats.py` 的 `TABLE_PREFIX`。当前自有前缀：`acc_ ai_ bug_ cm_ dp_ ks_ sl_ task_`。
4. 前端业务请求走 `frontend/src/shared/api-client.ts`，模块不得另起一套客户端。
5. 上层不得绕过 `engines.device.action` 去 import `engines.device.android`。验收角色固定 `build_adb_readonly_tools()`。
6. 前端 UI 默认遵循 Doodle Craft：设计令牌只在 `frontend/src/shared/styles/tokens.css` 登记，不写颜色 / 字号字面量。
7. 临时文件进 `temps/`，运行时媒体进 `data/`（或 `DATA_DIR`）。两者都不要提交。

**版本控制**（见根目录 `AGENTS.md`）：

- 长期分支只有 `Kahoku`。Conventional Commits：`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。
- 一次提交只做一件事。逐文件 `git add`，不要 `git add -A`。禁止对 `Kahoku` 强推。
- 提交前跑 `python run.py check`。推送后确认 `ci-phase1.yml` 的 `python` 与 `frontend` 两个 job 全绿。

---

## ✅ 质量门禁

```bash
python run.py check      # 本地门禁，阻塞项失败则退出码 1
python -m pytest -c tests/pytest.ini   # 全量用例；check 不会跑这个
```

- 检查清单以 `utils/check_gates.py` 的 `build_gates()` 为真相源。当前 32 项：29 个阻塞项；`cred-default-pwd`、`inline-style`、`engines-agents-style` 只告警，不影响退出码。模块依赖（每个包的允许清单 + 禁止合同，含间接链与第三方包）由 `linting` 一条门禁承担，配置是仓库根的 `.linting`，规则与红线见 `.agents/lint/linting.md`。
- 覆盖：Django system check、ruff（平台范围、`tests/` 与 `engines/`，版本钉在 `requirements.txt`）、迁移与模型一致、pytest **收集**（不执行用例）、OpenAPI 契约与业务路径覆盖、前端 vitest / vite build / eslint / vue-tsc / prettier / 样式令牌、硬编码凭据（含 `engines/` 与 `.ts`）、模块边界（含底座包不得反向依赖）、Vue 文件体积、伪造数据、内联样式、静默吞异常、`engines/agents` 退役守门，以及 `Agent(...)` 只能出现在 `creator.py`。
- 改接口必须同步 `openspec/openapi.yaml`，否则门禁失败。
- CI 为 `.github/workflows/ci-phase1.yml` 的 2 个 job：`python` · `frontend`。判定调用 `utils/check_gates.py --only`，不在 workflow 里另写一套命令。只在推送 `Kahoku` 和指向 `Kahoku` 的 pull request 时跑。

---

## 🤝 社区与贡献

所有改动走 **feature 分支 → PR → CI 全绿** 合入单主干 `Kahoku`（分支保护强制，管理员同样生效）。

| 入口 | 说明 |
|------|------|
| [贡献指南](CONTRIBUTING.md) | 环境准备、PR 流程、硬性规则 |
| [行为准则](CODE_OF_CONDUCT.md) | Contributor Covenant 2.1 |
| [安全策略](SECURITY.md) | 漏洞**私密报告**渠道，勿公开提 Issue |
| [变更日志](CHANGELOG.md) | Keep a Changelog 格式 |
| [Discussions](https://github.com/Kahoku-lazy/Android-AutoTests/discussions) | 问答、想法交流 |
| [Issues](https://github.com/Kahoku-lazy/Android-AutoTests/issues/new/choose) | Bug / 功能建议（含模板） |
| [Releases](https://github.com/Kahoku-lazy/Android-AutoTests/releases) | 版本发布与源码下载 |

---

## 📚 参考

| 文档 | 位置 | 说明 |
|------|------|------|
| 平台总思路 | 根目录 `AGENTS.md` | 三层分工、OpenSpec、提交与 CI |
| 引擎红线 | `engines/AGENTS.md`（红线 + 索引） | 原语与平台装配的边界；子模块细则见 `.agents/docs/engines/` |
| 后端 / 前端 | `backend/AGENTS.md`、`frontend/AGENTS.md` | 分层、契约、模块结构 |
| 能力规格 | `openspec/specs/` | 每个能力的可验收需求与场景 |
| 变更记录 | `openspec/changes/archive/` | 已归档变更 |
| 门禁清单 | `utils/check_gates.py` | 检查项与判定口径 |
| 环境变量样例 | `.env.example` | 数据库、JWT、三把模型密钥、重试与追踪 |

### 外部引用

| 项目 | 链接 |
|------|------|
| AgentScope | <https://docs.agentscope.io/> |
| Django 6.0 | <https://docs.djangoproject.com/en/6.0/> |
| Element Plus | <https://element-plus.org/> |
| ECharts | <https://echarts.apache.org/> |
