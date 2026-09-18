## 1. 数据模型与解析复用

- [x] 1.1 `AITask.attachment` 改为 TextField；新增可空 `attachment_filename`、`device_label`；写迁移。验证：`python manage.py migrate ai_assistant --plan` 含这三项变更
- [x] 1.2 把 `kb_files` 的 docx/pdf 解析抽成同模块可调用函数，任务提交与知识库预览共用，禁止第三份拷贝。验证：`ruff check apps/ai_assistant/kb_files.py` 通过，知识库预览单测（若有）仍过

## 2. 提交契约与规划 JSON

- [x] 2.1 `TaskSubmitInputSerializer` + `TaskSubmitAPIView` 改为接收 `title`（必填）、`goal`、可选文件、`device_serial`、可选 `device_label`；非法扩展名/超 20MB/解析失败/无设备 均 400 且不建任务。验证：`pytest tests/graybox/unit/` 中新增或扩展 submit 用例覆盖上述拒绝路径
- [x] 2.2 `api.create_task` 写入 title/goal/attachment(MD)/filename/serial/label；`engine_adapter.build_request` 将 `TaskRequest.goal` 设为四键 JSON（`ensure_ascii=False`）。验证：单测断言 JSON 键为 `任务标题`/`任务目标`/`附件文本内容`/`设备ID`，无附件时附件值为 `""`
- [x] 2.3 `PLANNER_PROMPT` 补充「用户输入可能是上述 JSON」。验证：`engines/ai/agentscope/config.py` 含四键说明；不改 VISION/VERIFIER prompt

## 3. 按设备调度

- [x] 3.1 在 `apps/ai_assistant/api.py` 实现 `dispatch_device(serial)`：事务内 `select_for_update` 该 serial 的 pending|running；有 running 则不启动；否则 `start_task` 最早 pending。验证：单测同 serial 第二条保持 pending；异 serial 可同时 running
- [x] 3.2 `finalize_task` 成功/失败后调用 `dispatch_device`；`TaskSubmitAPIView` 创建后调用 dispatch 而非无条件开线程。验证：单测前序 failed/completed 后最早 pending 变为 running
- [x] 3.3 启动恢复：`recover_orphaned_tasks` 后对仍有 pending 的 serial 调用 dispatch。验证：单测遗留 running→failed 且 pending 可被拉起
- [x] 3.4 列表序列化增加卡片所需 `device_label`（空则调用方展示 serial）。验证：`serialize_agent_task_row` 含 `title/status/created_at/device_serial/device_label`，可不含目标全文（详情仍含 goal）

## 4. 前端弹窗与卡片

- [x] 4.1 `useTaskPublish` + `TaskBoard` 弹窗增加标题；附件改为 `el-upload`（`.docx,.pdf`，限 1 个）；`submitTask` 走 FormData。验证：`npm test` 相关 composable/组件测覆盖标题必填与 accept
- [x] 4.2 卡片展示标题、状态、创建时间、设备名（label 或 serial），去掉目标正文。验证：浏览器打开 `/ai-assistant/agents` 新建一条后卡片四字段可见、目标不可见；详情页仍可见目标
- [x] 4.3 DTO：`frontend/src/shared/types/ai.ts` 与列表类型对齐后端字段。验证：`cd frontend && npm run typecheck`
- [x] 4.4 新建任务设备下拉：打开弹窗立即 `GET /devices`，打开期间每 30s 再拉；关闭停止。验证：`useTaskPublish` 单测覆盖打开再拉、关停后不再请求

## 5. 门禁

- [x] 5.1 后端：`python manage.py check` 与覆盖本单的 `pytest` 通过
- [x] 5.2 前端：`cd frontend && npm run lint:styles`（若改了 scoped 色）+ 本模块测试通过
- [x] 5.3 边界：不新增跨 App 写库；HTTP 仍只经 `api.ts`。验证：改动文件 grep 无 `apps.*.models` 直写、无裸 `fetch`/`axios` 旁路
