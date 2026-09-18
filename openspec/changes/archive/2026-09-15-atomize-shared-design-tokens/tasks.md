## 1. 原子词表落地（T0）

- [x] 1.1 逐条复核并冻结颜色原子表（`temps/atom-mapping-colors.md`，198 个唯一色值），确认命名无歧义、序号兜底条目可接受；验证：脚本比对该表覆盖集合与主 token 内字面量色值集合完全一致（差集为空）
- [x] 1.2 在 `tokens.css` 的 `:root` 新增 T0 颜色原子（按色相分组 + 注释），**不改动任何旧声明**；验证：`cd frontend && npx vue-tsc --noEmit` 无新增错误（基线 34 条 tests / 应用代码 0）
- [x] 1.3 新增 T0 排版与基础量原子（`--font*` / `--font-size-*` / `--space-*` / `--radius-*` / `--shadow-*` / `--duration-*` / `--ease` / `--size-*`），值取自现有 `--app-*` 规格；验证：新增原子数与设计表一致，且不与既有名冲突（脚本查重名）
- [x] 1.4 新增 T0 通用组件档 `--comp-<组件>-<场景>`，覆盖 shared 组件现有组件级载体（`--paper-mark-*` / `--mascot-*` / `--kpi-*` / `--ss-type-*` / `--avatar-shadow` 等）；验证：`shared/components/**` 的载体声明值 MUST 全部为 `var(--color-*)` 或 `var(--comp-*)`

## 2. 别名化与同值去重

- [x] 2.1 将 `tokens.css` `:root` 内旧名（`--c-*` / `--app-status-*` / `--app-pass|fail|pending*` / `--app-bg-*` / 杂项）的值改为 `var(原子)` 并加 `/* alias -> var(--color-…) */` 注释；验证：脚本做「别名解析值 == 原字面量值」全等校验，全量通过且视觉零变化
- [x] 2.2 将 `.ai-workbench`（42 条）与 `.case-workbench`（2 条）内的字面量改为 `var(原子)`，**作用域选择器不变**；验证：值等价校验通过 + 两个作用域块的选择器与行数不变
- [x] 2.3 将 35 条 `--el-*` 覆盖的值改为 `var(原子)`（含 `--el-color-primary-light-3` 等同色系档位）；验证：`tokens.css` 内 `--el-*` 声明的字面量命中 = 0
- [x] 2.4 消除同值重复 34 组（`temps/atom-dup-groups.md`，最大为 `#fff`×8 / `#999`×5 / `rgba(137,207,240,0.16)`×4）；验证：脚本输出同值重复组 = 0（门禁 G1 通过）

## 3. 门禁落地

- [x] 3.1 在 `frontend/tests/check-style-gates.mjs` 新增 G1（主 token 同值重复 = 0）· G5（原子名 MUST NOT 匹配 `/^--(ai|case|rg|di|wf|views)-/`）· 引用存在性（`var(--color-*)` 与 `var(--comp-*)` 必须在 T0 有声明）；验证：`cd frontend && npm run lint:styles`（= `node tests/check-style-gates.mjs`，package.json:14）在注入反例（重复值 / 模块前缀 / 悬空引用）时 MUST 非 0 退出，正常时 MUST 为 0
- [x] 3.2 输出遗留场景名别名的存量清单（`--app-*` 中场景名计数只降不增），供变更 B 归位；验证：清单计数记录在变更文档，重复运行结果稳定

## 4. 回归、文档与关单

- [x] 4.1 全仓裸值复核（`temps/verify-colors.ps1`：CSS 侧未登记 hex/rgba 与声明载体计数）；验证：`hex_bare = 0` · `rgba_bare = 0`，载体行数与基线（357 行）一致
- [x] 4.2 前端类型检查与基线比对；验证：`cd frontend && npx vue-tsc --noEmit` 输出 34 条错误且全在 `tests/`，应用代码 0（构建门禁 `npm run build` 在当前沙箱受 `spawn EPERM` 限制，若不可用则在关单记录中注明并保留静态核验证据）
- [x] 4.3 同步口径文档：`frontend/AGENTS.md` L0 §②/§④.3 与 skill `doodle-craft`（T0 四档 + 命名规则 + G1/G5 门禁）；验证：文档描述与 `openspec/specs/frontend-l0-design-tokens/spec.md` 一致（人工逐条核对）
- [x] 4.4 关单：`openspec validate atomize-shared-design-tokens --strict` 通过、tasks 全勾、`openspec archive atomize-shared-design-tokens` 存档；验证：命令输出 valid 且归档目录生成

## 关单记录（2026-09-15）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 零视觉变化（值等价） | `node temps/atomize-tokens.mjs` | 158 条旧声明逐一比对：VALUE-MISMATCH=0（4 条仅 hex 拼写不同、规范化后等价） |
| T0 门禁 | `cd frontend && npm run lint:styles` | exit 0：声明 438 条 · 颜色原子 198 · 复合值登记 3 · 引用完整 |
| 裸值复核 | `temps/verify-colors.ps1` | hex_bare=0 · rgba_bare=0 · decl_lines=630 |
| 类型检查 | 同上脚本内 `vue-tsc --noEmit` | TOTAL_ERRORS=34（全在 tests/）· APP_CODE_ERRORS=0（与基线一致） |
| 构建 | `npm run build` | **未执行**：沙箱 `spawn EPERM`（环境限制，非变更问题）；已用值等价校验 + 类型检查替代，浏览器核验仍未做 |
