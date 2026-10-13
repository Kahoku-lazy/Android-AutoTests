# AGENTS.md

## 沟通要求
1. 讨论时请用中文，**禁止**用英文。
2. **必须**遵循结论先行，再给出详细的分析结果，最后罗列需要我决策的点，并给出详细理由与建议。

## 行为规范

1. **必须**使用规范驱动流程 `OpenSpec` 开发，**禁止**直接写代码。四步走，缺一不可：
   1. `/opsx:explore` — 聊清需求；**动工前先确认范围**
   2. `/opsx:propose <change-id>` — 立项，产出 `openspec/changes/<change-id>/`：`proposal.md`（为什么做/改什么）· `specs/`（验收标准）· `design.md`（技术方案）· `tasks.md`（任务清单）
   3. `/opsx:apply` — 照清单实施，逐条打勾
   4. `/opsx:archive` — 归档关单，验收标准并入 `openspec/specs/`

2. **禁止** 主动跑全量回归



## 快速上手

### 技术栈

1. 后端，纯 API: Django 4.2 + DRF + Channels
2. 前端，纯 SPA：Vue 3.4 + Vite + Element Plus
3. AGENT 框架：AgentScope 2.0
4. 其它: uiautomator2/ADB（设备）· MySQL/SQLite + Redis

### 请求链路

 **请求链路**：前端模块 `api.ts` → `djangoClient`(/api) → Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status,data}`）→ ORM。

### 约定

1. 表前缀 `dp_ di_ el_ cm_ tr_ rg_ ai_ ev_ wf_` 
2. 响应信封 `{status,data}`

### 文档位置

1. 临时生成的代码与文件、临时生成的测试数据 **必须**放到 `temps/` 中，不要在项目根目录下生成临时文件
2. 设计方案与报告，接口文档在 `dev_docs\DEV_TEST`目录中，文件名举例：XXX.md/XXX.html
3. 需求文档与架构文档放在 `dev_docs\ARCH_PRD` 中，文件名举例：ARCH-XXX.md/ARCH-XXX.html 或 PRD-XXX.md/PRD-XXX.html
4. **功能需求文档入口一律从 PRD 开始**：`dev_docs\ARCH_PRD\PRD-需求总纲.md` → 各模块 `PRD-*` → `ARCH-*`。除本文件与 `DEV_DOCS_README.md` 外，代码 / 技能 / 其它文档**不得**在文件中引用 dev_docs 路径


### 项目工具

1. 启动/停止/检查平台： `python run.py start / stop / status`
2. 本地质量门禁： `python run.py check` — 跑完与 CI 同一批检查（阻塞项 + 告警项）。阻塞项失败退出码为 1，告警项不影响退出码。检查清单与判定口径以 `tools/check_gates.py` 为唯一真相源。
