## Why

工作流任务弹窗里的「自动化用例」现在是一条原生 `<select multiple>`：项目只靠 `optgroup` 分组，分组头不可点、不计数量、一滚就出视口，且没有搜索。用例一多，用户既看不出某条用例属于用例管理里的哪个项目，也只能靠滚轮和编号前缀去找。同一弹窗还把用例选择器、设备与按钮挤在 520px 单列里，校验要等点「开始运行」才报。

## What Changes

- 运行弹窗由 520px 单列改为 **960px 两栏**（左「基本信息」、右「用例选择」），窄屏（<1024px）回退单列。
- 「用例来源」由下拉改为分段控件（`平台用例` / `本地 YAML`），切换仍按现状清空另一侧输入。
- 平台用例选择器改为**项目栏 + 常驻搜索 + 按项目分组的复选列表**：
  - 项目栏显示「全部项目 / 各项目 + 条数」，选中即筛；
  - 搜索同时匹配用例名与编号，命中在其他项目时给出提示条并可一键切到全部项目；
  - 列表按项目分组展示，段头带项目名、条数与「全选本项目」，行内保留用例编号徽标；
  - 面板头显示「已选 N 条」，左列摘要卡显示「N 条 · 覆盖 M 个项目」并列出所选用例名。
- **切换项目不清空已选**（旧实现与已删的 `PlatformCasePicker` 都会清空）。
- 缺项时「开始运行」置灰，footer 左侧直接写出缺的是用例、YAML 还是设备。
- 选择器列表与项目栏各自固定视口内滚动；弹窗本体不滚动（登记为已知例外，见 design.md）。
- 提交字段、校验文案、`GET /cases/projects/automation/` 接口均**不变**。

## 关联文档

无独立需求编号。本次范围来自本轮确认的版式方案稿 `temps/sop-run-dialog-proto.html`（含可点原型与「改前/改后」对照），方案由需求方口头通过后落单。

## Capabilities

### New Capabilities

- `sop-run-case-picker`: 工作流运行弹窗的平台用例选择器——按项目分组与计数、按名称/编号搜索、跨项目保留已选、已选摘要，以及缺项时提交不可用。

### Modified Capabilities

- `assistant-bound-sop`: 「运行弹窗只提交工作流编号、里程碑 YAML 与可选设备」这一条只描述 YAML 来源；本次弹窗的字段与提交内容不变，需求级行为由新能力承接，故不改本条。

## Impact

- 前端（`frontend/src/modules/ai-assistant/`）：
  - `components/SopRunForm.vue`：改为编排层（基本信息 + 选择器 + footer 状态），表单状态与校验仍走 `helpers/sop-form.ts`。
  - 新增 `components/CasePicker.vue`：选择器本体（项目栏 / 搜索 / 分组列表 / 已选）。
  - 新增 `helpers/case-picker.ts`：纯函数（过滤、分组、计数、全选与已选合并）。
  - `components/SopWorkflowSection.vue`：运行弹窗宽度与窄屏回退。
- 测试（`frontend/tests/ai-assistant/`）：改写 `p0/sop-run-form.spec.ts` 的选项断言（不再依赖原生 `option`），新增 `p0/case-picker.spec.ts` 锁住过滤/分组/跨项目保留。
- 后端 / 接口：无改动。`list_automation_projects()` 已一次性返回全部自动化项目与其用例（`id` + `title`），够本方案用；不新增分页或搜索参数。
- 不在本次范围：用例选择器显示步骤数（需改序列化）、用例规模 > 500 的虚拟滚动或后端搜索、设备选项文案去掉 `(ONLINE)`。
