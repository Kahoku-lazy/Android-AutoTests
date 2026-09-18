## Context

- 变更性质：**纯文档同步**（single file），无代码改动，故 `.openspec.yaml` 声明 `skip_specs: true`。
- 事实基线：HEAD = `885f4c95`；`git status --porcelain -- apps/device_pool apps/test_runner engines` 为空，即 `apps/`、`engines/` 无未提交改动，文档漂移是**已提交**代码与文档之间的漂移，不是工作区假象。
- 证据链（三条，均可复现）：
  1. `git log --diff-filter=D -- apps/device_pool/session.py apps/test_runner/state_machine.py` → `439085a9`（设备管理瘦身：删除 service/session，落地 manager 四职责）、`1c4c47cf`（apps 七步重构）；两者都是 `885f4c95` 的祖先（`git merge-base --is-ancestor` 通过）。
  2. 归档变更任务书自证：`2026-09-03-flatten-device-session/tasks.md` 2.1「删除 session.py」、2.2「DEVICE_SESSION_ENABLED 开关已删，统一走 get_device_engine + connect」、3.1/3.2「pool.py 只留状态管理」、1.1~1.3「引擎缓存/实例锁/connect 幂等**全部回退**」。
  3. 代码实测：见 proposal「Why」中的命中/零命中清单。
- 文档侧事实：ARCH-00 共 757 行，本轮命中 89 行（设备域 / test_runner 域关键词）。

## Goals / Non-Goals

**Goals:**

- 让 ARCH-00 的**设备层与 test_runner** 两域陈述与 HEAD 代码一致：读 §4.4 不会去找 `session.py`，读 §七 不会去设一个不存在的开关，读 §A.5/A.6 不会去追一个已删除的直写点。

**Non-Goals:**

- 不重测 / 不重排全文档计数（用户裁定归「计数同步」另案），只在附录登记实测基准。
- 不修 SSE 通道口径（另一题材）。
- 不删 `openspec/specs/device-session/spec.md`（spec 退役属 spec 级变更，另案）。
- 不重编号层级（见 D1）。
- 不动任何代码、测试、前端、子 ARCH 文档、`技术栈参考.md`。

## Decisions

**D1 保留 L0/L1a/L1b/L1c/L3/L4 编号，L2 标注「已空置」，不把 L3 下移为 L2。**
全仓已按「L3 = 业务 App」建立索引（`apps/device_pool/manager.py` 文档串「L3 业务层数据面」、`apps/AGENTS.md`、九份子 ARCH、`tools/gen_arch_stats.py` 的层标签）。把 L3 改成 L2 会产生数十处 ripple，且对读者零收益。代价是层号出现一个空档——用一行「L2 已空置（2026-09-03 扁平化）」显式解释，比隐式重编号更清楚。

**D2 计数不重测：测试相关行删除，总数保留并加口径注。**
用户已裁定「计数与端口」另案。若只删 `test_runner` 行而不动总数，附录内部求和会不平——因此在附录 A 起始处加注，写明：本附录为 2026-08-21 口径，其中含 test_runner 的 4 表 / 13 端点 / 4 Tool 已不存在，实测基准为 33 表 / 116 路径端点 / 12 Tool / 8 前端模块，全量复测见后续变更。**不臆造**一个「总数减 4」的新数字冒充实测值。

**D3 WS 生产点数按事实改为 0（2→0）。**
`gateway/routing.py` 的 `websocket_urlpatterns` 是空表，且文档 §1.4 的表格自述行（原文 :247）已经写「当前无生产点」——即同一节内自相矛盾。修掉计数是消除矛盾，不是新增计数题材；与 `tests/arch/test_channels.py` 的断言一致。

**D4 前端模块数 9→8。**
`frontend/src/modules/` 实测 8 个（无 `test-runner`），且该差额完全由 test_runner 下线产生，属本变更主题。

**D5 引擎事实按代码重写，并把「契约测试基类」标为未落地。**
`U2Engine` / `u2.py` / `DEFAULT_ENGINE="u2"` / `engines/device/registry.py` 为代码真相；「进程内缓存 + 线程安全」按 `flatten-device-session` tasks 1.1 的回退结论删除；`EngineContractTestBase` 全仓 0 命中 → 标注「契约测试基类未落地」，但**保留** `openspec/specs/engine-protocol/spec.md` 的引用（该 spec 仍存在且仍有效）。

**D6 test_runner 统一表述为「已下线（仅保留卸表迁移）」。**
引 `apps/test_runner/AGENTS.md` 与 `apps/report_generator/AGENTS.md` 的既有措辞（「列表为空」「LOG_DIR 残留文件仍可下」），不自行发明新口径。

**D7 §1.6 的登记项改为「已消除」而不是删行。**
§1.6 是偏差历史的审计台账；直接删行会丢失「曾经存在、何时消除」的信息。改为保留行号、把现象/状态改写为「已消除 + 消除方式（变更号/提交）」。#5（`tr_test_runs` 回填）因表已卸载，改写为「随 test_runner 下线作废」。

## Risks / Trade-offs

- [附录总数与被删行不再求和平衡] → 附录 A 起始加口径注，写明旧口径构成、实测基准与后续变更；宁可留一条可追踪的注释，也不臆造实测数字（D2）。
- [L2 空置说明被误读为「架构退步」] → 在同一处写明扁平化的收益（去掉一层转发、短连接、业务锁即租用），并指向 `flatten-device-session` 的 Why。
- [残留表述遗漏（例如 `test_runner` 在图中为节点名、或在表里为「依赖来源」）] → 收尾用关键词全量 grep 扫描（`session.py`/`DeviceSession`/`DEVICE_SESSION_ENABLED`/`airtest_u2`/`AirtestU2Engine`/`recover_orphans`/`state_machine`/`test_runner`/`tr_`），逐条判定「已下线表述 / 漏改」。
- [与后续「计数同步」变更冲突] → 本变更已把计数改动限制到 test_runner 直接决定的两项（WS 生产点、前端模块数），其余登记为范围外，冲突面最小。
