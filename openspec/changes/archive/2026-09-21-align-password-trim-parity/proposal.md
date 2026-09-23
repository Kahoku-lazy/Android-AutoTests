## Why

登录密码的首尾空白由谁去掉，本仓三处说法互相矛盾：PRD 数据表单写「密码不做去空白」，`useAuthFlow.ts` 的注释声称「登录密码不 trim（与 LoginSerializer / authenticate 一致）」，而实际行为是 DRF `CharField` 默认 `trim_whitespace=True`，会在字段校验阶段去掉首尾空白 —— 与注册侧显式 `strip()` 同口径。矛盾在 2026-09-20 的 `close-auth-api-test-gaps` 里以 TC-LOGIN-016（密码前后带空格 → 200）按实测行为定格，但 PRD 该行与那条注释都没同步，于是后来者读到的仍是"没人 trim"。

更要紧的是：**"两侧归一化口径一致"这条契约目前没有任何零依赖测试守护** —— 它只写在需要活体后端的接口用例里（TC-LOGIN-016 / TC-REG-021 / TC-REG-022），改注释、改字段选项、或把注册侧的 `strip()` 删掉，默认单元测试都不会失败。而两侧口径一旦不一致，用户会在"注册时能填、登录时登不上"之间撞墙。

本次把口径钉进规格并加上守护，同时把那条误导注释改对。**不改变任何运行时行为。**

## What Changes

- **PRD 口径落地**（已在立单前按用户裁定完成）：登录 §数据表单 的密码行由「只要求非空 · 密码不做去空白」改为「只要求非空 · 首尾空白由接口去掉（与注册同口径）」。这正是 `close-auth-api-test-gaps` 声明的「口径修正」中缺失的那一半。
- **修正误导注释**：`useAuthFlow.ts` 里「登录密码不 trim（与 LoginSerializer / authenticate 一致）」的括号内容与事实相反 —— 前端确实不 trim，但后端会 trim，方向刚好相反。改为陈述真实分工：前端不 trim，去空白由接口统一负责，与注册侧归一化口径一致。
- **新增规格要求**（`auth-form-validation`）：密码的首尾空白在前后端**最终都被去掉**，两侧归一化口径 MUST 一致；并显式声明账号的口径**有意不同**（登录按原样核对、注册去空白）及其理由，防止将来有人把这条不对称"顺手修平"。
- **新增守护**：该不变量 SHALL 由 `tests/graybox/unit` 下不依赖运行中服务的用例断言，使口径漂移表现为测试失败。

**明确不在范围**：

- **不改运行时行为** —— `apps/accounts/serializers.py` 的字段选项与 `validate()` 的 `strip()`、TC-LOGIN-016 的 200 期望、PRD 的 §出口（第 39 行，「密码不做任何修剪」讲的是前端出口，仍然成立）与注册 §出口（第 137 行）全部保持现状。
- **不引入登录限流** —— 已作为已知缺口单独登记在 PRD 附录，不在本次处理。
- **不修 `formatApiError` / `_first_error` 等审查中发现的其它问题** —— 各自独立，不与本口径纠缠。

## 关联文档

- PRD-00 登录模块：登录 §数据表单（密码行）、登录 §出口、注册 §出口、登录 §校验（6 条提示）。
- 接口用例编号：TC-LOGIN-015（账号前后带空格 → 401）、TC-LOGIN-016（密码前后带空格 → 200）、TC-REG-021 / TC-REG-022（注册账号、邮箱 strip）。
- 上游裁定：变更 `close-auth-api-test-gaps` 的「口径修正（已与用户确认）」段。
- 规格真相源：`auth-form-validation`（本次修改）；`auth-registration`、`auth-response-shape`（只读参照）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `auth-form-validation`: 新增「密码首尾空白的归一化口径在两侧一致」要求，并显式声明账号空白口径两侧有意不同及其理由；该一致性 SHALL 由默认单元测试守护。现有「文案与数值阈值一致」要求不变。

## Impact

- 前端：`frontend/src/views/composables/useAuthFlow.ts` —— 仅改注释，零逻辑改动。
- 后端：**零改动** —— `apps/accounts/serializers.py` 保持 `password` 走 DRF 默认 `trim_whitespace=True`、`username` 走 `trim_whitespace=False`、注册侧四字段 `strip()`。
- 灰盒单元测试：`tests/graybox/unit/test_auth_validation_parity.py` 扩展一条空白归一化口径对拍（零外部依赖，留在默认套件内）。
- 接口用例与端到端：**零改动**（TC-LOGIN-016 现状即正确）。
- 规格：`openspec/specs/auth-form-validation`。
- 文档：PRD-00 登录模块（§数据表单 密码行已在立单前更新）。
