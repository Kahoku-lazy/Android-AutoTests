## Context

设备管理模块职责边界已写入 apps/device_pool/AGENTS.md（只管设备状态）。本次执行前 grep 核实了所有「删除」候选的调用方，发现历史函数与 d/engine 均有跨 App 引用，故收敛范围收窄为「纯冗余 + 规范」两项。

## Goals / Non-Goals

- Goals：消除同口径前缀常量散落、修正函数内 import。
- Non-Goals：不删透传 action、不清 d/engine、不清历史函数、不搬迁操作能力（均经 grep 核实有跨 App 调用方，属过度设计大动作）。

## Decisions

1. 前缀常量收敛到 contracts.py 单一落点，不新建文件（克制）。
2. 历史函数保留（有跨 App 调用方），从方案撤回，不因「怕臃肿」而误删。
3. 透传 action / d·engine 保留（涉及跨 App 改道），登记为后续独立评估项。

## 防火墙自检

- device_pool 内部收敛，无跨 App import 变更；contracts.py 仍为纯数据层，无越界。

## Risks / Trade-offs

- 前缀常量 device_inspector 仍有一份（跨 App 未收敛），登记为同步项，后续经 api.py 或共享常量收敛。

## Migration Plan

已完成：常量收敛 → import 规范化 → 回归验收全绿。
