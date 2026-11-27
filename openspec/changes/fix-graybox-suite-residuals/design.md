## Context

两条失败的共同点：**断言没错，前置状态脏**。

- device：`update_device_status()` 的 10 秒缓存是性能设计（列表/心跳都调它，不缓存会把请求线程拖在 ADB shell 上）。真实服务里 10 秒内复用是期望行为；但用例之间共享同一个进程，缓存跨用例泄漏。
- auth：`me` 的 `user` 字段随功能演进增加（运营分组、作者授权），schema 是手写的护栏，没跟着改就成了「越守越红」。

## Goals / Non-Goals

**Goals**

- 两条失败转绿，且不是靠放宽断言（`additionalProperties: False` 保留，只补真实字段）。
- 隔离机制放在夹具层，后续新增 device 用例自动受益。

**Non-Goals**

- 不改 `update_device_status()` 的缓存策略（TTL、单飞锁都不动）。
- 不把 `me` 的 schema 改成宽松模式（如 `additionalProperties: True`）——那会把「响应多出未申报字段」这条护栏废掉。
- 不处理 Playwright e2e 在本机的 `EPERM mkdtemp`（环境问题，非用例缺陷）。

## Decisions

1. **用 autouse 夹具调 `reset_status_sync_cache()`，不改用例本身。**
   备选（否）：在每条用例里手工调用 —— 新增用例容易忘；或短化 TTL —— 会削弱真实性能保护。
   放 `tests/device/conftest.py` 而非 `tests/device/integration/conftest.py`：`update_device_status` 也会被 api 层用例间接触发，统一覆盖更稳。
2. **schema 补字段而不是关掉 `additionalProperties`。**
   这条护栏的价值就是「响应字段必须在用例资产里显式登记」；关掉等于放弃信号。补两个字段并加入 `required`，等于把 `me` 的契约钉死。
3. **不改生产代码。**
   两条都证明是用例侧缺陷；改生产（去缓存 / 删字段）会引入真实回归。

## Risks / Trade-offs

- [夹具在每个用例前后清缓存，掩盖「跨请求复用」这一真实行为] → 真实行为由 `tests/device/api` 的接口用例覆盖（同一请求内仍走缓存），夹具只隔离用例边界。
- [`me` 后续再加字段会再次变红] → 这正是期望：加字段必须同时更新 schema，属于契约变更的一部分。

## 模块防火墙自检

- 只动 `tests/**`，无跨 App import、无写库路径变化、无异常类与依赖方向变化。
