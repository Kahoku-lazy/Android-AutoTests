## Context

- **目标**：下线元素定位的 Web/API 两域，连带三处外部职责。动机与范围边界见 `proposal.md`（Why / What Changes / 明确移出本变更范围），此处不重复。
- **能力现状（规格真相源）**：`element-locator-projects` 明文要求 **exactly three locator projects**，故本次是 spec 级行为变更，`.openspec.yaml` **不得**置 `skip_specs`，必须出 delta。
- **已核实的外部依赖（决定了连带范围）**：
  - `apps/dashboard/views.py:23,87,88` 读 `WebElement` / `ApiEndpoint` 出 KPI（跨 App 读 Model，合规）
  - `frontend/src/modules/workflow` 读 `/elements/web-groups/`、`/elements/web/`、`/elements/api-endpoints/`
  - `tools/seed_api_endpoints.py` 把平台自身 API **写入** `ApiGroup` / `ApiEndpoint`（该 App 外的唯一写入方，经 `apps.element_locator.models` 直接 ORM —— 属既有遗留，见防火墙自检）
  - 守护 `tests/graybox/unit/test_api_path_callers.py` 维护**四面**调用面，其中 `catalog` 面即该工具、`frontend` 面含将被删除的 11 个调用点
- **ApiNode 的强制连带性（核实结论）**：`registry/nodeRegistry.ts` 对 `ApiNode` 的注释为「无默认端口，关联 API 端点后从 schema 动态生成」，`defaultInputs` / `defaultOutputs` 皆空；`addApiPort` 的唯一调用点在 `PageFlowVueFlow.vue` 的接口选择器内。故 ApiNode 的端口唯一来源就是被删能力 → 保留即留下不可用节点。
- **存量数据形态**：`workflowStore.applySnapshot()` 对节点不做类型校验（`nodes.value = data.nodes || []`），注册表查询两处均为可选链（`NODE_REGISTRY[type]?` / `registry?.`）。即存量原型里的 `ApiNode` 在代码删除后**不会崩**，只会退化为普通节点。

## Goals / Non-Goals

**Goals:**

- 元素定位收敛为**单一 Android 项目**，前端不再存在 Web/API 域的入口、类型与封装
- 后端 Web/API 五域（模型 / 表 / 序列化器 / ViewSet / 路由 / admin / 写函数 / 目录树分支）归零
- workflow 不再依赖元素定位的 Web/API 端点；画布只剩 Android 页面素材
- 接口资产目录能力完整退役（工具、守护面、spec 三者同批消失）
- 全部门禁在改动后仍为绿（含按实测重登记的规模下限）

**Non-Goals:**

- 不动 Android 域的 `PageFlow`（跳转流）、`Page`、`Element`、`LocatorProject`、`LocatorDirectory`
- 不动 dashboard 的「Web用例 / API用例」（`web_automation` / `api_testing`，来自 case-manager 的用例类型）
- 不改写存量 workflow 原型数据（见 D6）
- 不解决元素定位页面其余既有死分支（`back` emit、`hideIdentity`、`activeFileId`、`reload`）；`element-locator/AGENTS.md`（0 字节）仍只记录

## Decisions

**D1 数据删除：一次迁移直接删表，并要求迁移前留备份**
`models.py` 删除五个模型后，`makemigrations` 会生成一个 `DeleteModel` 迁移，落库即 `DROP TABLE`。
理由：用户已明确「含模型与数据」；五张表在代码删除后无任何读写方，保留孤儿表只会持续污染 schema 与后续迁移。
备选：两阶段（先删代码、下个发布周期再删表）→ 否决：会把「表在但无人用」的僵尸态带过一个周期，且与「全栈清零」的目标相反。
代价与对冲：**数据不可逆**。故 tasks 要求在应用迁移前执行 `manage.py dumpdata element_locator`（含五模型）留档，并在迁移文件 docstring 中写明不可逆。

**D2 删除边界：`WebPageFlow` 删，`PageFlow` 留**
依据：`PageFlow`（`el_page_flows`）是 **Android 页面**跳转流，既不属 Web 也不属 API；`WebPageFlow`（`el_web_page_flows`）是 Web 域，属本次范围。
备选：一并删除 `PageFlow` → 否决：超出用户请求（用户说的是 web 与 API），且会误伤 Android 域能力。

