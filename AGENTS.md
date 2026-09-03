# AGENTS.md

## 行为准则

**编写/改动任何代码前，必须先加载 `android-autotests-rules` skill**（防火墙、架构红线、安全铁律、关键约定的唯一落点）。

1. **用最少的代码解决问题。不接受过度设计。** 不添加需求之外的功能。用户说"加个筛选条件"，不要顺便"优化整个表格组件"

2. **只碰必须碰的。只清理自己造成的混乱。** 不要"顺手"改进相邻代码、注释、格式。diff 中每一行都应能追溯到用户的请求

3. **将成功标准转化为可验证的目标。循环验证直到目标全部完成** 

4. **使用 openspec skill 的技能**

5. **先读文档，后写代码，不假设。不隐藏困惑。呈现权衡。** 

6. **不要重复造轮子** 


### 报错先诊断，不动手

**看到错误日志、堆栈、浏览器 console 报错、服务异常时，禁止直接猜原因改代码。** 必须先在文字中完成以下三步：

1. **复述现象**："我看到了什么"
2. **列出可能原因**："可能的根因有 A / B / C"
3. **提出验证计划**："下一步查什么来确认"


## 文档位置

1. 临时生成的代码与文件、临时生成的测试数据 **必须**放到 `temps/` 中，不要在项目根目录下生成临时文件

2. 设计方案与报告放在 `dev_docs/05-开发与测试/设计方案与报告` 路径中，文件名举例：设计方案-XXX.md/设计方案-XXX.html，报告-XXX.md/报告-XXX.html

3. 接口相关文档放在 `dev_docs/05-开发与测试/接口文档` 中，文件名举例：API-XXX.md/API-XXX.html

4. PRD 文档放在 `dev_docs/02-PRD需求` 中，文件名举例：PRD-XXX.md/PRD-XXX.html

5. 架构文档放在 `dev_docs/03-设计与架构` 中，文件名举例：ARCH-XXX.md/ARCH-XXX.html


## 工作偏好与经验教训

2. **命令/操作被拒 2 次即停**——不重复尝试第 3 次，直接告知用户手动执行
3. **方案/分析/流程文档额外输出 HTML**——Markdown 之外再生成 HTML，放`dev_docs/05-开发与测试/设计方案与报告`，风格对齐 `html-report` skill
4. **每个任务结束输出执行摘要**——用了哪些 Skill/工具、走了什么流程
5. **项目负责人思维**——发现问题 → 归类根因 → 提 ≥2 个方案 → 让用户决策；不假装知道、不猜测、不确定就问
6. **创建了专用技能/子代理就必须用**——不手动绕过；表现不好就改进定义，而不是弃用


## 项目工具

| 工具                                                  | 用途                 |
| --------------------------------------------------- | ------------------ |
| `python tools/gen_arch_stats.py`                    | 自动统计表/端点/Tool/步骤类型 |
| `python tools/gen_arch_stats.py --check-md`         | 检测文档是否落后代码         |
| `python tools/gen_arch_stats.py --check-boundaries` | 检测跨模块 ORM 写违规      |
| `python run.py start / stop / status`               | 启动/停止/检查平台         |


## 快速上手（codebase-onboarding 生成）

> 完整入门指南见 `dev_docs/代码库入门指南.md`

**技术栈**：Django 4.2 + DRF + Channels（后端，纯 API）· Vue 3.4 + Vite + Element Plus（前端 SPA）· AgentScope 2.0（AI，进程内）· uiautomator2/ADB（设备）· MySQL/SQLite + Redis。

**关键入口**：`manage.py` / `run.py` / `run_daphne.py` / `config/{settings,urls,asgi}.py` / `gateway/routing.py`（WS 真相源）· 前端 `frontend/src/{main.ts,router.ts}` / `frontend/vite.config.js`。

**目录速览**：`apps/`（11 个 Django App）· `gateway/`（JWT 中间件/WS 路由）· `shared/`（auth/renderers/events）· `engines/`（L1c 设备引擎插槽）· `models/`（领域类型）· `algorithms/`（vision/xpath/layout）· `frontend/src/modules/`（9 模块）· `dev_docs/`（PRD/ARCH/测试）· `tests/`（pytest 分模块 + arch 契约）。

**请求链路**：前端模块 `api.ts` → `djangoClient`(/api) → Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status,data}`）→ ORM。

**常见命令**：`python run.py start/stop/status` · `python manage.py check` · `ruff check .` · `pytest` · `cd frontend && npm run dev/typecheck/build:check/lint` · `npm test`。

**约定**：Conventional Commits（feat/fix/docs/chore/refactor/test + scope）· 表前缀 `dp_ di_ el_ cm_ tr_ rg_ ai_ ev_ wf_` · 响应信封 `{status,data}`（部分 legacy 平铺）· Python Ruff 双引号/行长 100/禁 print · 前端 kebab-case + camelCase。