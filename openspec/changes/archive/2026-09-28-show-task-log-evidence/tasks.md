## 1. 类型与纯函数口径

- [x] 1.1 `frontend/src/shared/types/ai.ts` 增加证据 DTO（`TaskLogEvidence` / `TaskLogEvidenceHit` / `TaskLogOccurrence` / `TaskLogFeature` / `TaskLogLine`，字段全部可选），并在 `TaskRunLogEntry` 上加 `log_evidence?: TaskLogEvidence`。验证：`npx vue-tsc --noEmit` 0 错。
- [x] 1.2 新增 `frontend/src/modules/ai-assistant/helpers/log-evidence.ts`：等级中文标签与配色类（`strong/periodic/before_action/out_of_window` → 强证据/疑似周期/动作前/超窗）、结论文案（`hit/no_hit/no_log/out_of_window`）、摘要文案（等级 + 条数 + 关键词 + 功能点，多条全列）、功能点文案（`名称（#id 模块）`）、是否有可折叠详情、四段数据取值函数（命中/动作前/超窗/原始日志，一律不排序）。验证：`npx vitest run tests/ai-assistant/p0/log-evidence.spec.ts` → 16 passed。
- [x] 1.3 同文件补容错：证据为 `undefined` / 空对象 / 字段缺失时不抛错。验证：同用例覆盖（没有证据对象、窗口无日志、命中但无 occurrences、`lines` 里缺字段的脏数据）。

## 2. 展示组件

- [x] 2.1 新增 `frontend/src/modules/ai-assistant/components/StepLogEvidence.vue`（136 行）+ `StepLogEvidence.style.css`（只用 Doodle Craft 令牌与刻度，等级配色沿用状态色）。结构：摘要行常显（等级标签 + 条数 + 关键词 + 功能点）+ 折叠详情四段（命中详情 / 动作前日志 / 超窗日志 / 窗口原始日志），空段不渲染；无证据时只渲染一行说明。验证：`npx vue-tsc --noEmit` 0 错、`npx eslint src/modules/ai-assistant` 0 error、`npm run lint:styles` 四批通过、prettier 通过。
- [x] 2.2 合并条按后端顺序换行渲染、最新在上（新证据），前端不排序；原始日志文本 `white-space: pre-wrap` 保留换行。验证：组件用例断言同毫秒合并条内部换行保留、行顺序与入参一致；真机页面与服务端原文逐行对拍 32/32 行一致。
- [x] 2.3 只读约束：区块内无任何按钮与输入控件（只有折叠标题）。验证：组件用例断言 `button` / `input` 数量为 0。

## 3. 挂载进任务详情

- [x] 3.1 `helpers/task-detail.ts`：`TaskStepAttempt` 增加 `logEvidence?: TaskLogEvidence`，`toAttempt` 从 `entry.log_evidence` 取值（缺失为 `undefined`）。验证：`npx vitest run tests/ai-assistant/p0/task-detail.spec.ts` → 9 passed（含新增「证据被带出 / 缺失为 undefined」用例）。
- [x] 3.2 `components/TaskAttemptCard.vue`：在「执行结果」区块之后挂载 `<StepLogEvidence :evidence="attempt.logEvidence" />`。验证：`npx vitest run tests/ai-assistant/p0/TaskAttemptCard.spec.ts` → 9 passed（含摘要常显、无证据说明行、未命中结论、合并条换行、只读五个新用例）。
- [x] 3.3 既有字段含义与既有渲染不变（执行/验收/截图/Agent 过程未动）。验证：`npx vitest run tests/ai-assistant` → 20 文件 / 143 passed；行数：`StepLogEvidence.vue` 136、`TaskAttemptCard.vue` 256、`TaskDetailPage.vue` 525（**存量为 525，本变更未增行**，属根 AGENTS 已登记的存量超限项）。

## 4. 真机与关单

- [x] 4.1 用既有带证据的历史任务（现场任务 id=100 的「设备开关」步，强证据 `switch_off`）在浏览器核对：摘要 `强证据 1 条 switch_off 关闭设备成功（#1 设备开关）`；展开后命中原文 `[light_switch][I]: switch_off`、窗口原始日志 32 行与**服务端下发原文逐行一致（32/32，页面未重排）**；任务 id=99 的步骤里「超窗」结论可见。验证：`temps/check_task_log_evidence_page.py` → PAGE CHECK PASSED；截图 `temps/task_log_evidence_hit.png`。
- [x] 4.2 无证据时的降级：由前端用例覆盖（`TaskAttemptCard.spec.ts` 的「无日志证据时给出一行可读说明」），页面显示 `本次未采集到设备日志证据（端口未监听或历史任务无该字段）`，不报错。现场 4 条历史任务都带证据，故未在页面上取得「无证据」的真实样本。
- [x] 4.3 关单门禁：`npx vue-tsc --noEmit`（0 错）+ `npx eslint src/modules/ai-assistant src/shared/types`（0 error）+ `npm run lint:styles`（四批通过）+ `npx prettier --check`（本次涉及文件全过；`TaskInputPanel.vue` 等存量失败与本次无关，未改动该文件）+ `npx vitest run tests/ai-assistant`（20 文件 / 143 passed）+ `openspec validate show-task-log-evidence --strict`（valid）全部通过。
