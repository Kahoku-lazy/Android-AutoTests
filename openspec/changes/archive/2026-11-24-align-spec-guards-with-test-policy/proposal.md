# Proposal: align-spec-guards-with-test-policy

## Why

`tests/` 的测试口径在 2026-11-24 改为「功能灰盒 + 浏览器 b2b + 落库校验（并入灰盒）」，业务单元层整体迁至 `temps/tests-unit-archive/`（见 `tests/AGENTS.md`）。

但 4 个活跃规格里 6 处仍写着「该一致性 SHALL 由 `tests/graybox/unit` 下的默认单元测试断言」。这句话两头都失真：

- `tests/graybox/` 早在 2026-09 随元素定位 Web/API 两域下线就删除了，目录不存在；
- 新口径**禁止**在 `tests/` 下新增单元测试，照着规格去建 `tests/graybox/unit` 会直接违反 `tests/AGENTS.md` 红线。

规格是准入依据，留着这句话等于给 AI 和人工发了一张"再建一个单元层"的许可。

## What Changes

- 把 4 个活跃能力中 6 条需求的守护落点，从 `tests/graybox/unit` 下的默认单元测试，改为 `tests/arch/unit` 下的契约守护（零 I/O、不依赖运行中的服务，与原要求的性质一致，只是落点改到仍然存在的目录）。
- 相应场景里的「运行默认单元测试」改为「运行 `tests/arch/unit` 契约守护」。
- **不改**任何断言内容、断言数量、被测行为；只改"由谁守护"的指向。无代码变更。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `api-path-convention`：2 条需求（「前端与测试调用面遵循唯一写法」「前端调用面与路由表的一致性由默认测试守护」）的守护落点与对应场景文字。
- `auth-form-validation`：2 条需求（「表单校验文案与数值阈值在两侧一致」「密码首尾空白的归一化口径在两侧一致」）。
- `auth-response-shape`：1 条需求（「前端认证 DTO 声明后端不返回的字段」）。
- `auth-session`：1 条需求（「公开认证端点的 401 不触发令牌刷新」）。

## Impact

- **规格文本**：`openspec/specs/{api-path-convention,auth-form-validation,auth-response-shape,auth-session}/spec.md`（归档时由 delta 覆盖）。
- **代码**：无。守护实现已在 `tests/arch/unit/{test_api_path_callers,test_auth_validation_parity,test_auth_frontend_contract,test_auth_endpoint_declaration}.py`。
- **依赖 / DB**：无。
- **关联文档**：`tests/AGENTS.md`（口径正文）、`.agents/docs/tests/tests_unit_and_contract_parity.md`（契约守护范式）。
