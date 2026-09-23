# 开发文档管理（DEV_DOCS_README）

> 本仓**开发文档的索引与维护约定**。产品介绍看 [README.md](README.md)；协作规范看 [AGENTS.md](AGENTS.md)。
> 本文只回答三件事：**文档放哪** · **登录模块的文档全貌** · **改了代码要同步哪些文档**。
> 最后核对：2026-09-20 · 核对方式：逐目录 `glob` + 逐文档读头部，并与代码实测数字对账。

---

## 一、文档地图（去哪找 / 该放哪）

> **需求入口**：功能需求文档一律从 PRD 开始 —— `dev_docs/ARCH_PRD/PRD-需求总纲.md` → 各模块 `PRD-*` → `ARCH-*`。

| 目录 | 放什么 | 命名约定 | 与代码的关系 |
|---|---|---|---|
| `dev_docs/ARCH_PRD/` | 需求与架构 | `PRD-xx-模块.md` · `ARCH-xx-xxx.md` | 需求侧叙述；**规格真相源在 `openspec/specs/`** |
| `dev_docs/DEV_TEST/接口文档/` | 分端点接口契约 | `API-模块.md` | 真相源是 `urls.py` + `views.py` + `serializers.py` |
| `dev_docs/DEV_TEST/接口自动化测试/` | 接口层用例（黑盒 HTTP） | `接口自动化测试-模块.md` | 用例源 `tests/api/case/*.yaml` |
| `dev_docs/DEV_TEST/单元测试文档/` | 前端单元层用例 | `单元测试-模块.md` | 用例源 `frontend/tests/<模块>/` |
| `dev_docs/DEV_TEST/集成测试文档/` | 集成层用例 | `集成测试-模块.md` | 用例源 `tests/graybox/integration/` |
| `dev_docs/DEV_TEST/功能测试用例/` | 业务功能用例（黑盒视角） | `功能测试用例-模块.md` | 与 `tests/e2e/` 通过编号映射 |
| `dev_docs/项目笔记/` | 学习笔记（AgentScope 等） | 自由 | 无 |
| `dev_docs/代码库入门指南.md` | 新人上手 | 单文件 | 无 |
| `dev_docs/Agent Skill 技能/` | dev_docs 内自带的**技能副本**（`animal-island-ui-style` · `appliance-test-cases` · `codebase-onboarding`） | `SKILL.md` | 独立副本，不在 `.agents/skills/` 内 |
| `openspec/specs/` | **行为契约真相源**（当前 50 个能力） | `<capability>/spec.md` | 归档变更时由 delta 合并进来 |
| `openspec/changes/` | 在途变更提案 | `<change>/{proposal,design,tasks}.md` + `specs/` | 变更的**唯一合法入口** |
| `openspec/changes/archive/` | 已归档变更（带日期前缀） | `YYYY-MM-DD-<change>/` | 历史；引用旧路径属正常 |
| `temps/` | 临时产物 / 可视化 bundle（**gitignore**） | `<topic>-proto.html` | 可随时重生成，不入库 |
| `frontend/tests/*.md` | 前端测试资产登记 | `README.md` · `PRIORITY_TEMPLATE.md` · `PLAN-*.md` · `DESIGN-*.md` | 登记表需与 `frontend/tests/` 实际文件对账 |
| 各层 `AGENTS.md` | 就近约束（根 / apps / 模块 / frontend / tests / engines） | 固定名 | 约束是**强制的**，优先于本文 |

约定三条：

1. **临时文件一律进 `temps/`**，不要在仓库根或模块下新建临时文件。
2. **文档与代码双边同步**：改路径 / 字段 / 行数 / 用例数，必须同时改文档（见第四节矩阵）。
3. **行为契约只认 `openspec/specs/`**；PRD 是叙述，两者冲突时以 spec 为准。

---

## 二、登录模块文档全表

登录链路横跨 **前端登录页 + 前端会话基础设施 + 路由守卫 + 后端 accounts**，因此文档散在多个层次。按「需求 → 契约 → 接口 → 各层测试」排列：

