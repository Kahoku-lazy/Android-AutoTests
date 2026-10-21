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

## 版本控制与提交

1. **单主干 `Kahoku`**：仓库只有这一个长期分支（`origin/HEAD -> origin/Kahoku`），不设 `develop` / `release/*`。临时分支按 `feat/<name>` / `fix/<name>` 命名，合并后删除。
2. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。一次提交只做一件事；**禁止 `git add -A`** —— 历史上有一次退役提交用它把未申报的目录改名一起带进去，导致已删除的包复活。
3. **没有 PR 流程**：改动直接推 `Kahoku`，不经 PR。不建长期分支、不设 `develop` / `release/*`；临时分支按 `feat/<name>` / `fix/<name>` 命名，用完即删。分支保护只保留「禁止强推 + 禁止删分支」，不再要求 PR 与状态检查。
4. **CI 是唯一的质量闸门**：没有 PR 就没人替你看，推送后必须确认 `ci-phase1.yml` 的 6 个 job 全绿 —— `backend-check` / `frontend-check` / `static-checks` / `security-scan` / `boundary-check` / `frontend-quality`。出现红项要当场修掉并在下一次推送里补齐，不得积压。
5. **禁止强推**：`Kahoku` 是唯一主干，禁止 `--force`。已推送的提交要改，用新提交修正，不改写历史。
6. **提交前先跑本地门禁**：`python run.py check`（与 CI 同一批检查，阻塞项失败即退出码 1）。不跑全量回归。

```bash
python run.py check                # 本地门禁
git add <具体文件>                  # 逐文件暂存，不用 -A
git commit -m "feat(scope): ..."
git push origin Kahoku             # 推送后确认 6 个 CI job 全绿
```

## 快速上手

### 技术栈

1. 后端，纯 API: Django 4.2 + DRF + Channels
2. 前端，纯 SPA：Vue 3.4 + Vite + Element Plus
3. AGENT 框架：AgentScope 2.0
4. 其它: uiautomator2/ADB（设备）· MySQL/SQLite + Redis

### 请求链路

 **请求链路**：前端模块 `api.ts` → `djangoClient`(/api) → Vite 代理 → `JWTAuthenticationMiddleware` → DRF View → `EnvelopeJSONRenderer`（`{status,data}`）→ ORM。

### 约定

1. 表前缀 `dp_ di_ el_ cm_ tr_ rg_ ai_ task_ ev_ wf_` 
2. 响应信封 `{status,data}`

### 文档位置

1. 临时生成的代码与文件、临时生成的测试数据 **必须**放到 `temps/` 中，不要在项目根目录下生成临时文件
2. 设计方案与报告，接口文档在 `dev_docs\DEV_TEST`目录中，文件名举例：XXX.md/XXX.html
3. 需求文档与架构文档放在 `dev_docs\ARCH_PRD` 中，文件名举例：ARCH-XXX.md/ARCH-XXX.html 或 PRD-XXX.md/PRD-XXX.html
4. **功能需求文档入口一律从 PRD 开始**：`dev_docs\ARCH_PRD\PRD-平台总需求.md` → 各模块 `PRD-*` → `ARCH-*`。除本文件与 `DEV_DOCS_README.md` 外，代码 / 技能 / 其它文档**不得**在文件中引用 dev_docs 路径


### 项目工具

1. 启动/停止/检查平台： `python run.py start / stop / status`
2. 本地质量门禁： `python run.py check` — 跑完与 CI 同一批检查（阻塞项 + 告警项）。阻塞项失败退出码为 1，告警项不影响退出码。检查清单与判定口径以 `tools/check_gates.py` 为唯一真相源。
