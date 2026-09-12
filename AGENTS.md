# AGENTS.md

## 行为规范

1. **必须**使用轻量级的规范驱动技能 `OpenSpec`开发，**禁止**直接写代码。openspec任务完成后要使用对应技能存档，关单。

2. **遵循实事求是的原则** 规划任务前**必须**先了解项目真实的业务逻辑，具体的代码实现，**不推测逻辑，不假设问题**。

3. **只碰必须碰的。只清理自己造成的混乱。** 不要"顺手"改进相邻代码、注释、格式。diff 中每一行都应能追溯到用户的请求

## 代码编写规范

1. **可读性至关重要**，数据契约中的变量名，有意义的变量名、方法的入参出参，以及核心代码 **必须** 使用适当的注释，让代码像英语文章一样易于理解

2. **代码结构清晰**，不要为了炫技把多行逻辑压缩成一行。适当换行、留白**能提升代码的可读性**，代码结构必须是清晰、有条理的。

3. **简单胜于复杂**，能用简单逻辑解决的问题，不要引入不必要的复杂设计。代码的意图应该直白地表达出来。**不要**依赖语言中晦涩的“魔法”或隐藏行为，让阅读者不需要猜测你的意图。

4. **扁平胜于嵌套**：尽量避免过深的 if-else 或循环嵌套。可以通过提前 return、使用多态或拆分函数来保持代码层级的扁平化

5. **错误不应默默忽略**：程序出错时应该抛出异常或明确记录，而不是返回 None 或假数据。隐藏的 Bug 比直接崩溃更可怕

6. **除非明确地选择忽略**：如果你确实需要忽略某个错误（例如清理临时文件时文件不存在），必须使用 try-except 显式捕获并注释说明原因。

7. **面对模糊不清，拒绝猜测**：遇到不确定的逻辑或数据时，不要盲目使用 if-else 去猜测处理，应该抛出异常或要求调用者提供明确的输入

8. **命名空间是个绝妙的主意**：在理解业务需求后，编写代码时充分利用模块、类和函数等命名空间来隔离作用域，避免全局变量污染和命名冲突

9. **不要重复造轮子**：重复造轮子会增加代码的复杂度，并且会引入额外的错误。

10. **用最少的代码解决问题。不接受过度设计。** 不添加需求之外的功能。用户说"加个筛选条件"，不要顺便"优化整个表格组件"


## 工作偏好与经验教训

### 遇到错误时先诊断，判断错位原因，捋清变动范围后再动手，禁止直接猜原因改代码

**看到错误日志、堆栈、浏览器 console 报错、服务异常时，禁止直接猜原因改代码。** 必须先在文字中完成以下步骤：

1. **复述现象**："我看到了什么"
2. **列出可能原因**："可能的根因有 A / B / C"
3. **修改范围**：   "我修改了 A、B、C"
3. **提出验证计划**："下一步查什么来确认"


## 快速上手

> 完整入门指南见 `dev_docs/代码库入门指南.md`

1. **技术栈**：Django 4.2 + DRF + Channels（后端，纯 API）· Vue 3.4 + Vite + Element Plus（前端 SPA）· AgentScope 2.0（AI，进程内）· uiautomator2/ADB（设备）· MySQL/SQLite + Redis。

2. **关键入口**：`manage.py` / `run.py` / `run_daphne.py` / `config/{settings,urls,asgi}.py` / `gateway/routing.py`（WS 真相源）· 前端 `frontend/src/{main.ts,router.ts}` / `frontend/vite.config.js`。

3. **请求链路**：前端模块 `api.ts` → `djangoClient`(/api) → Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status,data}`）→ ORM。

4. **常见命令**：`python run.py start/stop/status` · `python manage.py check` · `ruff check .` · `pytest` · `cd frontend && npm run dev/typecheck/build:check/lint` · `npm test`。

5. **约定**：Conventional Commits（feat/fix/docs/chore/refactor/test + scope）· 表前缀 `dp_ di_ el_ cm_ tr_ rg_ ai_ ev_ wf_` · 响应信封 `{status,data}`（部分 legacy 平铺）· Python Ruff 双引号/行长 100/禁 print · 前端 kebab-case + camelCase。

### 文档位置

1. 临时生成的代码与文件、临时生成的测试数据 **必须**放到 `temps/` 中，不要在项目根目录下生成临时文件

2. 设计方案与报告放在 `dev_docs/05-开发与测试/设计方案与报告` 路径中，文件名举例：设计方案-XXX.md/设计方案-XXX.html，报告-XXX.md/报告-XXX.html

3. 接口相关文档放在 `dev_docs/05-开发与测试/接口文档` 中，文件名举例：API-XXX.md/API-XXX.html

4. PRD 文档放在 `dev_docs/02-PRD需求` 中，文件名举例：PRD-XXX.md/PRD-XXX.html

5. 架构文档放在 `dev_docs/03-设计与架构` 中，文件名举例：ARCH-XXX.md/ARCH-XXX.html


### 项目工具

1. 启动/停止/检查平台： `python run.py start / stop / status`  
