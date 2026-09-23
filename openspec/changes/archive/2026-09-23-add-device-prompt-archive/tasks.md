## 1. 后端：模型与迁移

- [x] 1.1 `apps/ai_assistant/models.py` 新增 `AIDevicePromptArchive`（`agent` FK / `kind` / `planner` / `executor` / `verifier` / `created_by` / `created_at` / `updated_at`，`ordering = ["-created_at", "-id"]`，`(agent, kind, -created_at)` 索引），并 `makemigrations ai_assistant` 生成 `0042`。验证：`python manage.py makemigrations --check --dry-run` 无待生成、`python manage.py check` 通过。
- [x] 1.2 确认迁移只做建表、无数据回填。验证：`python manage.py sqlmigrate ai_assistant 0042` 输出只有 CREATE TABLE / CREATE INDEX。

## 2. 后端：api.py 写库与存档

- [x] 2.1 `api.py` 增加自动档保留份数常量（3）与 `create_device_prompt_archive(agent, kind, prompts, user_id)`：写一条存档；`kind="auto"` 时同一事务内按 id 倒序只保留最新三份、删除其余；`kind="permanent"` 时覆盖该智能体已有永久档（至多一份）。验证：6.1 的对应用例。
- [x] 2.2 `api.update_device_prompts(agent, data, archive="auto", user_id="")` 扩展：写库后按 `archive` 记账，全程一个事务；三份一起写、任一份为空拒绝、不部分更新的既有语义不变。验证：6.1 用例 + 既有测试不回归。
- [x] 2.3 `api` 新增 `list_device_prompt_archives(agent)` / `get_device_prompt_archive(archive_id)` / `delete_device_prompt_archive(archive_id)`（仅允许永久档）/ `restore_device_prompt_from_archive(archive_id, user_id)`（**先写一份自动档，再覆盖三份正文**，任何异常整体回滚）。验证：6.1 的覆盖顺序与回滚用例。

## 3. 后端：视图与路由

- [x] 3.1 `views_prompts_drf.py` 新增历史列表 / 详情视图与删除 / 覆盖视图；四个端点 MUST 强制超级管理员（非超管 403）。验证：6.1 的 403 / 200 用例。
- [x] 3.2 `DevicePromptsAPIView.post` 接收并校验 `archive` 参数（白名单 `auto` / `permanent`，其它值 400），透传给 `api.update_device_prompts`。验证：6.1 的参数用例。
- [x] 3.3 `urls.py` 注册 `device-prompt-archives/`、`device-prompt-archives/<int:pk>/`、`.../<int:pk>/delete/`、`.../<int:pk>/restore/`。验证：`python manage.py check` 且 6.1 按真实路径请求成功。

## 4. 前端：接口与编排

- [x] 4.1 `api/toolbox.ts` 新增历史 DTO 与列表 / 详情 / 删除 / 覆盖四个请求函数，`updateDevicePrompts` 增加 `archive` 参数。验证：6.2 断言请求路径与体。
- [x] 4.2 `constants.ts` 增加确认文案常量（「此次保存会覆盖之前的备份记录，请确认是否覆盖保存」）与自动档保留份数。验证：6.2 引用常量、源码无重复字面量。
- [x] 4.3 `composables/useDevicePrompts.ts`：`save()` 先 `ElMessageBox.confirm`（文案取常量），确认后以 `archive="permanent"` 提交；新增 `autoSaveIfDirty()`（比较 draft 与已保存三份正文，全等则跳过）与历史状态（列表 / 预览 / 覆盖 / 删永久档）。验证：6.2 的取消、确认、无改动三分支。
- [x] 4.4 退出编辑的三个出口调用 `autoSaveIfDirty()`：`editing` true→false、`activeSource` 离开 `prompt`、`onBeforeUnmount`。验证：6.2 断言三处各触发一次，且无改动时不发请求。

## 5. 前端：界面

- [x] 5.1 `components/ToolboxPanel.vue` 在三个角色下拉头右上角（`#title` 插槽内）加「保存」「查看历史记录」按钮，动作为整组。验证：6.2 或组件用例断言三个下拉头都有这两个入口。
- [x] 5.2 新增历史抽屉组件：列出自动档（≤3）与永久档（≤1），显示类型与时间，可预览正文；永久档提供删除且删除前二次确认；自动档无删除入口。验证：组件 spec 断言列表项与删除确认，`npm run build` 通过。
- [x] 5.3 抽屉与按钮样式走 T0 令牌（不硬编码色值 / 字号 / 圆角），样式单独成文件。验证：`node tests/check-style-gates.mjs` 通过。

## 6. 测试与文档

- [x] 6.1 新增 `tests/graybox/unit/test_ai_device_prompt_archive.py`：连续四次保存只留最新三份自动档；永久档唯一且不被淘汰；未带 `archive`（即未确认保存）不产生永久档；`archive=permanent` 覆盖永久档；覆盖前先写自动档且失败整体回滚（monkeypatch 制造失败）；列表 / 详情 / 删除 / 覆盖仅超管（403）；空值拒绝不回归。验证：`pytest tests/graybox/unit/test_ai_device_prompt_archive.py` 全绿。
- [x] 6.2 新增 `frontend/tests/ai-assistant/p0/useDevicePrompts.spec.ts`：确认弹窗文案正确、取消不发请求、确认后带 `permanent`、无改动退出不发请求、有改动退出发 `auto`、覆盖调用正确路径。验证：`npx vitest run tests/ai-assistant/p0/useDevicePrompts.spec.ts` 通过。
- [x] 6.3 AI 助手接口文档「设备提示词」段补四个历史端点与 `archive` 参数语义（自动档三份滚动、永久档唯一、覆盖前先留档）。验证：逐条与 `views_prompts_drf.py` / `api.py` 对照一致。

## 7. 门禁

- [x] 7.1 后端门禁：`python manage.py check`、`makemigrations --check`、`ruff check`、`ruff format --check`（改动路径）、`pytest tests/graybox/unit`。验证：全部通过、无新增告警。
- [x] 7.2 架构门禁：`python tools/gen_arch_stats.py --check-boundaries`。验证：零违规。
- [x] 7.3 前端门禁：`npm run build` + `/vue-frontend-check` 三块报告。验证：构建无错、门禁项全部有结论。
- [x] 7.4 端到端复验：真实浏览器在装配台改提示词 → 退出编辑自动保存 → 点「保存」走确认框 → 历史抽屉看到自动三份 + 永久一份 → 用历史档覆盖当前，核对库中存档数量与正文。验证：`GET /api/ai/device-prompt-archives/` 与磁盘/库状态一致，且覆盖前后自动档计数符合预期。
