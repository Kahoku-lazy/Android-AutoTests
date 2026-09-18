## 1. 概览与元信息

- [x] 1.1 版本行升 v3.3（日期 2026-09-14）并写本轮摘要；删除「含未提交的七步重构」失真表述（`439085a9`/`1c4c47cf` 已是 HEAD 祖先）
- [x] 1.2 `## 文档内容简述` 两条：五层表述与「会话租用」改为「L2 已空置 + 业务锁租用」
- [x] 1.3 `## 你能从文档获取什么信息` 的权威统计基准：标注 test_runner 下线后的口径
- [x] 1.4 `## 关联文档` 的正式契约列表：`device-session/spec.md` 标注「协议已扁平化，spec 退役另案」

## 2. §1.1 层定义 + §1.2 全景图

- [x] 2.1 §1.1 依赖方向链与「演进脉络」改写（去掉 `DeviceSession` 落地口径，补 09-03 扁平化）
- [x] 2.2 §1.1 层表：L2 行改为「已空置」；L3 行 App 数注明 test_runner 仅卸表迁移；前端模块 9→8
- [x] 2.3 §1.2 mermaid：删 L2 subgraph 与 `SES` 节点、test-runner 节点、`L3→L2→ENG` 连边（改为 `L3→ENG（引擎工厂）`）、`airtest_u2`→`u2`、WS 2 端点→0
- [x] 2.4 §1.2 存储节点表数标注（口径注）

## 3. §1.3 分层包图与防火墙

- [x] 3.1 §1.3 mermaid：删 `TR` 节点与 L2 subgraph；`DP` 去掉「L2 宿主」；过渡期 ⚠️ 连边（`DP-.->ENG`、`TR-.->ENG`）改为合法工厂边
- [x] 3.2 §1.3 防火墙文本：L3 允许项 `device_pool.session` → `engines.device.registry`（工厂）+ `device_pool.api`（业务锁）；删「L2 会话层」两条；L3 禁止项改为「引擎实现直触 / 裸句柄」

## 4. §1.4/§1.5 通道与范式

- [x] 4.1 §1.4 WS 节点与表格：2 端点→0 生产点（与本节现状自述一致）；`ws/test-run` 行随 test_runner 下线移除
- [x] 4.2 §1.5 网关图：删 `W1/W2` 与 `TR` 节点；`/api/{app}/ × 10` 去掉 `runner`
- [x] 4.3 §1.5 范式分布表：裸 Django View 行去掉 test_runner
- [x] 4.4 §1.5 信封例外：去掉 test_runner（其端点已不存在）

## 5. §1.6 偏差登记

- [x] 5.1 #1 `state_machine.recover_orphans` 直写 → 已消除（test_runner 下线 + `1c4c47cf`）
- [x] 5.2 #2 `DEVICE_SESSION_ENABLED` 旧路径 → 已消除（`flatten-device-session`：删 session.py/开关，上层直调引擎工厂）
- [x] 5.3 #3 `AirtestU2Engine.connect()` → `U2Engine.connect()`（`u2.py:137` 签名与返回 `self` 仍成立，保留偏差）
- [x] 5.4 #5 `tr_test_runs.status` 回填 → 随表卸载作废
- [x] 5.5 #9 平铺信封：去掉 test_runner
- [x] 5.6 #11 e2e 真机 + 双设备并行 → 改写为「执行链路已下线，该专测随之下线」

## 6. §二 五层逐层说明

- [x] 6.1 L0 行：Playwright/requests 触达口径改为实测（Playwright 仅 `tests/e2e`；requests 在 `ai_assistant`/`evaluator`）
- [x] 6.2 L1c 行：路径改为 `engines/device/{base,registry}.py · android/u2.py`；类名 `U2Engine`；`DEFAULT_ENGINE="u2"`
- [x] 6.3 L2 行删除，替换为「L2 已空置」说明行
- [x] 6.4 L3 行：删 `test_runner.state_machine`；依赖白名单 `device_pool.session` → 引擎工厂 + `device_pool.api`

## 7. §三 模块架构与速览

- [x] 7.1 §3.1 mermaid：删 `F_TR`/`B_TR` 节点与全部 `B_TR` 连边、MID 的 `SES`；`B_DP` 去掉「L2 宿主」
- [x] 7.2 §3.2 App 表：删 `test_runner` 行；`device_pool` 层改 `L3`；`report_generator` 职责改为「执行引擎已下线，列表为空；LOG_DIR 残留文件仍可下载」
- [x] 7.3 §3.3 前端模块表：删 `test-runner` 行，标题 9→8

## 8. §四 关键机制

