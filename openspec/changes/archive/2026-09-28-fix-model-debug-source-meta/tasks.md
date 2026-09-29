## 1. 来源定义承载副标题文案

- [x] 1.1 `frontend/src/modules/ai-assistant/helpers/toolbox-assembly.ts`：`AssemblySourceDef` 增加可选字段 `meta`（注释写明「无总闸来源必填」）；为 prompt / port / debug 三个无总闸来源各声明 `meta`，字面值与现状一致（prompt `规划 / 执行 / 验收 · 始终交给助手`、port `监听开关 · 原始日志 · 不交给助手`），debug 为 `规划 / 执行 / 验收 · 仅调试不交给助手`。验证：既有 `npx vitest run tests/ai-assistant/p0/toolbox-assembly-port-source.spec.ts` 仍通过（port 文案断言未变）。
- [x] 1.2 `frontend/src/modules/ai-assistant/composables/useToolboxAssembly.ts`：`sourceMeta` 改为「无总闸且有 `meta` → 直接返回 `meta`；否则维持现有总闸关闭文案与 `n/m 生效` 计数」，删除 prompt / port 的 key 特判。验证：`npx vitest run tests/ai-assistant/p0` 全绿，且 `sourceMeta(sourceDef('debug'))` 不再出现 `/` 形态计数。

## 2. 用例对齐

- [x] 2.1 新增 `frontend/tests/ai-assistant/p0/toolbox-assembly-debug-source.spec.ts`，按既有 port 用例形态断言：debug 来源存在且 `gateKey` 为空、不进 `gatedSources()` 与生效芯片、`sourceMeta` 恰为说明性文案且不含 `n/m` 计数、文案不得等于任何 Skill 目录数量拼出的字符串。验证：`npx vitest run tests/ai-assistant/p0/toolbox-assembly-debug-source.spec.ts` 通过（4 项）。
- [x] 2.2 扩展现有 port 用例，补一条「无总闸来源的副标题一律不含计数」的公共断言（对 prompt / port / debug 三个来源生效），防止后续新增来源重演。验证：`npx vitest run tests/ai-assistant/p0` 全绿。

## 3. 收口

- [x] 3.1 前端门禁：`frontend` 下 `npx prettier --check` 涉及本变更的文件、`npx eslint src/modules/ai-assistant` 无新增 error、`npx vue-tsc --noEmit` 通过。验证：三条命令退出码为 0。验证结果：改动文件 prettier 全通过（仓库既有 `helpers/task-detail.ts` 为本次无关的存量告警）；eslint 10 warning / 0 error（全为存量）；`vue-tsc --noEmit` 无输出、退出码 0。相关用例合计 14 项全绿（port 4 + debug 4 + prompts 2 + useToolbox 3 + ToolboxPanel 1）。
- [ ] 3.2 页面验收（用户侧）：刷新 AI 工具箱，左侧「工具来源」中「模型调试」一行副标题显示 `规划 / 执行 / 验收 · 仅调试不交给助手`，页面上不再出现「0/5 生效」。验证：用户目视确认。
