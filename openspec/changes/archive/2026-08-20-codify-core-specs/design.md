## Context

实现已落地并经真机验证；本变更只把既成契约写成规范（SHALL/MUST），供后续变更引用与回归。

## Goals / Non-Goals

**Goals:**

- 两份 spec delta 覆盖协议核心行为（与 L2/L1c 详档 §2.3/§三 一致）

**Non-Goals:**

- 不新增需求（只记录已实现行为）；不改实现

## Decisions

- Requirement 粒度 = 详档的"铁律级"行为（互斥/前置/并发/错误/原语/标准化/能力/注册/契约测试）；每 Requirement ≥1 Scenario
- 场景与现有测试对应（tests/device_pool/test_session.py、tests/engines/contract_base.py 等）

## 模块防火墙自检

- 纯文档；通过

## Risks / Trade-offs

- [spec 与实现漂移] → 后续变更走 Modified Capabilities 同步
