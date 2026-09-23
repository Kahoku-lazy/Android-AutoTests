## 1. 前端去掉评测子项

- [x] 1.1 从 `sidebarNavConfig.ts` 删除评测中心子项与 `MOD_COLORS` 的 `/ai-assistant/evaluator`，侧栏只剩三个 AI 子项
- [x] 1.2 删除 `routes.ts` 中 `/ai-assistant/evaluator`；`ViewMode` 去掉 `evaluator`；`index.vue` 去掉 EvaluatorTab / VIEW_META.evaluator；`index.style.css` 去掉 `.eval-host`
- [x] 1.3 删除 `EvaluatorTab.vue`、`evaluator-api.ts`；`constants.ts` 删除仅评测使用的 `EVALUATOR_POLL_MS` / `KB_SEARCH_TOP_K`；`index.logic.ts` 副标题去掉「评测」；更新 `ai-assistant/AGENTS.md` 为三子项
- [x] 1.4 grep 前端 `src/` 确认无 `/ai-assistant/evaluator`、`EvaluatorTab`、`evaluator-api`

## 2. 后端卸接口与表

- [x] 2.1 `config/urls.py` 去掉 `api/evaluator/` include；`SPECTACULAR_SETTINGS.TAGS` 去掉 evaluator
- [x] 2.2 删除 evaluator 业务源码（views/api/serializers/urls/frameworks/management/default_questions/evaluator.py）；`models.py` 改为卸表说明；新增 `apps.py`；新增 DeleteModel 迁移 `0003`
- [x] 2.3 修正 `ai_assistant/api.py` 中「供 evaluator」注释；`python manage.py check` 通过

## 3. 测试与文档

- [x] 3.1 删除 `tests/graybox/unit/test_evaluator_writes.py` 与 `test_evaluator_drf_writes.py`；`pytest.ini` 去掉 evaluator marker
- [x] 3.2 `README.md` 去掉评测中心行；`apps/自测与检测指令.md` 的 marker 列表去掉 evaluator
- [x] 3.3 `ruff check` 触及的后端路径；grep `apps/` `frontend/src/` `tests/` 无评测业务入口（迁移壳与 ARCH 前缀映射 `ev_` 可保留）
