## 1. 数据模型与迁移

- [x] 1.1 `AIAgent` 增加 `task_kind`（默认 `device_control`），迁移 `0061` 种子 Agent-02（`case_authoring`、职责「测试用例编写」）。验证：`showmigrations` 已应用；DB 中 Agent-02 的 `task_kind=case_authoring`。
- [x] 1.2 `Task` 增加 `task_kind` 快照，迁移 `0004`。验证：`makemigrations --check` 无变更。

## 2. 后端任务链

- [x] 2.1 `TaskSubmitInputSerializer` 放宽设备必填；`TaskSubmitAPIView` 按 Agent 类型分流，用例编写任务要求 `documents` 并调用 `collect_document_files`。验证：Agent-02 提交用例 9 项测试通过（含 Word）；设备任务旧测试 6 项通过。
- [x] 2.2 `attachments.collect_document_files` 支持 `.docx/.pdf/.md`，上限 5 份；MarkItDown 缺可选依赖时 `.docx` 走 python-docx、`.pdf` 走 PyMuPDF 兜底，requirements 补 `markitdown[docx]` / `python-docx` / `PyMuPDF`。验证：docx 提交、docx/pdf 兜底、缺文档、错格式测试通过。
- [x] 2.3 `api.create_task` / `rerun_task` / 序列化补 `task_kind`；新增 `dispatch_case_authoring`、`build_case_requirement`、`case_project_code`。验证：调度与文档拼装测试通过。
- [x] 2.4 `task_runner` 按 `task_kind` 分流，用例编写任务调用 `CaseAuthoringWorkflow` 并把文档/判决写 `Task.result`；取消信号置位时中断工作流。验证：no-doc 失败、取消与工作流结果映射 3 项测试通过。

## 3. 报告与前端

- [x] 3.1 `task_reports.build_task_flow` 增加用例编写分支，返回 `document/documents/conclusion.verdicts`；报告列表补 `task_kind`。验证：报告详情与列表测试通过。
- [x] 3.2 任务清单改为当前用户可见 Agent 的全部任务；详情/删除/关闭/重跑/清空使用同一可见性。验证：相关旧测试 56 项通过。
- [x] 3.3 AI 助手看板每个 Agent 一张卡，职责/工作流按 `task_kind` 显示。验证：前端 `assistant-cards` / `AgentRouteCard` 测试通过。
- [x] 3.4 新建任务弹窗按 Agent 类型切换：Agent-02 上传 PRD/Word；任务卡显示类型。验证：`useTaskPublish` 7 项测试通过。
- [x] 3.5 任务详情增加 Markdown 用例面板与验收意见，渲染前 DOMPurify 净化；报告列表增加「类型」列。验证：`renderMarkdown` 3 项测试 + 报告常量测试通过。

## 4. 验证

- [x] 4.1 后端相关测试：`tests/api/test_task_case_authoring.py`、`tests/graybox/unit/test_case_authoring_task_runner.py`、报告/提交旧测试。验证：全部通过（用例 8 + 执行 3）。
- [x] 4.2 前端：`npx vitest run tests/task-list tests/ai-assistant tests/report-generator`。验证：126 passed。
- [x] 4.3 静态检查：`ruff format/check`（后端改动）、`npm run typecheck`、`npm run lint`、`prettier --check`。验证：ruff 通过；typecheck 通过；eslint 0 error；prettier 改动文件通过。
- [x] 4.4 本地门禁：`python run.py check`。验证：阻塞项 22/22 通过，0 失败。
- [x] 4.5 OpenSpec：`openspec validate add-appliance-case-authoring-task --strict`。验证：通过；已归档为 `2026-10-26-add-appliance-case-authoring-task`。
- [x] 4.6 端到端冒烟：登录平台 → 选择 Agent-02 上传 `prd.md` → 任务 148 两次尝试后 `completed` / `PASS`，报告返回 9,192 字符测试用例文档；报告页与 AI 助手双卡片截图人工核对通过。
