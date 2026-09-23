## Context

见 `proposal.md` - Why。现状：前端四子路由共用 `index.vue`，`evaluator` 视图挂 `EvaluatorTab` 并走 `evaluator-api.ts`（legacy 平铺 `/api/evaluator/*`）。后端 `apps.evaluator` 含 models / views / views_api / api / frameworks。`test_runner` 已用「清空 Model + DeleteModel 迁移 + 仍留 INSTALLED_APPS」下线，本单复用该模式。

## Goals / Non-Goals

**Goals:**

- 产品面与 HTTP 面不可达；四表删除；业务 Python/Vue 文件删除。

**Non-Goals:**

- 不删 `PRD-11` 历史文档、不改知识库 `/api/ai/` RAG 能力。
- 不把 `apps.evaluator` 从 `INSTALLED_APPS` 拿掉（否则历史迁移无法 apply）。
- 不修改 `get_provider_config` / `search_knowledge` 实现（知识库与 Agent 仍用）。

## Decisions

- **迁移壳对齐 test_runner**：只留 `models.py` 说明、`apps.py`、`migrations/`。备选是连 App 目录一起删——会打断已部署库的 migrate 链，否决。
- **DeleteModel 顺序**：`EvalResult` → `EvalRun` → `Question` → `QuestionBank`，避免外键阻塞。
- **Swagger TAGS 去掉 evaluator**：schema 不再宣传已卸端点。

## 模块防火墙自检

- 跨 App import：删除 evaluator 对 `ai_assistant.api` 的调用，不新增反向依赖。
- 写库：无新写点；旧 evaluator `api.py` 随业务代码删除。
- 前端不直连数据库。

## Risks / Trade-offs

- [生产库评测数据不可恢复] → 明确 BREAKING；无备份策略则不要在生产 migrate 前导出。
- [书签打到 `/ai-assistant/evaluator`] → 无匹配路由时回落到 Vue Router 默认行为（通常空白/重定向由全局 404 处理，不专门做评测兼容页）。
