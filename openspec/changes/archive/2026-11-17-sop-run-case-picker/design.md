## Context

见 `proposal.md` 的 Why。现状：`components/SopRunForm.vue` 一个文件里同时承载「用例来源」「平台用例多选」「YAML 选择」「设备下拉」「校验与提交」，用例选择就是一条原生 `<select multiple>` + `optgroup`。数据侧 `GET /cases/projects/automation/` 一次性返回当前用户的全部自动化项目及每个项目下的用例（`id` + `title`），没有分页、没有搜索参数。版式依据是 `temps/sop-run-dialog-proto.html` 的「主方案 A」，需求方已按该原型确认。

约束（来自 `frontend/AGENTS.md` 与模块 `AGENTS.md`）：

- 弹窗不 `append-to-body`，否则脱离 `.ai-assistant-page` 取不到模块令牌；宽度写在 `SopWorkflowSection.vue` 的 `el-dialog` 上。
- 虚线只属于已登记的助手卡片 / 对话栏 / 运行日志卡 / `.sketch-kit`，弹窗、表单、列表一律实线。
- 字号只取 `--app-size-*`，间距只取 `--app-space-*`，颜色只用令牌。
- `.vue` ≤ 500 行；组件只渲染与事件，过滤/分组/计数下沉 `helpers/`。

## Goals / Non-Goals

**Goals:**

- 用例的**项目归属**在首屏就看得见：项目栏 + 分组段头 + 计数。
- 用例**找得到**：常驻搜索，名称与编号一起匹配，命中在别处时给出口。
- 已选**看得回来、不丢失**：跨项目保留，摘要写明条数与覆盖项目数。
- 缺项**提前说**：按钮禁用 + 可见文案，而不是点完才报错。
- 提交载荷与后端接口零改动。

**Non-Goals:**

- 不改 `/cases/projects/automation/` 的返回结构，不加分页或服务端搜索。
- 不在选择器里显示步骤数、优先级、模块（响应里没有这些字段）。
- 不做虚拟滚动；用例规模超过 500 条时另开变更。
- 不改设备下拉的取值口径与 `device-address.ts`。
- 不改 YAML 来源的行为（仍是选文件 + 提交配置）。

## Decisions

1. **两栏，宽度写在外壳上。** `SopWorkflowSection.vue` 的运行弹窗宽度改为 `min(960px, 92vw)`，`SopRunForm.vue` 内部 `.sop-run` 用 `grid-template-columns: 320px minmax(0, 1fr)`，`@media (max-width: 1023px)` 回退 `1fr`。备选是在表单内部做容器查询；EP 弹窗宽度由外壳决定，写在内部会与外层打架。窄屏断点取 1023px（而非 1024px），与 `max-width` 语义对齐，避免正好 1024 时两栏挤压。

2. **选择器独立成组件 `CasePicker.vue`，纯逻辑进 `helpers/case-picker.ts`。** 组件只做渲染与事件，函数只做数据变换，便于单测直接覆盖「过滤 / 分组 / 计数 / 全选 / 已选合并」。备选是把逻辑留在 `SopRunForm.vue`：该文件已 227 行，加上分组与搜索会逼近 500 行红线，且逻辑无法脱离 DOM 测。

3. **数据只用现有响应，一次拉全量。** 输入类型 `CaseProjectGroup = { id, name, rows: { id, title }[] }` 与接口一一对应；`filterCases(projects, query)` 返回带命中行的分组，`countByProject()` 返回项目栏计数。搜索用 `toLowerCase().includes()`，同时匹配 `title` 与 `id`。备选是服务端搜索：当前接口没有 `q`，为一个弹窗加接口不值得。

4. **默认「全部项目」，而不是第一个项目。** 用户的目标通常是「找某条用例」，不是「先挑项目」；默认全量 + 分组段头比默认收窄少一次点击。项目栏的「全部项目」计数在搜索时显示命中数，不显示全量数。

5. **切项目不清空已选。** 已选状态是 `string[]`（用例编号），与当前项目无关；只有切换「用例来源」和点「清空」会清空。旧 `PlatformCasePicker` 的「切项目清空」明确不复用。

