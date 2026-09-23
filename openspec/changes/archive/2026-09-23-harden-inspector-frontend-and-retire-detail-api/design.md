## Context

动机见 proposal.md - Why。方案需要的事实（2026-09-23 实测，HEAD `01e17632`，模块工作区无未提交改动）：

- 媒体展示 URL 拼接有 **3 份**实现：`device-inspector/store.ts:32`（`mediaUrl`）、`element-locator/helpers/elementPresentation.ts:4`（`elementThumbnailUrl`）、`ai-assistant/helpers/task-detail.ts:144`（`attemptScreenshotUrl`，额外直通绝对 URL / `data:` / 已带 `/` 的路径）。
- 执行引擎占用前缀有 **2 份**：`device-pool/constants.ts:66`（`RUNNER_OCCUPIED_PREFIXES`，被 `DeviceCard.vue:36`、`DeviceActionsCell.vue:17`、`DeviceStatusCell.vue:21` 消费）与 `device-inspector/store.ts:24`（`EXEC_PREFIXES`，被 `store.ts:26` 消费）。两处判定粒度不同：设备管理页的 `isRunnerOccupied` 只看前缀，`DeviceStatusCell` 与检查器还要求 `status === 'BUSY'`。
- 截图几何全在 `ScreenshotView.vue` 内：`boxOf`（`coords` → `x/y/width/height` → `bounds` 文本三形态，`:210-234`）、`hitTest`（DOM `getBoundingClientRect` + `displayScale` 后取面积最小者，`:367-389`）、`normalizeColor/withAlpha`（`:251-263`）。该文件 474 行、无单测。
- 快照详情端点：`urls.py:21` → `views.py:66` → `api.get_snapshot`（`api.py:308`），前端无调用方；`tests/api/case/inspector.yaml` 仍有 TC-INS-003（未登录 401）与 TC-INS-030（不存在 404）两条用例；`api.snapshot_to_dict`（`api.py:589`）仍被 `capture_snapshot` 使用（`api.py:113`），不可删。
- `tests/graybox/unit/test_api_path_callers.py` 会把 `tests/api/case/*.yaml` 的 `path:` 逐条 `django.urls.resolve()`：删端点前必须先删这两条用例，否则默认单元套件失败。
- 并发变更 `fix-locator-workbench-contract-and-cleanup` 明确「两条元素定位零调用端点下线另开变更」，与本变更不重叠。

## Goals / Non-Goals

**Goals:**

- 四项动作各自落地且可验证：共享登记处唯一、截图几何纯函数有单测、保存弹窗有分支用例、快照详情端点彻底退役且文档 / 用例同步。
- 行为零漂移：收敛与抽函数只改实现位置，不改可观察行为（框线、命中取舍、提示文案、提交体形状）。

**Non-Goals:**

- 不修「重试兜底静默」：`store.ts:139-143` 在失败来源匹配不到已知四类时静默返回，属独立缺陷，另开变更。
- 不改七项交互标志、列集合、固定 14 行分页、布局与样式令牌；不改分层端点的返回形状与筛减语义。
- 不为截图区新增缩放 / 平移能力（属能力边界，非本轮动作）。
- 不清理其它模块的无消费方端点（元素定位 `POST /api/elements/move/`、`POST /api/elements/files/batch-delete/`）。

## Decisions

1. **共享件落点用 `frontend/src/shared/helpers/`，不让模块互相 import。** 备选：检查器直接 import `device-pool/constants.ts` 的前缀清单——被否，跨模块 import 其它模块内部实现，违反 `frontend/AGENTS.md`「跨模块的组件放在 `shared/`」。
2. **占用口径共享件同时提供两种粒度，逐处替换为语义相同的那一个。** `isRunnerOccupied(occupiedBy)`（只看前缀，供 `DeviceCard` / `DeviceActionsCell`）、`isExecutionOccupied(device)`（`BUSY` + 前缀，供 `DeviceStatusCell` 与检查器）。备选：只提供 `isExecutionOccupied` 并让设备管理页也加 `BUSY` 判断——被否，会改变设备卡在非 `BUSY` 占用时的可操作态。
3. **媒体 URL 共享件只承担相对路径拼接。** `mediaUrl(path)`：空路径 → 空串，否则 `/media/{path}`。AI 助手的绝对 URL / `data:` / 已带 `/` 直通分支留在 `attemptScreenshotUrl` 内，只把最后的字面量拼接换成共享件。
4. **截图几何只抽纯函数，DOM 基准留在组件。** 抽 `boxOf(el)` 与 `pickElementAt(elements, x, y)`（画布坐标系，取包含命中点且面积最小者，宽高 `<= 0` 跳过）；`getBoundingClientRect` / `displayScale` / canvas 尺寸仍由组件计算后把坐标与比例传进去。备选：连 `hitTest` 一起抽并把 rect / scale 作为参数注入——被否，纯函数签名要携带 DOM 量，测试价值低且与组件耦合。
5. **命中策略先锁测试再替换调用点。** 现状语义（面积最小者取胜、零宽零高不参与、点在框外返回 null）先写成用例，再改组件，保证 diff 只落在调用点。
6. **保存弹窗用例用 `vi.mock` 固定元素定位项目树。** 与 `frontend/tests/device-inspector/p0/store.spec.ts:19` 的既有替身范式一致，用例零网络、零凭据。
7. **端点退役一次删干净：路由 + 视图 + 公开函数 + 白名单条目 + 用例 + 文档。** `snapshot_to_dict` 保留（仍被采集链路使用）。删除顺序上用例先删、路由后删，具体见 tasks 第 4 组。备选：保留端点并在文档登记为「预留」——被否，无消费方且与分层端点职责重叠，只会留下虚假的文档覆盖面。

## 模块防火墙自检

- **跨 App import**：本变更不新增任何跨 App import。删除的 `api.get_snapshot` 只被本 App 视图调用，属白名单收敛；`snapshot_to_dict` 保留且仍只在 `apps/device_inspector` 内部使用。
- **service / runner / consumer / state_machine**：不涉及。
- **写库收敛**：无新增 INSERT/UPDATE/DELETE；端点退役不触碰任何数据行。
- **前端**：不直连数据库；共享件的依赖方向是「模块 → `shared/`」，MUST NOT 出现「`shared/` → 模块」，任务 1.7 以此收口。
- **仪表盘**：不涉及。

## Risks / Trade-offs

- [删除端点可能影响仓外消费方] → 仓内三个调用面（前端 API 层、`tests/`、`tests/api/case/*.yaml`）实测均无调用方；分层端点提供同一份数据且字段更多；BREAKING 已在 proposal 标注；回滚 = revert 本提交（无数据迁移）。
- [用例与路由删除顺序错误会让默认单元套件先红] → tasks 4.1（删用例）排在 4.2/4.3（删路由与函数）之前，并以 `test_api_path_callers.py` 收口。
- [收敛共享件时占用判定漂移] → 共享件保留两种粒度，逐处替换为语义相同的那一个，并用 `frontend/tests/device-pool/p0/*` 现有用例回归。
- [AI 助手媒体 URL 的直通语义被吃掉] → 共享件只做相对路径拼接，直通分支保留在原 helper，`task-detail.spec.ts` 继续守护。
- [抽纯函数时悄悄改了命中策略] → 用例先锁定现状（面积最小、零宽零高不计入、框外为 null），再替换组件内调用。
- [共享件被反向依赖，形成隐式循环] → 任务 1.7 断言共享件内不出现 `@/modules/`。
