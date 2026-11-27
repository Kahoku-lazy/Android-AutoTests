## 目标

把「草稿只对作者可见」这条口径补齐到所有按编号访问的接口，把任务版本口径收敛到 SOP，把发布状态机补上工作流那条缺失的边，并让 `revision` 乐观锁真正生效。

## 决策与取舍

### D1 改名不退回草稿，改为解析时刷新运行名（偏离用户最初选择，已在 proposal 说明）

- **原推荐**：把 `display_name` 计入「运行内容」，改名即回草稿。
- **否决理由**：与 `assistant-release`「只修改显示名 MUST 保持已发布」及其两个场景冲突；与既有用例 `test_runtime_edit_returns_to_draft_display_name_does_not` 冲突；且名片本身就是发布体，回草稿会让它从**所有非作者的列表里消失**，改一个错别字等于下线。
- **采用**：版本里 `run_name` 保留发布当时值（留痕），`_resolved_from_release` 在解析时用名片当前 `display_name` 覆盖，并重跑 `align_run_names` 处理同名后缀。
- **代价**：历史任务重跑时报告角色名跟随当前名片名，不再是「当时的名」。这是「名字是展示、不是行为」的取舍——行为（提示词/模型/工具）仍按版本冻结。

### D2 goal / team 不记版本，读最新发布版本

- 提交侧：`release_version` 只在 `orchestration == "sop"` 时写入，其余写空。
- 读取侧保持现状（`_finish_goal` / `_finish_team` 用 `resolve_sop_workflow`）。**注意实现事实**：`resolve_sop_workflow` 先取该工作流最新 `AssistantRelease`，没有版本时才回落 `resolve_workflow`（实时配置）。所以这两类是「跟随最新发布」，不是「跟随实时草稿」——这正好挡住未发布改动泄漏进运行。
- 好处：数据不再声称「可复现」；坏处：这两类任务的重跑会跟随后来发布的新版本，需在文档写明。

### D3 草稿可见性

- 新增视图级 helper `_visible_card(assistant_id, user_id)`：作者或超管放行；否则要求 `release_state == "published"`；不满足一律 404（按规格，不泄露存在性）。
- 覆盖：`/avatar/`、`/assistants/<id>/threads/`（GET/POST）、`/assistants/threads/<tid>/`（GET/PATCH/POST/DELETE）、`/threads/<tid>/delete/`、`/threads/<tid>/logs/`（列表）。
- 日志文件下载走一次性 ticket，不额外加校验（ticket 只能由已鉴权的列表接口签发）。

### D4 发布前引用校验

- `publish_assistant`：`AIRole` 不存在 → `ValueError("Agent 配置不存在，无法发布")`，视图已把 `ValueError` 映射成 400。
- `publish_workflow`：复用已有 `WorkflowBindingError`（视图已映射 400），覆盖两侧与 team 的队长/成员。

### D5 工作流回草稿

- `update_sop_workflow` 对比 `name / executor_assistant_id / verifier_assistant_id / leader_assistant_id / members`；有变化且已发布 → `release_state = "draft"`、`revision += 1`。无变化也 `revision += 1`（与名片一致，表示一次编辑）。

### D6 乐观锁

- 后端已实现，只补前端：`AssistantCard.revision` 类型、表单带出、`PATCH` 的 `FormData` 回传。工作流侧暂不启用（前端表单未持有版本号，留作后续）。

### D7 顺手项

- `list_assistants()` 加 `.defer("avatar")`（`values_list("role_id")` 仍可用）。
- `queue_turn` 判据加 `settings.TESTING`。
- `apps.ready` 改调 `api.mark_interrupted_threads()`，把写库收回 `api.py`。

## 风险与回退

| 风险 | 影响 | 回退 |
|---|---|---|
| 草稿 404 影响既有调用方 | 仅影响非作者访问草稿，正是目标 | 回退 3 个视图 helper 调用即可 |
| goal/team 空版本 | 旧任务仍有版本号，新任务没有；兼容读路径 `if task.release_version` 已判空 | 回退 `_submit_*` 一行 |
| 运行名解析刷新 | 历史报告标签变化 | 回退 `_resolved_from_release` 的覆盖逻辑 |
| 工作流回草稿 | 改绑定后需重新发布（预期） | 回退 `update_sop_workflow` 的状态赋值 |

## 验证口径

- 灰盒：`tests/ai_assistant/api/`（名片/对话栏/发布/工作流）+ `tests/task/api/`（提交版本）。
- 门禁：`python -m run check`；涉及 Model 无变化，不需要 `makemigrations --check`，但跑一次确认。
- 文档：模块文档与架构图卡片文案同步。