- [x] 8.1 §4.2 状态机整节：改写为「已下线」（`tr_` 表由 0020 卸载；`models/test_models.py` 枚举保留但无消费方）
- [x] 8.2 §4.3 引擎注册表：路径 `engines/device/registry.py`；删「进程内缓存 + 线程安全」；补 `DEFAULT_ENGINE`；`EngineContractTestBase` 标注未落地
- [x] 8.3 §4.4 整节：由「DeviceSession 租用协议（L2）」改写为「设备消费与业务租用（原 L2 已扁平化）」
- [x] 8.4 §4.6 枚举真相源：删 `0019_backfill_lowercase_run_status` 回填口径

## 9. §五/§六/§七

- [x] 9.1 §5.1 目录树：`device-session/spec.md` 标注状态
- [x] 9.2 §5.2 代码地图：删 `session.py` 行；`engines/` 路径与类名修正；`gateway/routing.py` WS 2→0；`test_runner/` 标注仅卸表迁移；前端模块 9→8
- [x] 9.3 §六 决策表：`DeviceSession 租用式会话` → 扁平化决策；`五层分离` 措辞调整
- [x] 9.4 §七 关键开关：`DEVICE_ENGINE` 默认 `u2`；删 `DEVICE_SESSION_ENABLED` 行

## 10. §八 + 附录 A + 变更记录

- [x] 10.1 §8.3 任务状态表加「执行引擎已下线，仅保留枚举定义」注
- [x] 10.2 §8.4 WS 通道：2 端点 → 0；删 `ws/test-run` 行
- [x] 10.3 附录 A 起始加口径注（旧口径构成 + 实测基准 33/116/12/8 + 后续变更）
- [x] 10.4 A.1：删 `test_runner` 行；`device_pool` 层改 `L3`
- [x] 10.5 A.2：删 `tr_` 行
- [x] 10.6 A.3：删「执行 runner（4）」组
- [x] 10.7 A.4：删 `test-runner`，标题 9→8
- [x] 10.8 A.5：删 `test_runner` 被依赖行；`device_pool`/`case_manager` 行的 `test_runner`/`session.lease` 依赖项删除；删「残留」段
- [x] 10.9 A.6：`--check-boundaries` 行去掉 recover_orphans 盲区表述
- [x] 10.10 变更记录新增 v3.3 行

## 11. 验证

- [x] 11.1 全量残留 grep：`session.py` · `DEVICE_SESSION_ENABLED` · `DeviceSession` · `LeaseMode|LeaseConflict|LeaseError` · `airtest_u2` · `AirtestU2Engine` · `recover_orphans` · `executors/ui` · `tr_test_` · `tr_task_cards` · `engines/registry`。验证：`airtest_u2` / `AirtestU2Engine` / `engines/registry` **各 0 命中**；其余命中全部落在「已消除 / 已作废 / 历史 / 变更记录 / 防火墙模块名清单」语境（`session.py` 4：:47 演进脉络、:347 登记 #2、:369 L2 空置行、:505 历史注；`DEVICE_SESSION_ENABLED` 2：:347/:505；`recover_orphans` 3：:346/:708/:714；`tr_test_` 1：:350）
- [x] 11.2 `test_runner` 在 ARCH-00 内只允许出现在「已下线 / 卸表迁移 / 历史登记」语境。验证：全部 31 处命中经逐行判定为合规（含 §1.6 #1/#5/#11、§3.2/A.1 标题、§4.2、§8.4、§A.2/A.5 标题、§1.3 防火墙模块名清单、v3.0/v3.1/v3.3 变更记录）
- [x] 11.3 `python tools/gen_arch_stats.py --check-md` 运行并记录输出。验证：**退出码 0**，输出「💡 ARCH-00-平台总体架构.md 需要初始化 ARCH_STATS 区域」——本文无 auto 区域，故无自动 diff（既有事实，非本次引入）；注：PowerShell `>` 落盘为 UTF-16LE（BOM `255,254`），需转 UTF-8 后审阅（`temps/read_checkmd.py`）
- [x] 11.4 §七 开关行与 `config/settings.py` 逐项对齐。验证：`DB_ENGINE` 默认 `mysql`（`settings.py:141`）✓、`DEVICE_ENGINE` 默认 `u2`（`settings.py:145`）✓；`DEVICE_SESSION_ENABLED` 行已删（代码零命中）
- [x] 11.5 `openspec validate fix-arch00-device-runner-drift --strict`。验证：**Change is valid**（`skip_specs` 已声明，零 spec delta）
- [x] 11.6 附加：6 个 mermaid 块的子图配对 / 节点引用 / style 目标全部自洽（`node temps/check_mermaid.cjs` → 未闭合 0、未定义引用 0、style 悬空 0）