**D3 `api-endpoint-catalog` 整能力退役，用 REMOVED Requirements 表达**
落地三件套必须同批：删 `tools/seed_api_endpoints.py`、删守护的 `catalog` 面、在 delta 里对该能力的唯一需求写 `## REMOVED Requirements`（含 Reason / Migration）。归档同步后该能力需求归零，主 spec 由归档流程删除，不留空壳。
备选：保留 spec 改指向新载体 → 否决：当前没有替代载体，编造一个载体正是 spec 要禁止的「为了通过校验而造需求」。

**D4 调用面守护由四面收敛为三面；`frontend` 面下限按实测重登记**
`test_api_path_callers.py` 的 `catalog` 面整体移除（面不存在就不该留一个恒为 0 的空面，否则下限语义失效）。`frontend` 面将减少 11 个调用点（元素定位 8 + workflow 2 + pageCatalog 1），按实施时实测值的 ~95% 重登记，并在注释写明「因 Web/API 域下线删除 11 个调用点，非扫描器退化」。
备选：把 `catalog` 面下限改为 0 → 否决：规模下限的用途是发现「扫描器漏扫」，恒 0 的下限恒真，等于删除该守护却留下假象。

**D5 workflow 的两个连带项（「关联 Web 页面」、「ApiNode 节点类型」）一并删除**
依据见 Context 的两条核实结论：前者数据源即被删的 `listWebGroups` / `listWebGroupElements`；后者端口唯一来源即被删的接口关联。
备选：只删「关联 API 接口」而保留 `ApiNode` → 否决：会留下 `defaultInputs/Outputs` 为空、无任何途径补端口的节点类型，等于交付一个坏功能。

**D6 不改写存量 workflow 原型数据，改为验证「优雅降级」**
依据：`applySnapshot` 不校验节点类型、注册表查询均用可选链，故存量 `ApiNode` 渲染不崩；其持久化的 `outputs` 仍在。
决策：不写数据迁移、不写清理脚本，改为在 tasks 中要求**用一份含 ApiNode 的原型快照验证**：画布可打开、节点可见、无控制台报错、其余节点连线正常。
备选：迁移时清理存量 JSON 中的 ApiNode 与相关连线 → 否决：那会**不可逆地改写用户内容**，且判定「哪些节点该删」缺乏产品依据；宁可降级展示，把清理留给将来有明确处置口径的变更。

**D7 保留 `LocatorProject` / `LocatorDirectory` 结构，前端不硬编码 `'android'`**
理由：项目仍由 `GET /api/elements/projects/` 驱动；把「只有一个项目」表达为「列表接口返回一个」而不是前端写死，改动最小且保留了将来加回项目形态的余地。
落地：`LocatorProjectCode` 收敛为字面量 `'android'`，`isLocatorProjectCode` 只接受它；`LocatorFileKind` 收敛为 `'page'`。
备选：把 `projectCode` 整个从路由与 composable 移除（无项目概念）→ 否决：会推翻 `element-locator-projects` 的目录树模型与现有路由 `/elements/projects/:code`，远超下线 Web/API 的需求。

**D8 两处主 spec 的 `## Purpose` 直接修改，而不是放进 delta**
`element-locator-projects` 与 `api-path-convention` 的 Purpose 分别描述了「三项目」与「端点资产目录」调用面，归档只合并 Requirements，Purpose 需直接改主 spec。
理由：这是 OpenSpec 的既定手法（delta 的 `## Purpose` 对既有能力会被忽略）。
备选：在 delta 里写 Purpose → 否决：会被忽略，主 spec 留下失真描述。

**D9 前端 element-locator 的分支收敛方式：删净 Web/API 分支而非保留通用分支**
`LocatorFilePanel` 删除 web/api 两个表单与 `saveWeb`/`saveApi`；`loadDetail` 只保留 `page` 早返回；`LocatorTree` 的 `createFileLabel`/`fileKindOf` 固定为页面。
备选：保留 Web/API 表单代码但不可达 → 否决：正是上一轮清退过的死代码形态，不应再造。

**D10 `api-path-convention` 用「REMOVED + ADDED」而非「MODIFIED」表达收窄**
`openspec validate --strict` 会拒绝「MODIFIED 块丢弃既有场景」：MODIFIED 语义是整块替换，校验器要求把当前 spec 仍有的场景全数抄入，因此**无法**用它表达「这条需求少了一个场景」。
决策：把旧的「端到端调用方遵循唯一写法」整条 REMOVED（含 Reason / Migration），并 ADDED 一条收窄后的「前端与测试调用面遵循唯一写法」。
备选：保留 MODIFIED 并强行带上「端点资产目录」场景 → 否决：该场景的前提（目录工具）已删除，保留即写入一个不可能成立的断言。备选：REMOVED 与 ADDED 同名 → 否决：归档合并顺序未定义，同名会造成结果不确定。

