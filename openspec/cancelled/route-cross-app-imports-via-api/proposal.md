# Proposal: route-cross-app-imports-via-api

## Why

审计确认一处存活红线违规：dashboard 跨 App import `usage_ledger.rates` 内部计价常量（DISPLAY_FX_DATE / DISPLAY_FX_USD_CNY），违反 apps/AGENTS §1.2「严禁跨 App 内部实现 import」；且 `--check-boundaries` 门禁对此形态漏报（实测零违规通过）。另有 `task_list.case_identity` 纯函数被三个 App 直接 import 的两级规则冲突——需求方已裁决：**收进 task_list/api.py 导出**，不改红线文本。本变更把跨 App 读取全部收敛到对方 api.py，并补上门禁盲区。

## What Changes

- **usage_ledger**：api.py 增只读导出 `display_fx()`（返回展示汇率与日期，内部读 rates 常量）；rates.py 降为内部实现。
- **dashboard**：ai_usage.py 改调 `usage_ledger.api.display_fx()`，删除对 rates 的直接 import。
- **task_list**：api.py 导出 `case_identity_label`（re-export case_identity 纯函数，纳入 `__all__`）。
- **dashboard / report_generator / bug_manager**：三处 `task_list.case_identity` 直接 import 改调 `task_list.api.case_identity_label`。
- **门禁补盲**：utils/gen_arch_stats.py 的 `--check-boundaries` 增规则——跨 App import 非 `api`/`models`/`contracts` 白名单模块即违规（覆盖常量/计价件/纯函数形态）；以本变更修复后的代码为基线自检零违规，并用修复前的违规形态做负向自测。
- 纯重构：所有响应形状、字段、计费口径不变。

## 关联文档

无新增 PRD 需求编号——纯重构 + 门禁工具变更。问题来源为后端审计报告 R-1 / R-5；需求方已裁决 case_identity 走 api 导出（不改红线例外清单）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无——纯 import 路径重构与工具增强，无需求级行为变化；按 schema 约定设 `skip_specs: true`。）

## Impact

- **backend**：usage_ledger/api.py、dashboard/ai_usage.py、task_list/api.py、report_generator/report_inventory.py、bug_manager/api.py（各一处 import 改道）。
- **utils**：gen_arch_stats.py 边界检查规则。
- **tests**：tests/arch/unit 边界相关用例（如有）同步；新增门禁负向自测。
- **协调**：dashboard/ai_usage.py 与变更②（retire-backend-dead-code 5.2）同文件——建议②先合并，本变更基于其后工作树改道，避免冲突；task_runner 对 pricing 的死 import 已划归变更②（2.5），本变更不重复处理。
- **明确排除**：engines 私有函数访问（pricing._is_peak_time、serial_log._port_in_use）需 engines 侧立公开口，走 engines AGENTS 流程另行立项；shared→app 反向依赖属分层债登记项，不在本变更。