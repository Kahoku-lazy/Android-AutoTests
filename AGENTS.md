# AGENTS.md

## 与用户沟通协议（最高优先）

用户是需求方，不是开发者。用户提出需求后：

1. **自己消化**：读代码、核事实、走 OpenSpec 流程都在后台完成，**不把过程摊给用户看**
2. **只回结果**，固定三段式：
   - **结论**：这个需求能不能做、当前真实状态（以代码事实为准，不推测）
   - **你会看到什么**：做完之后界面 / 数据 / 行为上的变化，用业务语言描述
   - **要你拍板**：必须取舍时给出 A/B 选项及各自后果
3. **默认不贴**代码片段、文件路径、框架术语、命令输出；用户明确说"展开细节 / 给我看改哪儿"时才给
4. 禁止以"我看了 xxx 文件 / 我执行了 xxx"这类过程叙述开场
5. 唯一例外：**不可逆操作**（删数据、删文件、强制覆盖、停服务）仍须先取得用户确认——这不是过程叙述，是真实决策

## AGENTS 分级

本仓 `AGENTS.md` 按下列优先级生效，下级不得与上级冲突：

1. 根 `AGENTS.md`（最高）
2. `frontend/AGENTS.md` · `apps/AGENTS.md` · `engines/ai/AGENTS.md` · `tests/AGENTS.md`
3. 各子模块 `AGENTS.md`（`apps/{app}/` · `frontend/src/**/`）

## 行为规范

1. **必须**使用规范驱动流程 `OpenSpec` 开发，**禁止**直接写代码。四步走，缺一不可：
   1. `/opsx:explore` — 聊清需求；**动工前先确认范围**
   2. `/opsx:propose <change-id>` — 立项，产出 `openspec/changes/<change-id>/`：`proposal.md`（为什么做/改什么）· `specs/`（验收标准）· `design.md`（技术方案）· `tasks.md`（任务清单）
   3. `/opsx:apply` — 照清单实施，逐条打勾
   4. `/opsx:archive` — 归档关单，验收标准并入 `openspec/specs/`


## 代码规范

规范分三层，避免与工具重复、避免跨语言互相打架。

### 1. 总则：格式类要求以工具配置为准

格式、引号、缩进、换行、import 顺序等**可机械判定**的要求，一律以工具配置为唯一真相源，本文件不重复描述。入口：

| 语言 | 唯一真相源 |
| --- | --- |
| Python | `ruff`（`ruff.toml`：行宽 100、双引号、尾随逗号、import 顺序、禁止裸 `except` 与 `print`） |
| 前端 TS / Vue / CSS | `prettier`（`frontend/.prettierrc`）· `eslint`（`frontend/eslint.config.js`）· `vue-tsc`（`frontend/tsconfig.json`） |
| 其它（JSON / YAML / Markdown） | 跟随所在目录既有风格，不新造风格 |

改格式类规则时**只改配置**，不要在本文件里另写一份。

### 2. 跨语言原则（人工遵守，工具查不了）

1. **可读性优先**：结构清晰、命名直白，适当注释与留白；不为炫技把多行逻辑压成一行。
2. **简单胜于复杂**：能用简单逻辑解决就不引入复杂设计；不依赖晦涩的"魔法"或隐藏行为，让阅读者不需要猜意图。
3. **错误不许静默忽略**：出错要抛出或明确记录，不返回 `None` / 假数据。隐藏的 Bug 比崩溃更可怕。
4. **拒绝猜测**：遇到不确定的逻辑或数据，不要用 if-else 猜着兜底；抛异常或要求调用方给出明确输入。
5. **命名空间隔离**：用模块、类、函数划分作用域，避免全局变量污染与命名冲突。
6. **最少代码**：不实现需求之外的功能，不接受过度设计。
7. **只碰必须碰的**：不擅自改动相邻代码、注释、格式；diff 中每一行都应能追溯到用户请求。

### 3. 语言与边界细节：下沉到各层

本文件只放跨语言原则。与具体语言、具体模块有关的判断类要求，写在对应层级的 `AGENTS.md`（分级见上）：后端 Python 与模块边界 → `apps/AGENTS.md`；前端 Vue / TS、版式与设计令牌 → `frontend/AGENTS.md`；测试 → `tests/AGENTS.md`；引擎 → `engines/ai/AGENTS.md`。

**已知盲区登记（2026-09-23）**：以下四道检查已接入 CI，但当前**仅警告、不拦截**——违反不阻断构建，只落在日志里：

- 前端 `eslint`（范围 `frontend/src/`）
- 前端类型检查 `vue-tsc`（范围 `frontend/src/`，当前 `tsconfig` 未开严格模式）
- `prettier` 的 `.ts` 覆盖（CI 既有的 prettier 步骤只查 `.vue/.js/.css`）
- 后端 `ruff` 的 `engines/` 覆盖（CI 既有的 ruff 步骤只查 `apps/ config/ gateway/ shared/ models/`）

存量基线（本地实测）：`.ts` 格式 **98 个文件**不合规、类型报错 **3 处**、eslint **69 条警告（0 报错）**、`engines/` 后端检查 **0 问题**。存量清理后由独立变更把这四道转为拦截。



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
