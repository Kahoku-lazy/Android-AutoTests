## 1. 展示格式化纯函数

- [x] 1.1 `frontend/src/modules/ai-assistant/helpers/task-detail.ts` 新增 `formatPlannerInputText(raw?: string): string`：空/空白返回空串；`JSON.parse` 成功按 2 空格缩进逐键展开、字符串值内 `\n`/`\r\n`/`\r` 转真实换行并按层级缩进；解析失败原样返回。验证：新增单测断言通过
- [x] 1.2 单测覆盖四类输入：四键紧凑单行 → 缩进多行；字符串含 `\n` → 真换行且续行对齐；非法 JSON → 原样回退；空串/`undefined` → 空串。验证：`cd frontend && npx vitest run tests/ai-assistant/p0/planner-input-format.spec.ts` 6 项全绿

## 2. 区块渲染接入

- [x] 2.1 `frontend/src/modules/ai-assistant/components/TaskInputPanel.vue`：规划输入 `<pre>` 改绑格式化结果（`computed` + 纯函数），组件内不写解析逻辑；空态文案与附件区块行为不变。验证：`npx eslint src/modules/ai-assistant/helpers/task-detail.ts src/modules/ai-assistant/components/TaskInputPanel.vue` 0 error、`npx prettier --check` 通过、`npx vue-tsc --noEmit` 通过
- [x] 2.2 视觉沿用既有令牌与 `.ti-pre` 规则（等宽字体、虚线边框、定高内部滚动），不新造字号/颜色/圆角。验证：挂载组件断言 DOM 文本形态（`tests/ai-assistant/p0/TaskInputPanel.spec.ts`），长正文仍由既有 `max-height: 240px` 内部滚动兜底

## 3. 验收

- [x] 3.1 组件级自证：四键逐行缩进、`\n` 字面量消失、附件正文空行与续行可读（DOM 文本断言，覆盖含空行的 Markdown 正文）。验证：`TaskInputPanel.spec.ts` 3 项全绿
- [x] 3.2 对照后端：详情接口返回的 `planner_input` 与改动前逐字一致（未被改写）。验证：`python -m pytest tests/graybox/unit/test_ai_task_title_attach_dispatch.py -q` 14 项全绿
- [x] 3.3 相关前端单测：`cd frontend && npx vitest run tests/ai-assistant/p0` 14 文件 93 项全绿（改动后新增 2 个文件 9 项）
