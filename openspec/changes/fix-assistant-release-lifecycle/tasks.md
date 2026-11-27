## 1. 草稿可见性（D3）

- [x] 1.1 `views_drf.py` 新增 `_visible_card(assistant_id, user_id)`：作者/超管放行，否则要求已发布，不满足抛 `NotFound`。验证：`python -m pytest -c tests/pytest.ini tests/ai_assistant tests/task -q` → 114 passed
- [x] 1.2 挂到 `/avatar/`、对话栏列表与新建、对话栏详情四动作、删栏、日志列表。验证：新增用例 `test_draft_thread_surfaces_are_hidden_from_plain_user`、`test_draft_avatar_is_hidden_from_plain_user`
- [x] 1.3 已有对话栏/日志用例改口径：普通用户先拿到已发布名片再操作。验证：`test_assistant_threads.py`、`test_assistant_thread_logs.py` 全绿

## 2. 任务版本口径（D2）

- [x] 2.1 `task_list/views.py` 两处提交：`release_version` 仅 `orchestration == "sop"` 时写入（`_pinned_release_version`）。验证：新增用例 `test_release_version_is_recorded_only_for_sop`（sop → 4，goal → None）
- [x] 2.2 无版本号的任务走「最新发布版本」，从未发布时才回落实时配置。验证：`test_task_without_version_follows_latest_release`（已发布的读快照、从未发布的读实时提示词）

## 3. 发布前引用校验（D4）

- [x] 3.1 `api.publish_assistant` 校验 `AIRole` 存在，缺失抛 `ValueError`。验证：`test_publish_requires_existing_agent_config`（400 且无新版本）
- [x] 3.2 `api.publish_workflow` 经 `_published_card` 校验两侧 role 存在；team 校验队长与全部成员名片已发布。验证：`test_team_publish_requires_published_members`（草稿成员 → 400 并指出；补齐 → 200）

## 4. 工作流回草稿（D5）

- [x] 4.1 `api.update_sop_workflow` 比较绑定字段，变化且已发布 → 回 draft、`revision += 1`。验证：`test_editing_published_workflow_returns_to_draft_and_republishes`（draft → 再发布 version +1）

## 5. 运行名解析刷新（D1）

- [x] 5.1 `api._resolved_from_release` 用名片当前显示名覆盖两侧 `run_name`，再跑 `align_run_names`。验证：`test_workflow_run_name_follows_rename_but_version_keeps_history`（解析出新名、payload 留痕不变）

## 6. 乐观锁（D6）

- [x] 6.1 前端 `types.ts` 加 `revision`，`AssistantEditor.save` 带出，`updateAssistant` 写进 `FormData`。验证：`npx vue-tsc --noEmit` 通过；后端既有 409 分支由 `test_runtime_edit_returns_to_draft_display_name_does_not` 覆盖

## 7. 删除保护与顺手项（D7）

- [x] 7.1 `services/agent_configs.delete_role` 被名片引用 → `RoleConflictError` 列出名片名；视图映射 400。验证：`test_delete_role_in_use_is_rejected`
- [x] 7.2 `list_assistants()` 加 `.defer("avatar")`。验证：`test_assistants.py` 全绿（`has_avatar` 仍正确）
- [x] 7.3 `queue_turn` 判据加 `settings.TESTING`；`apps.ready` 改调 `api.mark_interrupted_threads()`。验证：`python -m run check` 的 django-check 通过

## 8. 文档与收尾

- [x] 8.1 `.agents/docs/apps/ai_assistant/ai_assistant_agent_config_and_cards.md` 补「对话与快照」「发布与版本口径」两节
- [x] 8.2 `dev_docs/ARCH_PRD/ARCH-助手数据链路.html` 卡片文案改为「首次发送冻结快照 / SOP 按版本、goal·team 读当前绑定」
- [x] 8.3 `openspec validate fix-assistant-release-lifecycle --strict` → valid
- [x] 8.4 `python -m run check` → 阻塞项 30/30；`pytest tests/ai_assistant tests/task` → 116 passed
- [x] 8.5 实施报告 `dev_docs/DEV_TEST/DEV-助手发布生命周期修复-2026-11-27.md`
- [ ] 8.6 PR 合并后 `openspec archive fix-assistant-release-lifecycle`（归档时才把 delta 落进主 spec）
