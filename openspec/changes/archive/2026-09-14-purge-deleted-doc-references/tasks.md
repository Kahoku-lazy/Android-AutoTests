## 1. 复核

- [x] 1.1 确认 `frontend/README.md` 无入站引用；验证：全仓检索 `frontend/README` = **0**（未发现任何文档/代码指向它）
- [x] 1.2 确认三处残留文本；验证：`plans/ai-assistant-vue-spec.md:3`（依据列表）· `plans/ai-engine-abstraction.md:180`（P6 行）· `config/api_docs.py:521`（页脚文案 `· VUE_API_CONTRACT.md`）

## 2. 清理

- [x] 2.1 删除 `frontend/README.md`；验证：`Test-Path` = False，`git status` 显示 `D`；其变更记录里对 `DEVELOPMENT_CHECKLIST.md` / `VUE_API_CONTRACT.md` 的提及随文件一并消失
- [x] 2.2 `plans/ai-assistant-vue-spec.md` 去掉了依据里的 `android-autotests-rules/references/frontend.md`，保留 `frontend/AGENTS.md` + `vue` skill
- [x] 2.3 `plans/ai-engine-abstraction.md` P6 改为「同步规则引用：`apps/AGENTS.md` §1.2 通道收敛（真相源 `ARCH-00` §1.4 五条通信通道）· ARCH-08 · `apps/ai_assistant/AGENTS.md` · `ruff.toml known-first-party` 加 `ai_engines`」
- [x] 2.4 `config/api_docs.py` 页脚去掉 `· VUE_API_CONTRACT.md`（保留 JSON Docs / Django Admin 两个链接）

## 3. 验证

- [x] 3.1 关键字清零；验证：全仓（含显式检索 gitignored 的 `plans/`）`VUE_API_CONTRACT` / `DEVELOPMENT_CHECKLIST` / `android-autotests-rules` 命中只剩两类 —— ① 本变更的规划文档（记录清掉了什么）· ② **活跃变更** `openspec/changes/complete-openapi-schema/proposal.md:37`（把已删契约文档列为真相源，属另一在建变更的计划文档，**未改，见下方说明**）；归档区 `openspec/changes/archive/**` 按惯例保留清理记录
- [x] 3.2 语法与范围；验证：`python -m py_compile config/api_docs.py` exit 0；`git status` 中 `frontend/README.md` = `D`、`config/api_docs.py` = `M`（`plans/` 为 gitignored 不进 status，改动已复核）

## 4. 边界说明（未做，交由用户决定）

- [x] 4.1 活跃变更 `complete-openapi-schema` 的 proposal 第 37 行仍把 `dev_docs/03-设计与架构/工具-VUE_API_CONTRACT.md` 列为契约真相源 —— 该文档已删。**未改**：它属于另一在建变更的规划文档，改动可能与正在进行的 openapi 迁移工作冲突；需要我一并改（换成 `dev_docs/05-开发与测试/接口文档/API-*.md` 或 OpenAPI schema）请说一声