| # | 文档 | 层次 | 规模（实测） | 主要真相源 |
|---|---|---|---|---|
| 1 | `dev_docs/ARCH_PRD/PRD-00-登录模块.md` | 业务功能需求 + 用例编号总表 | 663 行 | 代码 + `openspec/specs/` |
| 2 | `dev_docs/ARCH_PRD/ARCH-平台总体架构.md` | 架构（含前端 L0–L5 / 请求链路） | — | 代码 |
| 3 | `apps/accounts/AGENTS.md` | 后端模块约束（会话 / 唯一性 / 尾斜杠 / 错误码） | 44 行 | `openspec/specs/auth-session` |
| 4 | `dev_docs/DEV_TEST/接口文档/API-登录.md` | 接口契约（5 端点：login/register/refresh/logout/me） | 240 行 | `apps/accounts/{urls,views,serializers}.py` |
| 5 | `dev_docs/DEV_TEST/接口自动化测试/接口自动化测试-登录.md` | 接口层用例 | **39 条** | `tests/api/case/{login,register,refresh,logout,me}.yaml` |
| 6 | `dev_docs/DEV_TEST/单元测试文档/单元测试-登录.md` | 前端单元层用例 | **11 spec / 57 条** | `frontend/tests/login/{p0,p1}/` |
| 7 | `dev_docs/DEV_TEST/功能测试用例/功能测试用例-登录.md` | 业务功能用例 + E2E 编号映射 | 业务流 8 · 输入 20 · 交互异常 22 | `tests/e2e/test_login_e2e.py` |
| 8 | `tests/e2e/test_login_e2e.py` | 端到端（**用例即文档**） | **15 条** | `tests/e2e/selectors.py` |
| 9 | `frontend/tests/README.md` · `PRIORITY_TEMPLATE.md` | 前端测试资产登记 / 样板 | — | `frontend/tests/` 实际文件 |

> 第 6 条的单元测试文档是**逐条五字段**（用例名称 / 业务功能 / 测试目的 / 测试方法与步骤 / 断言逻辑），编号 `TC-FE-LOGIN-###`；第 5 条沿用 YAML 里的 `TC-LOGIN-###`。两者都与 PRD 的编号一一对应。

### 2.1 登录相关的 OpenSpec 规格（`openspec/specs/`）

| 能力 | 覆盖 |
|---|---|
| `auth-session` | 登出按 `sid` 作废整会话 · 认证端点鉴权姿态成对 · 公开端点 401 不刷新 |
| `auth-registration` | 注册用户名唯一性（DB 唯一约束 + 409） |
| `auth-form-validation` | 前后端校验文案与阈值两侧一致 |
| `auth-response-shape` | 认证 DTO 与后端响应形状一致 |
| `frontend-login-hand-drawn-hero` | 登录页视觉与两态（login / register），无账号切换提示态 |
| `frontend-sidebar-hand-drawn` | L1 侧栏视觉与交互（含账号区） |
| `frontend-l5-overlay` | 错误覆盖层必须跳出 transform 包含块（`append-to-body`） |
| `frontend-l0-design-tokens` · `frontend-l3-content-block` · `frontend-motion` | 登录页用到的令牌 / 内容块 / 动效约束 |
| `api-path-convention` · `api-endpoint-catalog` | 路径必须带尾斜杠 · 端点资产目录与路由表对账 |

### 2.2 登录相关的在途 / 已归档变更

- **在途**：登录线**已无在途变更**（当前活跃变更只有 `fix-l0-paper-bleed-through`）。
- **近期归档（登录线）**：`2026-09-20-remove-multi-account-pool`（移除多账号池，前端会话回归单账号；delta 已合并进 `auth-session` 与 `frontend-sidebar-hand-drawn`）· `2026-09-20-add-login-e2e-playwright-coverage` · `2026-09-20-close-auth-api-test-gaps` · `2026-09-20-login-hero-copy-relayout` · `2026-09-18-fix-auth-frontend-contract-gaps` · `2026-09-18-guard-auth-validation-parity` · `2026-09-17-revoke-session-on-logout` · `2026-09-17-fix-register-duplicate-race` · `2026-09-17-remove-login-switch-prompt-and-rule-line`。

---

## 三、技能清单（`.agents/skills/`，共 29 个）

技能按需加载，完整清单见会话技能目录。登录模块开发常用的是下面这些：

### 3.1 流程骨架（强约束）

| 技能 | 用途 | 何时用 |
|---|---|---|
| `openspec-explore` `openspec-propose` `openspec-new-change` `openspec-ff-change` | 探索 / 出提案与规格 | **任何行为变更的入口**（根 AGENTS.md 行为规范 1） |
| `openspec-apply-change` | 按 tasks 实施并勾进度 | 方案评审通过后 |
| `openspec-verify-change` `openspec-sync-specs` `openspec-update-change` `openspec-continue-change` | 校验 / 同步规格 / 改计划 / 续写产物 | 实施中或收尾 |
| `openspec-archive-change` `openspec-bulk-archive-change` | 归档（把 delta 合并进主 spec） | 完成后 |
| `openspec-onboard` | 流程入门 | 新人 |

### 3.2 前端与视觉

| 技能 | 用途 |
|---|---|
| `frontend-change-plan` | 写平台代码**之前**产出「自包含 HTML 方案 + 可点原型」，放 `temps/<topic>-proto.html` |
| `doodle-craft` | Doodle Craft 主题：令牌唯一真相源是 `frontend/src/shared/styles/tokens.css` |
| `vue` · `vue-frontend-check` | Vue 3 写法参考 · 前端关单门禁（布局裁剪 / 字号 / 契约 / 可达性） |
| `frontend-design` · `ui-ux-pro-max` · `web-design-guidelines` · `prototype-design` | 视觉方向 / 设计智能 / 可用性审查 / 高保真原型 |

