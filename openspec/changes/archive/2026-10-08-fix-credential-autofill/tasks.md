## 1. 加提示属性（4 个前端文件）

- [x] 1.1 `frontend/src/modules/ai-assistant/components/ModelConfigField.vue`：API Key 的 `el-input` 加 `autocomplete="new-password"`（该字段所在的 Element Plus 表单是真正的 `<form>`，且其上方紧邻"模型名"下拉的文本输入，构成浏览器的"用户名+密码"判定）。验证：新增用例断言该输入框收到的 `autocomplete` 为 `new-password`。**验证结果**：`tests/ai-assistant/p0/model-config-field.spec.ts` 断言 `input[type="password"]` 的 `autocomplete` 为 `new-password` → 通过（并附注释说明该判定的由来）。
- [x] 1.2 `frontend/src/views/components/LoginCard.vue`：账号 `el-input` 加 `autocomplete="username"`、密码 `el-input` 加 `autocomplete="current-password"`。验证：`tests/login/p0/LoginCard.spec.ts` 扩展断言（输入框桩透传该属性）。**验证结果**：桩已透传 `autocomplete`；新增用例断言 `input[autocomplete="username"]` 与 `input[autocomplete="current-password"]` 各存在一个 → 通过（该文件 6 项全绿）。
- [x] 1.3 `frontend/src/views/components/RegisterCard.vue`：邮箱 `el-input` 加 `autocomplete="email"`、两个密码 `el-input` 各加 `autocomplete="new-password"`。验证：`tests/login/p0/RegisterCard.spec.ts` 扩展断言。**验证结果**：新增用例断言 `input[autocomplete="email"]` 存在、`input[autocomplete="new-password"]` **恰好两个** → 通过（该文件 5 项全绿）。
- [x] 1.4 核对：全前端不再存在"密码框但无 autocomplete 声明"的输入（`grep type="password"` 的每一处都有对应声明）。验证：grep 结果逐处对照通过。**验证结果**：全 `frontend/src` 的 3 处 `type="password"`（配置页 1、登录页 1、注册页 2 个中的 2 处）逐处对照 —— 配置页 → `new-password`、登录页 → `current-password`、注册页两个 → `new-password`，无遗漏；另注册页邮箱补 `email`、登录页账号补 `username`。

## 2. 用例（钉住属性传递）

- [x] 2.1 新增/扩展用例：模型配置区块的 API Key 输入收到 `autocomplete="new-password"`（输入框桩需透传该属性）。验证：该用例通过；把属性删掉即红。**验证结果**：新增 `tests/ai-assistant/p0/model-config-field.spec.ts`（2 项）：① API Key 的 `autocomplete` 断言；② 需要图片的角色选中纯文本模型时提示升级为告警样式、多模态模型不告警、不需要图片的角色不渲染该提示（顺带把上一单的界面行为补上了 DOM 级覆盖）。桩会渲染真实 `autocomplete` 值，删属性即失配。
- [x] 2.2 扩展认证用例：登录页账号/密码、注册页邮箱/密码/确认密码的属性断言。验证：`npx vitest run tests/login/p0/LoginCard.spec.ts tests/login/p0/RegisterCard.spec.ts` 全绿（按文件跑，不发起全量前端测试）。**验证结果**：连同模型配置与该能力判定用例共 **4 个文件 15 项全绿**（2.04s）。

## 3. 验证与归档

- [x] 3.1 前端门禁（按文件范围）：`npx prettier --check` 改动文件、`npx eslint` 改动文件、`npm run typecheck`。验证：全部通过。**验证结果**：prettier → All matched files use Prettier code style；eslint → 零告警；`npm run typecheck`（vue-tsc --noEmit）→ 无错误。
- [x] 3.2 相关用例最小集：本次新增/扩展的用例文件 + `tests/ai-assistant/p0/model-capability.spec.ts`（同区块的既有用例）。验证：全部通过。**验证结果**：4 文件 15 项全绿（含 `model-capability.spec.ts` 2 项）。
- [x] 3.3 浏览器复核（**必须由使用者肉眼确认**）：打开智能体配置页 → 在模型配置区块点选模型名 → 确认**不再弹出**用户名/密码的保存或填充提示；登录页与注册页的密码框填充/保存行为正常。验证：使用者确认；因浏览器原生 UI 自动化读不到，本条不做自动化断言（见 design.md D4）。**验证结果**：**待使用者确认**（自动化已钉住"组件把正确提示属性交给输入框"，且该属性在 Element Plus 中会落到原生 `input`；但"浏览器是否还弹凭据提示"属浏览器原生 UI，自动化读不到，故不作虚假断言）。若复核后仍有残留提示，按 design.md D1 的备选（不用密码框类型 + CSS 掩码）另立一单。
- [x] 3.4 关单与归档：汇总改动清单与用例结果；`openspec validate` 通过后归档（`skip_specs: true`）。验证：`openspec validate "2026-10-08-fix-credential-autofill"` 通过并完成归档。**验证结果**：改动清单 = 3 个源文件（配置页 / 登录页 / 注册页）+ 3 个用例文件（新增 1、扩展 2）；`openspec validate --strict` 通过；已归档。
