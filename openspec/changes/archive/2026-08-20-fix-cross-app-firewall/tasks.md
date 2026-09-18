## 1. shared 能力落位

- [x] 1.1 新增 `shared/users.py`（resolve_username 平移）；`case_manager/views_helpers.py` 改 re-export；验证 `python manage.py check && python -m ruff check shared/users.py apps/case_manager/views_helpers.py`
- [x] 1.2 新增 `shared/auth/require_auth.py`（平移）；`ai_assistant/decorators.py` 改 re-export；验证 ruff

## 2. 违规方改走合法通道

- [x] 2.1 `ai_assistant/api.py` 增 `filter_agents_for_user` + `__all__`；`permissions.py` 改 re-export；验证 ruff + `python manage.py check`
- [x] 2.2 `dashboard/views.py` 改 import（shared.users + ai_assistant.api）；`evaluator/views.py` 改 import（shared.auth.require_auth）；验证 ruff

## 3. 门禁与文档同步

- [x] 3.1 违规清零：`grep -rn "from apps\..*\.(views_helpers|permissions|decorators) import" apps/` 0 命中；`python tools/gen_arch_stats.py --check-boundaries`
- [x] 3.2 全量门禁：`python manage.py check && python -m ruff check shared apps tests && python -m pytest -m "unit or integration" --nomigrations -q`（基线 308）
- [x] 3.3 落地实测文档差距 #8 标注已修复；总纲 §六 6.2 标注完成
