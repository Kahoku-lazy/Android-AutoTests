## Context

- **目标模块**：`frontend/src/modules/element-locator/`（15 个文件）。动机与范围边界见 `proposal.md`（Why / What Changes / 明确移出本变更范围），此处不重复。
- **判定口径（本设计的唯一判据）**：对每个候选删除项，在 `frontend/src` 内检索其标识符，命中仅剩"声明处自身"即判为零生产消费者；再对"唯一命中落在另一个待删项体内"的函数做**传递性死亡**复核。之所以必须用标识符检索而非构建：Vue 模板与 composable 返回值解构的缺失不会在构建期报错，`typecheck` 不覆盖"返回了但没人解构"这一类。
- **live spec 约束**：
  - `element-locator-projects`「Legacy group write path retired」明确规定 WebGroup / ApiGroup **写端点 SHALL 返回 HTTP 410**。因此 `apiCreateWebGroup` / `apiUpdateWebGroup` / `apiDeleteWebGroup` / `apiBatchMoveWebGroups` 与 API 分组同名的 4 个封装，是"代码里存在一条已知必然失败的通路"；删除它们与 live spec 同向，而非削弱规格。
  - `api-path-convention`「端到端调用方遵循唯一写法」要求前端 api 层路径带尾斜杠。该约定由 Python 侧守护测试断言（`frontend/src` 下无测试运行器），**不由** `frontend/tests` 的 vitest 用例守护。
- **欠账来源**：`openspec/changes/archive/2026-09-11-remove-legacy-element-locator-managers/proposal.md` 已登记"`api.ts` 未裁剪（27 个遗留函数属后续 C 档）"；后续 commit `d61e0985` 只删了视图模块，未动这一层。本次闭环。
- **在途改动约束**：工作区存在大量未提交修改（含 `element-locator` 自身 6 个文件）。故 tasks 一律**锚定符号**（函数名 / 方法名），不锚定行号。同理，"前端面实测值 136"是探测时读数，实施时须以当时的实测值为准。
- **环境约束**：`npx vitest` 在受限沙箱下因 Node 子进程管道 EPERM 无法启动，需以 `danger-full-access` 运行；已实测确认（本变更探测阶段即在该模式下跑出 46/46 全红）。

## Goals / Non-Goals

**Goals:**

- `api.ts` 的导出面从 46 收敛到 18，且剩下的 18 个**每一个都有生产调用方**
- `useLocatorTree` 的返回面不含任何"无人解构"的项
- `frontend/tests/element-locator/p0/api.spec.ts` 由 46/46 全红转为**全绿**，并恰好覆盖裁剪后存活的 18 个函数
- 每条删除都能被一条静态检索命令复验（删除后命中数为 0）
- 零可观察行为变化：请求次数、时机、路径、渲染均不变

**Non-Goals:**

- 不删后端任何端点、路由、视图、模型；失联端点只在 proposal 登记（见"明确移出本变更范围"）
- 不触碰 `element-locator/AGENTS.md`（用户明确指示本轮只记录、不解决）
- 不解决上一轮探测的其余 P3 死分支/死事件（`back` emit、`hideIdentity` 分支、`activeFileId` 链路、`reload` 暴露、4 条兼容 redirect、`unwrapDetail` 死分支、伪造兜底与多余整树抓取）
- 不为 element-locator 补组件层或端到端测试
- 不改任何令牌、样式几何与页面结构

## Decisions

**D1 删除 `api.ts` 的 26 个零消费者导出（分域，不做部分保留）**
理由：每个都在 `frontend/src` 内零命中。按域分组见 proposal「What Changes」。逐域复核结论：
- 遗留 Pages / Elements / Flows 10 个：属项目化重构（`refactor-element-locator-projects`）后被 `/elements/projects/{code}/tree/` 与目录 CRUD 取代的旧通路。
- Web 元素与 Web 分组 7 个、API 分组 6 个：分组写通路已由 live spec 判为 410；`apiListWebElements` / `apiListApiEndpoints` / `apiListWebGroups` 等读通路也已无消费（树由 `getLocatorProjectTree` 统一提供）。
- Web 流 3 个：无任何消费。
备选：保留为"未来扩展点" → 否决：不接受过度设计；确需时 `git show HEAD:<path>` 即恢复。备选：只删最高确定性的几个 → 否决：留下的一半仍会让静态检索持续给出假信号，等于把欠账再传一轮。

