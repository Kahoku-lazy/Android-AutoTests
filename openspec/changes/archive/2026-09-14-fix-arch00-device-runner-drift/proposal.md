## Why

ARCH-00 是平台架构总纲，自 2026-08-21（v3.2）后未再同步。此后两个**已归档** OpenSpec 变更与一次重构把它的两个主题整段推翻，文档仍在描述已不存在的层与已下线的 App：

**1) L2「设备交互中台」整层已扁平化。** 归档变更 `2026-09-03-flatten-device-session`（tasks 1.1/2.1/2.2/3.1/3.2）删除了 `apps/device_pool/session.py`、`DEVICE_SESSION_ENABLED` 开关与 `pool.py` 的操作部分，调用链改为「上层 → 引擎」+ `DeviceLock` 业务租用。全仓实测：

- `DEVICE_SESSION_ENABLED` 代码 **0 命中**；`LeaseMode` / `LeaseConflict` / `LeaseError` **0 命中**；`apps/device_pool/session.py` 在 HEAD **不存在**；
- `DeviceSession` 仅剩 3 处注释（`engines/device/registry.py:6`、`engines/device/base.py:4`、`config/settings.py:144`）；
- 真实消费点是引擎工厂 `open_engine` / `close_engine`：`apps/device_pool/views.py:14`、`apps/device_inspector/service.py:34`+各处、`apps/ai_assistant/tools.py:114,160,190,220,249`；租用是 `apps/device_pool/api.py` 的 `acquire_device` / `release_device` + `DeviceLock`；
- `apps/device_pool/pool.py` 现为 23 行，只剩「当前激活设备」指针。

**2) 引擎坐标与语义失准。** 代码真相：`engines/device/registry.py`（不是 `engines/registry.py`）· `engines/device/android/u2.py`（不是 `android/airtest_u2.py`）· 类名 `U2Engine`（`u2.py:58`，不是 `AirtestU2Engine`）· `ENGINE_REGISTRY = {"u2": ...}` + `DEFAULT_ENGINE = "u2"` · `DEVICE_ENGINE` 默认 `"u2"`（`config/settings.py:145`）。同变更 tasks 1.1 已**回退**引擎侧缓存/实例锁/connect 幂等（结论：引擎保持无状态、短连接），故「进程内缓存 + 线程安全」不成立；`EngineContractTestBase` 全仓 **0 命中**（契约测试基类不存在，`openspec/specs/engine-protocol/spec.md` 仍在）。

**3) test_runner 已下线。** `1c4c47cf` 删除其 api/executors/views/consumers，`migrations/0020_delete_test_runner_models.py` 卸载 `tr_*` 4 表；`apps/test_runner/AGENTS.md` 明写「执行引擎已下线…禁止恢复 views / urls / WS / 执行器」；`config/urls.py` 已无 `runner` 挂载；前端 `test-runner` 模块已删除（模块数 9→8）；`gateway/routing.py` 的 `websocket_urlpatterns` 为**空表**（WS 生产点 0）。

**后果**：§1.6 #1/#2/#11 与 §A.5/A.6 的「残留 / 工具盲区」指向已删除的 `state_machine.recover_orphans`；接手者按 §4.4 去找 `session.py` 会扑空；按 §七 设置 `DEVICE_SESSION_ENABLED` 不会产生任何效果；§3.2/§A.1 仍在统计一个已下线的 App。

## What Changes

纯文档同步，**只改 `dev_docs/03-设计与架构/ARCH-00-平台总体架构.md` 一个文件**，分四组：

1. **删除 / 替换 L2 会话层描述**：§1.1 层表 L2 行、§1.2 全景图 L2 subgraph 与 `DeviceSession` 连边、§1.3 防火墙 L2 规则、§二 逐层表 L2 行、§3.1 模块图 MID/SES、§4.4 整节、§5.2 目录树 `session.py`、§六「DeviceSession 租用式会话」决策、§七 `DEVICE_SESSION_ENABLED` 开关行。改为现行事实：**L2 已空置**（上层直调 `engines.device.registry` 工厂 + `DeviceLock` 业务租用）。
2. **修正引擎坐标与语义**：`engines/device/{base,registry,connection}.py`、`engines/device/android/u2.py`、`U2Engine`、`DEFAULT_ENGINE="u2"`、`DEVICE_ENGINE` 默认 `u2`；删除「进程内缓存 + 线程安全」；`EngineContractTestBase` 标注为未落地。
3. **test_runner 下线同步**：§1.2/§1.3/§3.1 图中的执行 App 节点、§1.5 裸 view 范式行与信封例外、§1.4 WS 端点（2→0，与 §1.4 现状自述一致）、§1.6 #1/#2/#5/#9/#11、§3.2/A.1 App 行、§3.3/A.4 前端模块（9→8）、§4.2 状态机整节、§8.3/§8.4、§A.2 `tr_` 行、§A.3 执行组、§A.5 依赖边、§A.6。
4. **记账**：版本行升 v3.3 + 变更记录新增一行；附录 A 加「口径含已下线 test_runner 项」注并给出实测基准。

## 关联文档

- 依据变更（已归档）：`openspec/changes/archive/2026-09-03-flatten-device-session/`、`openspec/changes/archive/2026-08-20-introduce-device-session/`、`openspec/changes/archive/2026-08-20-executor-session-toggle/`
- 代码真相源：`engines/device/registry.py` · `engines/device/android/u2.py` · `apps/device_pool/{pool,manager,api}.py` · `gateway/routing.py` · `config/{settings,urls}.py` · `apps/test_runner/AGENTS.md`
- 被测文档：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`

**范围外登记（本次不修，另行变更）**：

- 计数复测：表总数（文档 35 / 实测 33）、路径端点（143 / 实测 116）、Tool 数（26 / 实测 12）——用户裁定归「计数与端口同步」另案；本次只删除 test_runner 行 + 修正 WS 生产点数与前端模块数（这两项直接由 test_runner 下线决定）。
- SSE 通道口径（§1.4 ③、§4.5、§二 L4 行、§3.2 ai_assistant 行）与 `architecture.md` 引用的悬空问题。
- `openspec/specs/device-session/spec.md` 的退役（spec 级变更，不能夹带在文档变更里）。
- `dev_docs/03-设计与架构/技术栈参考.md:61` 的 `tr_` 行、子 ARCH（ARCH-06/07）口径。
- D0-5/6 安全默认值（`按顺序修复` 第 3 项）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无；本次为纯文档同步，无需求级行为变化，`.openspec.yaml` 已声明 `skip_specs: true`）

## Impact

- **修改**：`dev_docs/03-设计与架构/ARCH-00-平台总体架构.md`（唯一文件）
- **不影响**：`apps/` · `engines/` · `gateway/` · `config/` · `frontend/` · API 契约 · 路由 · DB · `openspec/specs/`
- **测试范围**：`python tools/gen_arch_stats.py --check-md`（记录文档-代码漂移报告）· 全量残留 grep · `openspec validate fix-arch00-device-runner-drift --strict`
