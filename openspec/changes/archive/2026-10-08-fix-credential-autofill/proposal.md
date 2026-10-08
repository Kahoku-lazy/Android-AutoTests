# 修复：模型配置页被浏览器误判为登录表单（凭据提示/填充）

## Why

在智能体配置页的模型配置区块里，选完模型名后浏览器会弹出「保存用户名与密码」或自动填充凭据——把一个**填 API Key 的配置表单**当成了登录表单。这不是 DeepSeek 相关，也不是配置页功能缺陷，而是浏览器密码管理器的启发式判定：

1. 该区块用 Element Plus 表单组件，渲染出来是一个**真正的 `<form>` 元素**（已核实：`el-form` 的模板就是 `createElementBlock("form", …)`）；
2. 表单内是紧挨着的「文本输入框 + 密码框」：上面"模型名"下拉（下拉内部本身是一个文本输入框），下面 `API Key`（`type="password"`）。浏览器据此判定为「用户名 + 密码」；
3. **API Key 字段当前的 DOM 已经是 `autocomplete="off"`**——因为 Element Plus 的输入框把 `autocomplete` 声明为属性且默认值就是 `off`；但 **Chrome 早已忽略密码字段上的 `off`**，所以挡不住。

于是"和这对输入框的第一个交互"（点选模型名）就是触发条件，与用户的观察一致。

同时发现登录页与注册页的密码/账号输入**没有任何 `autocomplete` 声明**（全前端 `src/` 零命中），密码管理器在那两页的填充与保存行为同样不规范（可能填错，或该提示保存时不提示）。

## What Changes

- 模型配置区块的 **API Key 字段**标记为 `autocomplete="new-password"`（告诉浏览器这是新的凭据，别把它当登录密码填充/保存）。
- **登录页**：账号输入标记 `username`、密码输入标记 `current-password`。
- **注册页**：邮箱标记 `email`、两个密码输入标记 `new-password`。
- 新增/扩展前端用例，把上述标记钉在组件与输入框之间（防止被后续改动静默移除）。
- 不改任何平台自身行为：校验规则、提交逻辑、接口契约、字段形状一律不动。

## 关联文档

- 受影响能力：无（表单对浏览器的提示属性属实现细节，平台承诺的行为不变）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。本单只改「组件往输入框传什么浏览器提示属性」：平台的表单校验、提交与接口契约零变化，浏览器密码管理器属外部工具行为，不构成本平台的行为契约，故按 schema 约定在 `.openspec.yaml` 设 `skip_specs: true`。

## Impact

- 前端（4 个文件）：`modules/ai-assistant/components/ModelConfigField.vue`（API Key）、`views/components/LoginCard.vue`（账号 / 密码）、`views/components/RegisterCard.vue`（邮箱 / 两个密码）。
- 测试：`tests/login/p0/LoginCard.spec.ts`、`tests/login/p0/RegisterCard.spec.ts` 的输入框桩需透传该属性并加断言；模型配置区块新增一条用例。
- 后端 / 引擎 / 数据库 / 通道：零改动。
- **验证口径说明**：浏览器的"是否弹凭据提示"是**浏览器原生 UI，自动化无法断言**；自动化只能钉住"组件确实把正确的提示属性交给了输入框"（再由 Element Plus 的声明式属性落到原生 input 上，此点已核实其属性定义与默认值）。最终确认由使用者在浏览器里肉眼复核。