6. **搜索跨范围提示条。** 当前项目命中数 < 全部命中数时，渲染一条提示（`role="status"`），文案分两种：项目内也有命中时说「当前项目命中 X 条，另有 N 条在其他项目命中」；项目内零命中时说「这个项目没有命中，另有 N 条在其他项目命中」。文案由 helper 生成，便于断言。

7. **缺项提示在 footer 左侧，与按钮禁用同源。** 复用 `sop-form.ts` 的 `sopRunError()` 作为唯一判据：`error` 非空即禁用并把 `error` 文案显示出来。备选是新写一套提示文案：会和提交时的报错分叉。

8. **列表视口内滚动，登记为已知例外。** doodle 硬规则是「卡片与弹窗内部不滚动」。选择器必须有固定视口，否则弹窗被列表撑长、按钮被顶下去。处理方式：弹窗本体不滚动，`.case-picker__rail` 与 `.case-picker__list` 各自 `max-height + overflow-y: auto`（对齐被删 `PlatformCasePicker` 的 220px 视口做法，按两栏高度放到 320px）。此例外写在本节，落地后若做主题自检需一并说明。

9. **用例行保留编号徽标，不显示步骤数。** 响应只有 `id` 与 `title`；编号徽标让用户能和用例管理里的行对上，步骤数需要改序列化，做 Non-Goal。

## 模块防火墙自检

- 只改 `frontend/src/modules/ai-assistant/`，不 import 其它模块的私有组件；`CasePicker.vue` 与 `helpers/case-picker.ts` 都是模块私有。
- 不新增对 `case-manager` 模块代码的依赖：数据仍走本模块 `api/assistants.ts` 的 `listAutomationProjects()`（内部打 `/cases/projects/automation/`）。
- 不新增后端调用；`runSopWorkflow()` 的请求体保持 `workflow_id` / `title` / `case_source` / `case_ids` / `device_serial`。
- 共享件只用 `DoodleBtn`、`EmptyState`、`SkeletonCard`，不自建第二套按钮或空态。

## Risks / Trade-offs

- [全量用例一次性渲染，几百条时首屏变慢] → 现有接口本来就是全量；本方案不加接口。到 500 条以上再开分页/虚拟滚动变更。
- [列表内部滚动与 doodle「内部不滚」规则冲突] → 已登记为例外（Decision 8），并在实现中把滚动限制在两个固定视口内，弹窗本体不产生滚动条。
- [320px 左列里设备选项 `IP:端口 · 型号 (ONLINE)` 会被截断] → 本次不改设备文案（避免与 spec 的设备取值口径混在一起），只保证下拉可展开、选中值可读；去 `(ONLINE)` 作为后续小改动。
- [现有测试断言「没有文本输入框」] → 搜索框用 `type="search"`，并把该断言收窄为「没有可手填序列号的 text 输入框」，避免误判。
- [窄屏回退后两栏变单列，视觉上与备选方案 B 相同] → 接受，B 只是 A 的窄屏形态，不需要第二套实现。

## Migration Plan

1. 先写 `helpers/case-picker.ts` 与其单测（过滤 / 分组 / 计数 / 全选 / 提示文案），纯函数无 DOM。
2. 再加 `CasePicker.vue`，用静态数据在 `SopRunForm.vue` 里替换原生多选。
3. 再调整 `SopRunForm.vue` 为两栏 + 摘要 + footer 缺项提示，并改 `SopWorkflowSection.vue` 的弹窗宽度。
4. 最后改 `frontend/tests/ai-assistant/p0/sop-run-form.spec.ts` 的选项断言，跑 `npx vitest run tests/ai-assistant`、`npx vue-tsc --noEmit`、`npm run lint:styles`。

回退：本变更不动数据与接口，回退只需还原上述 4 个前端文件与测试文件，无数据迁移。

## Open Questions

无。原待定项已在需求方确认时定下：默认「全部项目」、切换项目保留已选、搜索只匹配用例名与编号（不匹配项目名）。
