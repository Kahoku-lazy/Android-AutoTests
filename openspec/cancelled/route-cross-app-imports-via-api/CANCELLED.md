# 已取消：route-cross-app-imports-via-api

> 状态：**cancelled**（2026-11-23，需求方决定）
> 原因：**未启动**（tasks 0/6），统一取消未开工变更，收敛在途数量；原文全部保留以便恢复。
> 位置：openspec/cancelled/route-cross-app-imports-via-api/（不在 openspec/changes/ 下，CLI 不会列为活跃变更）

## 取消前的原定内容（摘自 proposal）

审计确认一处存活红线违规：dashboard 跨 App import usage_ledger.rates 内部计价常量。

## 恢复方法

把本目录整体移回 openspec/changes/route-cross-app-imports-via-api/，即可重新出现在 `openspec list`；tasks 仍是未勾选状态，从第 1 项做起。
恢复前建议先复核 proposal 的事实是否仍成立（代码在动，审计结论可能过期）。

## 取消后的实际影响

**红线违规仍在**（跨 App 内部实现 import）。

取消只去掉**跟踪载体**，不改变代码现状。上述问题若仍要处理，须重新立项。