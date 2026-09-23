## Why

元素定位模块（`frontend/src/modules/element-locator/`）残留 **28 个零消费 API 封装**与 **2 个零消费 composable 方法**；同时该模块唯一的 P0 单测 `api.spec.ts` 因 `/api/` 路径补尾斜杠（`openspec/specs/api-path-convention`）而 **46/46 全红**，既提供不了守护、又让套件长期为红。

已归档变更 `2026-09-11-remove-legacy-element-locator-managers` 已把 `api.ts` 的遗留函数登记为"后续 C 档"，本次闭环该欠账；本变更不改变任何可观察行为，属纯清退与测试对齐，故 `.openspec.yaml` 置 `skip_specs: true`。

## What Changes

### 1. 删除 `api.ts` 的 26 个零生产消费者导出

在 `frontend/src` 全量检索确认无任何生产调用方：

- 遗留 Pages / Elements / Flows（10 个）：`apiPages`、`apiUpdatePage`、`apiFlows`、`apiCreateFlow`、`apiDeleteFlow`、`apiGetPageElements`、`apiAddElementToPage`、`apiBatchAddElementsToPage`、`apiClearAll`、`apiBatchMovePages`
- 遗留 Web 元素与 Web 分组（7 个）：`apiListWebElements`、`apiBatchImportWebElements`、`apiListWebGroups`、`apiCreateWebGroup`、`apiUpdateWebGroup`、`apiDeleteWebGroup`、`apiBatchMoveWebGroups`
- 遗留 API 分组与端点列表（6 个）：`apiListApiGroups`、`apiCreateApiGroup`、`apiUpdateApiGroup`、`apiDeleteApiGroup`、`apiBatchMoveApiGroups`、`apiListApiEndpoints`
- 遗留 Web 流（3 个）：`apiListWebFlows`、`apiCreateWebFlow`、`apiDeleteWebFlow`

其中 Web 分组 / API 分组的写封装调用的是 live spec 已判定"停用、SHALL 返回 HTTP 410"的写端点（`element-locator-projects`「Legacy group write path retired」），删除它们同时消除"代码里存在一条已知必然失败的通路"这一误导。

### 2. 删除 2 个传递性死亡导出

`moveLocatorItem`、`batchDeleteLocatorFiles` 的唯一调用点分别落在下面两个待删方法内，方法删除后二者随之失去消费者。

### 3. 删除 `useLocatorTree` 的 2 个零消费方法

`removeFiles`、`moveTreeItem` 在被返回但从未被任何调用方解构（`ProjectWorkspace.vue` 与 `LocatorFileView.vue` 的解构清单均不含这两个名字）。

删除后 `api.ts` 导出从 **46 收敛为 18**。

### 4. 重写 `frontend/tests/element-locator/p0/api.spec.ts`

该文件 46 个用例现全部失败，且其中 26 个覆盖的是本次删除的函数。改写为**只覆盖裁剪后存活的 18 个函数**：

- 11 个沿用用例修正为带尾斜杠的 router 路径（如 `/elements/web` → `/elements/web/`；`apiCreate*` 系列删除已不存在的 `/create` 断言）
- 7 个项目化函数新增覆盖：`listLocatorProjects`、`getLocatorProjectTree`、`createLocatorDirectory`、`updateLocatorDirectory`、`deleteLocatorDirectory`、`apiGetWebElement`、`apiGetApiEndpoint`

### 5. 按实测重新登记前端调用面扫描下限

`tests/graybox/unit/test_api_path_callers.py` 的 `MIN_PER_SURFACE["frontend"] = 130`（实测 136）。`api.ts` 现有 46 个路径字面量，删除 28 个后前端面实测值降至约 108，原下限不再可达。本变更按**新实测值的 ~95%** 重新登记该下限，并在注释中写明"下限下调源于调用点真实减少，而非扫描器识别规则退化"——该守护的失败文案明确要求排查扫描器而非直接调低下限，故此处必须显式登记理由。

### 6. 非变更项

- **BREAKING**：无。删除项均不在任何渲染路径、事件绑定或数据流上。
- 后端、路由表、数据模型、迁移、依赖：零改动。

## 明确移出本变更范围

以下为同一轮探测的发现，**不在本次解决**：

- **后端失去全部前端调用方的端点（只登记、不删除）**：`/elements/move/`、`/elements/files/batch-delete/`、`/elements/pages/clear/`、`/elements/pages/batch-move/`、`/elements/pages/{pid}/elements/`、`/elements/pages/{pid}/elements/batch/`、`/elements/flows/*`、`/elements/web-groups/*`、`/elements/api-groups/*`、`/elements/web-flows/*`。删除后端端点涉及路由表、DRF 视图与既有测试，另开变更。
- **`frontend/src/modules/element-locator/AGENTS.md` 为 0 字节**（归档变更 `remove-legacy-element-locator-managers` 的 task 4.1 要求写入的"项目树为唯一树实现"约束未落盘）。经用户明确指示：**本轮只记录、不解决**。
- **两份历史测试计划文档中的失效引用（只登记、不修改）**：`frontend/tests/PLAN-batch2-3modules.md`（9 处）与 `frontend/tests/DESIGN-batch2-3modules.md`（1 处）引用了本次删除的函数名。二者是 2026-08-13 定稿的历史设计与配套实施清单（PLAN 的 50 个 checkbox 全未勾选，正文描述的正是「为 37 个端点写 api.spec.ts」），属档案记录。改写它们等于重写历史，故本次不动；已知风险是照该 PLAN 复跑会写出引用已删导出的 spec。
- **上一轮探测的其余 P3 死分支/死事件**（另开）：`LocatorFilePanel` 的 `back` 事件（声明并在 `LocatorFileView` 绑定，但全模块零处 `emit('back')`）、`hideIdentity=false` 分支及其连带的 `kindLabel`/`FILE_KIND_LABELS`/两条 CSS、`LocatorTree` 的 `activeFileId` 高亮链路（唯一调用方恒传 `null`）与孤儿类名 `locator-row--dir`、`PageElementsWorkbench` 的 `defineExpose({ reload })`、`routes.ts` 的 4 条兼容 redirect、`unwrapDetail` 的不可达第二分支、`LocatorFileView` 树中查不到 id 时伪造 `文件 #N` 的兜底与删除后多余的整树抓取。

## 关联文档

- 需求编号：`PRD-04-元素定位`（本次为纯死代码清退与测试对齐，无需求变更）
- 须保持成立的既有能力：`element-locator-projects`、`api-path-convention`。已逐条检索确认删除项未被任何 live spec 引用。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 无 spec 级行为变化，`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- 前端源码 2 个文件：
  - `frontend/src/modules/element-locator/api.ts`（46 → 18 个导出）
  - `frontend/src/modules/element-locator/composables/useLocatorTree.ts`（删 2 个方法及其返回项）
- 前端测试 1 个文件：`frontend/tests/element-locator/p0/api.spec.ts`（46 → 18 个函数的用例）
- 后端测试守护 1 个文件：`tests/graybox/unit/test_api_path_callers.py`（仅重登记 `frontend` 面下限）
- 后端 / 路由 / 数据模型 / 迁移 / 依赖：零改动
- 观感与行为变化：无（删除项均零消费）
- 测试范围：`npx vitest run tests/element-locator`（应由全红转全绿）、`python -m pytest tests/graybox/unit -q`、`npm run typecheck`、`npm run lint:styles`
- 恢复方式：全部为删除与测试收紧，`git revert` 即回滚；无数据迁移