**D2 传递性死亡的两个导出一并删除（`moveLocatorItem` / `batchDeleteLocatorFiles`）**
二者在生产代码里各有且仅有 1 个调用点，分别落在待删的 `moveTreeItem` 与 `removeFiles` 体内。删除 D3 的两个方法后，它们不再有任何消费者。
理由：D1 的判据是"有生产调用方"，而"调用方本身是死的"不构成存活理由；若保留，下次扫描仍会因命中 `useLocatorTree.ts` 而误判为存活。
备选：先删方法、留封装给后端端点"留个入口" → 否决：前端零调用的封装不是入口，是噪音；端点联通性由 Python 侧 `test_api_path_callers.py` 按字面量守护，不依赖这两个封装。

**D3 删除 `useLocatorTree` 的 `removeFiles` / `moveTreeItem`（删方法，不补调用方）**
现状：两者定义后被 `return` 暴露，但两个调用方的解构清单（`ProjectWorkspace.vue` 的 `{ project, tree, loading, error, loadTree, addDirectory, renameDirectory, removeDirectory, addFile, removeFile }`、`LocatorFileView.vue` 的 `{ removeFile }`）都不含这两个名字。
理由：模块 AGENTS 约束"项目树 `useLocatorTree` 为唯一树实现"——批量删除与移动若要上线，应作为显式需求接入 UI 与后端 409 语义，而不是留一个无人接线的半成品。
备选：补一个批量删除 UI 调用 `removeFiles` → 否决：那是新增功能，超出纯清退范围，且后端 `/elements/files/batch-delete/` 的验收口径未定。

**D4 `api.spec.ts` 选择"重写为 18 个函数的用例"，而不是删除文件**
理由：该文件是模块唯一的 P0 契约测试，断言的是"调用哪个 client 方法 + 哪个 URL + 几参"，正是本次收敛后最需要钉住的面；直接删除会让模块前端覆盖归零，且丢掉"URL 漂移"这一曾在 `2ec9469e`（认证链路补尾斜杠）中真实发生过的漂移形态的守护。
用例构成（18 = 11 修正 + 7 新增）：
- 11 个沿用并修正为带尾斜杠的 router 路径：`apiPageItems`、`apiUpdateElement`、`apiGetPages`、`apiCreatePage`、`apiDeletePage`、`apiCreateWebElement`、`apiUpdateWebElement`、`apiDeleteWebElement`、`apiCreateApiEndpoint`、`apiUpdateApiEndpoint`、`apiDeleteApiEndpoint`。其中 `apiCreate*` 系列须删除已不存在的 `/create` 断言（当前 router 形式为 `/elements/<资源>/`）。
- 7 个新增的项目化函数：`listLocatorProjects`、`getLocatorProjectTree`、`createLocatorDirectory`、`updateLocatorDirectory`、`deleteLocatorDirectory`、`apiGetWebElement`、`apiGetApiEndpoint`。
- 保留该文件既有的表驱动形态（`it.each` + `ApiCase`，mock `@/shared/api-client`，不断真网络）与其"恰好调用一次"断言。
备选：删除该 spec 只留 Python 守护 → 否决：Python 守护只查"字面量带尾斜杠且能 resolve"，查不出"调错了 client 方法（get/post/put/delete 混用）"与"参数形状传错"。
备选：把 46 个用例中过时的 26 个只做 URL 修正保留 → 否决：它们覆盖的函数本次会被删除，保留即引用不存在的导出，文件无法编译。

**D5 `check-style-gates` 与 vitest 之外的 Python 守护下限必须同批重登记**
现状：`tests/graybox/unit/test_api_path_callers.py` 的 `MIN_PER_SURFACE["frontend"] = 130`（注释实测 136）。`api.ts` 现有 46 个 `client.*('...')` 路径字面量；删除 28 个后前端面实测值约 108，**低于登记下限 → `test_scanner_finds_the_expected_volume` 必然失败**。
决策：在同批把该下限按**新实测值的 ~95%** 重新登记，并在注释中写明下调依据（"`api.ts` 死代码清退删除了 28 个调用点，非扫描器退化"）。
理由：该守护的失败文案明确要求"检查 `_CALL_RX` / `_YAML_PATH_RX` 与面清单，而不是直接调低下限"——即下调必须伴随理由与证据。本次下调有可复算的证据（28 个被删函数各自对应 1 条字面量），且扫描器健康另有两条独立测试守护（`test_multiline_call_sites_are_captured` 要求跨行调用仍被扫到、`test_exception_list_entries_are_real` 要求例外清单指向真实字面量），因此下调不会掩盖识别规则退化。
备选：保留 130 不动 → 否决：门禁永久为红，等于用一条必失败的守护换掉一条真守护。备选：不删封装以免动下限 → 否决：与 Why 直接冲突。
风险控制：下限**只下调一次、只调这一个面**；若实施时实测值高于预期，则按实测值重算，不先验地取 108。

