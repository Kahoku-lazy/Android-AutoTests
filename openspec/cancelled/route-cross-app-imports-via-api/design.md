# Design: route-cross-app-imports-via-api

## Context

动机见 proposal.md。代码事实（审计亲验）：dashboard/ai_usage.py:20 import usage_ledger.rates 两常量；:17 与 report_inventory.py:21、bug_manager/api.py:18 import task_list.case_identity。`utils/gen_arch_stats.py --check-boundaries` 现行规则不覆盖「跨 App import 内部常量/纯函数」形态，实测漏报。约束：跨 App 只允许读 Model 或调对方 api.py；不改计费口径与响应形状。

## Goals / Non-Goals

**Goals**
- 跨 App 读取全部经对方 api.py；门禁能抓住本类违规（含负向自测防规则退化）。

**Non-Goals**
- 不动 engines 私有函数访问（另行立项）；不处理 shared→app 反向依赖；不改 task_list/AGENTS.md 的 case_identity 例外表述（属变更⑤文档批）。

## Decisions

### D1 导出形态：函数口而非裸常量 re-export
`usage_ledger.api.display_fx() -> dict`（含 fx_date / usd_cny），内部读 rates。理由：api 门面以函数为契约单元，裸常量 re-export 会让 `__all__` 与「写库走 api」的门面语义混杂；dashboard 侧一次调用取两值，语义不变。备选：api 直接 re-export 两常量——改动更小但门面形态不一致，弃。
`case_identity_label` 是纯函数，api.py 直接 re-export 并进 `__all__`（与既有 case_identity 纯函数先例一致，task_list/AGENTS 已允许该函数被跨 App 读）。

### D2 门禁规则白名单：api / models / contracts
跨 App import 允许模块名白名单 = `{api, models, contracts}`（contracts 为 device_pool 既有跨 App 契约件，审计确认其消费形态合规）；其余（rates/pricing/case_identity/services/manager/…）一律违规。规则以 AST import 解析实现，覆盖 `from X import Y` 与 `import X.Y` 两形态。负向自测：在临时 fixture 构造违规 import 断言检查器报错（不落生产代码）。

### D3 与变更②的时序
②先合并（ai_usage.py 死参数/空桩删除在先），本变更再改道 import，避免同文件双向冲突。若②未合并，本变更等待，不并行改同一文件。

## Risks / Trade-offs

- [门禁新规则误伤既有合规 import] → 以修复后全仓为基线跑 `--check-boundaries` 必须零违规；白名单外的历史合规形态（如 backend→engines 既有豁免）不受影响（规则只约束 apps 之间）。
- [display_fx 函数口增加一次调用开销] → 常量读取，可忽略。

## Migration Plan

纯重构，无迁移。回退 = 还原提交（import 改道可逆，门禁规则可单独还原）。

## Open Questions

无。