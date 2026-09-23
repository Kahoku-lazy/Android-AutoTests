## Why

评测中心已不再作为 AI 助手产品能力提供。它仍占用侧栏第四子项、整套 Django App（`/api/evaluator/*`、`ev_` 四表）与寄宿页 `EvaluatorTab`，继续维护会与「只保留平台小助手 / 工具箱 / 知识库」的口径冲突。现在整模块下线并删除相关代码。

## What Changes

- 前端：去掉侧栏「评测中心」、路由 `/ai-assistant/evaluator`、`EvaluatorTab` / `evaluator-api.ts` 及 `ViewMode`/`VIEW_META` 中的 `evaluator`。
- 后端：卸掉 `api/evaluator/` 挂载与全部 View/API/框架适配；`ev_` 四表用迁移删除。App 壳保留在 `INSTALLED_APPS` 中（与 `test_runner` 已下线同一模式），只为跑卸表迁移。
- 测试：删除 `test_evaluator_*.py`；契约/种子/Swagger tag 中评测端点一并去掉。
- **BREAKING**：`/ai-assistant/evaluator` 与 `/api/evaluator/*` 不再存在；题库与评测运行数据随表删除。

## 关联文档

- PRD：`PRD-11-评测中心`（本单下线该能力；不重写历史 PRD 正文）。
- 无新增 PRD。

## Capabilities

### New Capabilities

- `evaluator-retirement`：评测中心产品面与 HTTP API 下线；表删除；App 仅保留迁移壳。

### Modified Capabilities

- `frontend-doodle-subpage-nav`：AI 助手侧栏由四子项改为三子项（去掉评测中心）。
- `frontend-l3-content-block`：分区页样例 URL 不再使用 `/ai-assistant/evaluator`。
- `frontend-l3-container`：分区皮肤对照样例改为其它仍存在的工作台页。

## Impact

- 前端：`sidebarNavConfig.ts`、`ai-assistant/routes.ts`、`index.vue`、`index.style.css`、`index.logic.ts`、`constants.ts`、`shared/types/ai.ts`；删除 `EvaluatorTab.vue`、`evaluator-api.ts`。
- 后端：`config/urls.py`、`config/settings.py`（Swagger tag）；`apps/evaluator/` 清空业务代码并加 DeleteModel 迁移；`apps/ai_assistant/api.py` 仅改「供 evaluator 调用」注释。
- 测试：删除 `tests/graybox/unit/test_evaluator_writes.py`、`test_evaluator_drf_writes.py`；`pytest.ini` 去掉 `evaluator` marker。
- 文档：`README.md` 模块表、`frontend/src/modules/ai-assistant/AGENTS.md`。
- 知识库检索仍走 `/api/ai/`，不随评测 KB 自测端点一起删。
