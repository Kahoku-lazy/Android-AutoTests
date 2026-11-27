## Why

`tests/` 灰盒层还剩 **2 条既有失败**，两者都与业务实现无关，是用例资产自身过期/缺隔离：

| 用例 | 现象 | 根因 |
|---|---|---|
| `tests/device/integration/test_device_state_machine.py::test_update_status_protects_busy_device` | 单独跑绿、全文件跑红 | `DeviceStateMachine.update_device_status()` 有 10 秒结果缓存（`_status_sync_at` / `_status_sync_result`，用于避免高频 GET 打 ADB）；同文件前一条用例把缓存写成 `(0, 1)`，后一条 10 秒内复用拿到 `removed=1`，断言 `removed == 0` 失败。`reset_status_sync_cache()` 早就存在，但没有任何夹具调用它 |
| `tests/auth/api/test_auth_tokens.py::test_auth_tokens_authenticated[TC-ME-001 me-success]` | jsonschema 报 `additionalProperties` 校验失败 | `/api/auth/me/` 的 `user` 后来新增了 `is_operator` / `is_assistant_author` 两个布尔字段，而 `tests/api_kit/schemas.py` 的 `ME_SUCCESS_SCHEMA` 仍只登记 3 个字段且 `additionalProperties: False` |

## What Changes

- `tests/device/conftest.py`（新增）：autouse 夹具在每个 device 用例前后调用 `reset_status_sync_cache()`，把缓存隔离到单条用例内。夹具放在 `tests/device/` 而非 `integration/`，api 层用例同样受益。
- `tests/api_kit/schemas.py`：`ME_SUCCESS_SCHEMA` 补 `is_operator` / `is_assistant_author` 两个布尔字段并加入 `required`，与响应保持一致。

**不改生产代码**：两条都是用例侧资产缺陷；缓存本身是设计（避免高频 ADB 探测），`me` 的两个布尔字段是既有契约。

## 关联文档

无 PRD 条目：清测试债，不对应需求编号。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

（无 —— 响应形状与缓存行为都没变，只是用例资产跟上现状；`.openspec.yaml` 置 `skip_specs: true`）

## Impact

- **测试**：新增 `tests/device/conftest.py`；修改 `tests/api_kit/schemas.py` 一处 schema
- **生产代码**：0 行
- **接口**：不变
- **依赖与迁移**：无
