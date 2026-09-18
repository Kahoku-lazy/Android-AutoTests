## Context

`device-session` spec 描述 2026-08-20 引入、2026-09-03 删除的会话租用协议。`ARCH-00` 已按现实改写正文，但把该 spec 的退役挂为「另案」。本单收口。

## Goals / Non-Goals

**Goals:**

- 让 spec 集合只包含**现行**行为契约，消除假契约
- 把 `ARCH-00` 里两处「退役另案」的挂起状态结清
- 清掉仍指向已删除层名的陈旧注释

**Non-Goals:**

- 不新建「设备租用 / 设备锁」能力的 spec（现状由 `ARCH-00` §4.4 承担；是否升格为正式 spec 属独立裁决）
- 不动 `ARCH-00` 的历史行（§1.6 #2/#11、§4.4 的历史注、v3.0/v3.1 变更行）—— 那些是准确的历史记录

## Decisions

### 1. 用 `REMOVED Requirements` delta 退役，而不是直接删文件

- **选择**：新增 `specs/device-session/spec.md` delta，逐条 REMOVED（含 Reason + Migration）
- **理由**：项目规则要求经 OpenSpec 工作流；REMOVED 是 schema 支持的规范操作，归档时由工具应用到主 spec，且 **Reason / Migration 强制填写** —— 强制留下「去哪了」的线索，比裸删文件更有价值

### 2. 逐条列全 4 条，不做部分移除

- **选择**：4 条全部 REMOVED
- **理由**：4 条同属一个已消失的层；留任何一条都会让读者以为该协议还在用

### 3. 顺带修两处引擎注释

- **选择**：`engines/device/base.py` · `engines/device/registry.py` 的 docstring 去掉 `DeviceSession` 指向
- **理由**：它们是同一处 drift 的代码侧残留，且是**注释**（零行为风险）；留着会让下一位读者按已删除的层理解引擎边界

## Risks / Trade-offs

- [归档后主 spec 变空] → 该能力确实不存在，空/删除都是正确终态；归档后复核 `openspec validate --strict` 与 `openspec spec list`
- [误删仍在用的契约] → 已实测全仓零消费；且「引擎协议」另有 `engine-protocol` spec
- [注释改动误伤代码] → 只改 docstring 文本，全量单测兜底

## Migration Plan

1. 写 delta + 改 `ARCH-00` 两处 + 改两处 docstring
2. `openspec validate --strict`（change）→ 通过后归档，由工具应用到主 spec
3. 归档后复核 `openspec validate --strict` / `openspec spec list`，并跑 `manage.py check` · `ruff` · 全量单测 · `--check-boundaries`
4. 回滚 = `git checkout` 文档与注释文件 + 从归档还原 spec