### 3.3 校验与审查

| 技能 | 用途 |
|---|---|
| `boundary-check` | 模块边界 · 引擎边界 · 通信通道边界三合一检查 |
| `django-backend-check` | 后端关单门禁（check / ruff / 迁移 / 写库收敛 / 信封 / 行数） |
| `reviewer` | 代码质量审查（正确性 / 安全 / 性能 / 规范） |

### 3.4 产物与交付

| 技能 | 用途 |
|---|---|
| `html-report` | **纯文字类报告**（分析 / 质量 / 测试）的统一设计规范；它与 `frontend-change-plan` 分工不同（界面原型走后者） |
| `archify` · `archify-review` | 架构 / 时序 / 数据流 / 状态图（可交付 HTML）· 基于价值-成本-影响的维护决策 |
| `github-manager` | 提交 / 分支 / PR / Issue / 发布（Conventional Commits） |
| `skill-creator` · `find-skills` | 造技能 / 找技能 |

---

## 四、维护约定：改了代码要同步哪些文档

登录模块的「改动 → 必同步」矩阵（依据各层 `AGENTS.md` 与实测）：

| 你改了什么 | 必须同步 |
|---|---|
| `apps/accounts` 的路径 / 字段 / 错误码 | `API-登录.md` · `接口自动化测试-登录.md` · PRD 的「API契约」与「数据表单」· `apps/accounts/AGENTS.md` · spec `auth-session` / `auth-response-shape` / `api-path-convention` |
| 登录页交互 / 文案 / 视图态 | `PRD-00-登录模块.md` §UI交互 · `功能测试用例-登录.md` · `tests/e2e/test_login_e2e.py` |
| 前端会话 / 令牌读写（`shared/auth/`、`api-*`） | PRD「数据表单」· `单元测试-登录.md` · `frontend/tests/README.md` 与 `PRIORITY_TEMPLATE.md` · spec `auth-session` |
| 路由守卫 / 重定向规则 | PRD「会话与账号管理」· `功能测试用例-登录.md`（E2E 映射）· `tests/e2e/test_login_e2e.py` |
| 测试加减（spec 数 / 用例数变化） | `单元测试-登录.md` 文首「规模」+ 文末「实测」+ 用例文件清单 · PRD §测试 的覆盖清单与规模行 · `frontend/tests/README.md` |
| 任何**行为**变化 | 先走 OpenSpec change；归档时 delta 合并进 `openspec/specs/`（**不要手改主 spec**） |

### 命令速查

```bash
# 前端登录模块单元测试（11 spec / 57 用例）
cd frontend && npx vitest run tests/login
cd frontend && node tests/run.mjs html tests/login      # 附带 HTML 报告

# 端到端（需 python run.py start；15 条，零密钥）
python -m pytest tests/e2e -q

# 接口层（需后端 :8766）
python -m pytest tests/api/test_login_page.py tests/api/test_auth_tokens.py -q

# 灰盒单元 / 契约对拍
python -m pytest tests/graybox/unit -q

# 前端门禁
cd frontend && npm run lint && npm run lint:styles && npm run typecheck

# 架构红线 / 文档漂移
python tools/gen_arch_stats.py --check-boundaries
python tools/gen_arch_stats.py --check-md --doc <架构文档路径>
```

---

## 五、已知不一致（照实登记，未擅自修改）

| # | 位置 | 问题 | 影响 |
|---|---|---|---|
| 1 | `dev_docs/代码库入门指南.md:107,108` · `dev_docs/DEV_TEST/接口文档/API-元素定位.md:5` | 仍引用**已不存在**的旧路径 `dev_docs/03-设计与架构/`、`dev_docs/05-开发与测试/`（实际为 `dev_docs/ARCH_PRD/`、`dev_docs/DEV_TEST/`） | 照文档找路径会扑空；归档变更里的同类引用属历史，可不动 |
| 2 | `frontend/tests/README.md` 模块注册表 | login 行文件数写 `8 / 3`，实测为 **9 / 2**（总数 11 正确） | 数字误导；该偏差在移除多账号之前就存在 |
| 3 | `frontend/tests/PLAN-module-classification.md` | 同一张注册表且整份为**历史规划**（还写着 devices/inspector/elements/cases 等旧模块名） | 建议标注为历史或删除，单改一行无意义 |
| 4 | `tools/generate_report.py:80` | 文案仍写「导航到 `/login?add=1`，跳过已登录账号切换提示」，该例外已随多账号移除 | 文字与**冻结截图**配对，只改文案会图文打架 |
| 5 | `frontend/tests/reports/` · `tests/reports/` | gitignore 的可再生产物，可能停留在旧数字（如 59 用例） | 重跑对应命令即刷新，不作为依据 |

> 发现新的不一致：请**登记到本表**并说明原因，不要静默改掉相邻文档（根 AGENTS.md 行为规范 3）。