**D6 实施顺序：先删源码、再重写测试、最后重登记守护**
理由：`api.ts` 收敛后 `typecheck` / `vite build` 才会把"仍然 import 已删函数"的遗漏调用方暴露出来；此时 `api.spec.ts` 必然编译失败，正好作为"该文件确实引用了已删导出"的确认信号；最后一步才动 Python 守下限，此时实测值已稳定。
备选：先改测试再删源码 → 否决：中间态两边都编译不过，无法区分"我漏了调用方"与"测试还没改完"。

**D7 两份历史测试计划文档不修改（只登记）**
状况：`frontend/tests/PLAN-batch2-3modules.md`（9 处）与 `frontend/tests/DESIGN-batch2-3modules.md`（1 处）引用了本次要删除的函数名。
判定依据：`DESIGN-batch2-3modules.md` 头部标注「日期：2026-08-13 / 状态：已评审通过」，是定稿的历史设计记录；`PLAN-batch2-3modules.md` 是其配套实施清单，**50 个 checkbox 全部未勾选、且正文描述的正是「为 37 个端点写 api.spec.ts」**——即它记录的是一次已经以别的方式落地的历史计划，其产物就是本次要重写的那个文件。
决策：二者一律不改。理由：它们是对「当时为什么这么测」的忠实记录；把函数名从历史计划里抹掉，会让该文本描述的对象（当时的 37 个导出）与实际文字自相矛盾，属重写历史。且根 AGENTS 要求「只碰必须碰的」。
备选：同步更新为 18 个函数 → 否决：那是把历史计划改写成「事后正确」的版本，既越出本变更范围，也破坏了该文档的档案价值。
风险留痕：若未来有人照该 PLAN 复跑，会写出引用已删导出的 spec —— 这一风险已在 proposal「明确移出本变更范围」登记。

## 模块防火墙自检

- **跨 App import**：**零新增、零改动**。本变更全部发生在 `frontend/src/modules/element-locator/` 内部与两个测试文件内，不新增任何 import；`SaveToElementsDialog.vue` / `SavedPagePicker.vue` 对 `@/modules/element-locator/api` 的既有 `apiGetPages` 引用**本次不动**（`apiGetPages` 在存活 18 个之内）。
- **禁止跨 App import service/runner/consumer/state_machine**：不涉及（纯前端 + 测试文件）。
- **写库收敛到 `api.py`**：不涉及。本变更不新增/修改任何 INSERT/UPDATE/DELETE，不触碰 `apps/element_locator/`。
- **前端不直连数据库**：不涉及。前端仅经 `shared/api-client` 出口，本次删除的是该出口上的死封装，**净减** 28 个 HTTP 调用字面量。
- **通信通道**：不新增任何 HTTP 端点、WebSocket 生产点或 SSE；通道数只减不增。
- **净效果**：本变更使前端对后端的可达调用面缩小，属于"减接口消费"，不引入任何新的跨模块依赖。

## Risks / Trade-offs

- [误判存活：某个调用方通过动态方式引用被删导出] → 反证：`api.ts` 的消费者全部是静态 `import { ... } from '../api'`；已全仓检索 `import * as`（仅 echarts 两处）。实施后以 `typecheck` + `vite build` 复核。
- [HTML 模板里引用了被删的东西而构建不报错] → 被删项均为 TS 导出函数与 composable 返回值，模板访问它们会经 `<script setup>` 的绑定，缺失即 `typecheck` 报错；已额外用标识符检索覆盖 `.vue` 文件。
- [扫描下限下调被后人当作先例继续放宽] → 在下限注释中写明"本次依据 = 删除了 28 个调用点"，并保留 `test_multiline_call_sites_are_captured` / `test_exception_list_entries_are_real` 两条与计数无关的扫描器健康守护。
- [在途大量未提交改动导致行号漂移 / 实测值漂移] → tasks 锚定符号不锚定行号；下限按实施时实测值重算。
- [vitest 在受限沙箱下无法运行] → 需以 `danger-full-access` 运行；已在探测阶段实测可得 46/46 全红，故验收可复现。
- [删除后 `api.spec.ts` 覆盖从 46 降到 18，覆盖数下降被误读为质量下降] → 以"存活函数的覆盖率"替代"用例绝对数"作为验收口径：18/18 = 100%。

## Migration Plan

- 纯删除 + 测试收紧，无数据迁移、无部署顺序要求、无接口版本变化。
- 实施顺序：`api.ts` 收敛 → `useLocatorTree` 收敛 → `typecheck`/`vite build` → `api.spec.ts` 重写 → `vitest` 全绿 → Python 守下限重登记 → `pytest tests/graybox/unit` 全绿。
- 回滚：全部为删除与测试收敛，`git revert` 或 `git show HEAD:<path>` 即恢复；无残留状态。