## 模块防火墙自检

- **跨 App import**：本次**只减不增**。删除 `apps/dashboard/views.py` 对 `WebElement` / `ApiEndpoint` 的 Model 读（跨 App 读 Model 本属允许，此处是收敛职责）；不新增任何跨 App import。
- **禁止跨 App import service/runner/consumer/state_machine**：不涉及。
- **写库收敛到 `api.py`**：本次不新增写路径。**须在实施时登记一处既有违规**：`tools/seed_api_endpoints.py` 直接 `from apps.element_locator.models import ApiEndpoint, ApiGroup` 后 `update_or_create`，绕过了 `element_locator/api.py`。该文件本次整体删除，故违规随载体消失，属"删除即修复"，不新增债务。
- **前端不直连数据库**：不涉及；本次删除前端 HTTP 调用点，调用面只减。
- **通信通道**：不新增 HTTP 端点 / WebSocket / SSE；`/api/elements/` 下 Web/API 路由全部移除（净减 5 组），WS 与 SSE 生产点不变。
- **跨模块影响**：`dashboard`（去 KPI 项）与 `workflow`（去 Web/API 素材与 ApiNode）均为**减少**对 `element_locator` 的依赖；无新增耦合。
- **关单附加项**：涉及跨模块改动，须跑 `python tools/gen_arch_stats.py --check-boundaries`。

## Risks / Trade-offs

- [数据删除不可逆] → 迁移前 `dumpdata` 留档；迁移 docstring 标注不可逆；proposal 已标 **BREAKING**。
- [漏改调用方导致 500] → 删除后必须让 `python manage.py check`、`makemigrations --check`、`ruff`、`pytest -m "unit or integration"`、`npm run typecheck`、`vite build` 全绿；`typecheck` 会逐处暴露对已删导出/类型的引用。
- [守护下限连降导致门禁失守] → `frontend` 下限下调必须附「删除了哪些调用点」的清单；`catalog` 面是整体移除而非设为 0；保留 `test_multiline_call_sites_are_captured` 与 `test_exception_list_entries_are_real` 这两条与计数无关的扫描器健康守护。
- [存量 ApiNode 原型渲染异常] → D6 的快照验证任务；两处注册表查询已确认使用可选链，预期降级为普通节点。
- [接口资产目录退役导致接口测试无资产可用] → `tests/api/` 本就以 YAML + 路由表为准，不依赖该目录；退役后接口契约断言路径不变（`api-path-convention` 的三面仍然生效）。
- [工作区存在大量并发未提交改动（含其他会话在改 device-inspector）] → tasks 锚定符号不锚定行号；改动面以 mtime 窗口 + 逐文件 `git status` 核对，不用裸 `git diff --stat` 当凭据。
- [vitest / vite build 在受限沙箱下 EPERM] → 需 `danger-full-access`；本会话已实测该模式可跑。

## Migration Plan

1. 后端：删模型 → `makemigrations`（生成 `DeleteModel` 迁移）→ `migrate` 前先 `dumpdata element_locator` 留档 → 应用迁移
2. 后端：删序列化器 / ViewSet / 路由注册 / admin / `api.py` 写函数 / `api_projects.py` 与 `api_directories.py` 的 web/api 分支；`dashboard/views.py` 去 KPI
3. 工具：删 `tools/seed_api_endpoints.py`
4. 前端：元素定位收敛 → workflow 收敛 → dashboard KPI 收敛
5. 测试：`frontend/tests/element-locator/p0/api.spec.ts` 收敛到 10 个；`tests/graybox/unit` 与 `tests/arch` 同步；`test_api_path_callers.py` 四面 → 三面并重登记 `frontend` 下限
6. 验收：`manage.py check` + `makemigrations --check` + `ruff` + `pytest -m "unit or integration"` + `pytest tests/graybox/unit` + `npm run typecheck` + `vite build` + `npm run lint:styles` + `vite build 后` 的含-ApiNode 原型快照验证
7. 回滚：代码 `git revert` 即恢复路由与视图；**数据需从第 1 步的 `dumpdata` 备份恢复**（`loaddata`），无自动回滚
