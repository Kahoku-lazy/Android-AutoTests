## 1. 后端

- [x] 1.1 `task_reports._case_events`：按 seq 收集事件，补角色映射；思考/文本详情全文保留，结构化交付正文替换为「完整文档见生成的测试用例」提示，避免重复整篇文档。验证：任务 148 报告返回 41 条事件，思考详情完整，角色映射为 case_writer/verifier。
- [x] 1.2 `_case_authoring_flow` 增加 `events` 字段，`document`/`documents`/`conclusion` 保持不变。验证：报告接口返回 document 9,192 字符 + events 41 条。

## 2. 前端

- [x] 2.1 `TaskDetailPage` 增加「模型事件流」区块：时间、角色、事件标签、模型、状态、次数、详情。验证：任务 148 页面可见 case_writer_role 事件与思考详情。
- [x] 2.2 事件详情默认 `max-height: 320px` 滚动；超过 600 字的详情显示「展开全文 / 收起」，展开后看完整思考文本。验证：Playwright 点击展开后按钮切换为「收起」。

## 3. 验证

- [x] 3.1 后端测试：`tests/api/test_task_case_authoring.py` 增加事件流断言（含 case_writer/verifier 角色映射与 6000 字思考全文保留）。验证：8 passed。
- [x] 3.2 前端：`npm run typecheck`、相关 vitest。验证：通过。
- [x] 3.3 本地门禁：`python run.py check`。验证：阻塞项 22/22 通过。
- [x] 3.4 OpenSpec：`openspec validate add-case-authoring-event-stream --strict`。验证：通过并归档。
