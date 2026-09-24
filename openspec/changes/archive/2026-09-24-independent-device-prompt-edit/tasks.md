## 1. 常量与 composable 改造

- [x] 1.1 把 `PROMPT_ROLES` 与 `Role` 联合类型收敛到 `constants.ts`，`ToolboxPanel.vue` 与 `DevicePromptHistoryDrawer.vue` 改为引用；验证：`npx vue-tsc --noEmit` 通过，且全仓检索 `PROMPT_ROLES` 定义只剩一处（`constants.ts:72`）
- [x] 1.2 `useDevicePrompts` 的编辑态改为按角色（`editingRoles` / `isEditing(role)` / `startEdit(role)` / `cancelEdit(role)` / `save(role)`），保存与自动保存按「已保存值为基底 + 只覆盖编辑中且有改动的份」合并提交；验证：`npx vitest run tests/ai-assistant/p0/` 16 个文件 106 用例全绿
- [x] 1.3 实现中修正 D3/D4 的一处口径并同步规划件：点某份「取消」只处理该份（不把另一份仍在编辑中的草稿写库），切换来源 / 离开页面才合并所有「编辑中且有改动」的份；验证：`openspec validate` 通过 + 对应用例覆盖

## 2. 组件拆分与入口调整

- [x] 2.1 新增 `DevicePromptPanel.vue` 与 `DevicePromptPanel.style.css`：三份各自的「编辑 / 保存 / 取消」、按角色展开折叠项、页头唯一的「查看历史记录」与历史抽屉，组件自持 `useDevicePrompts` 并在卸载时自动保存；验证：`python tools/gen_arch_stats.py --check-frontend` 未把新组件计入超标（121 行）
- [x] 2.2 `ToolboxPanel.vue` 删除提示词区块、相关样式引用、`watch(activeSource)` 与 `onBeforeUnmount` 自动保存，改为按来源渲染新组件（父级 `.tb-cat-head` 对提示词来源不再渲染）；验证：`ToolboxPanel.vue` 由 499 行回落到 378 行，未出现在体积超标的门禁清单里

## 3. 测试

- [x] 3.1 更新 `frontend/tests/ai-assistant/p0/useDevicePrompts.spec.ts` 覆盖新行为：保存一份时另两份取已保存值、取消一份不影响另一份编辑态与草稿、自动保存只覆盖编辑中且有改动的份、无改动退出不写库；验证：该文件 11 个用例全绿
- [x] 3.2 新增设备提示词区交互用例并清理旧 mock：点某一份的「编辑」只有该份出现输入框、其余保持只读渲染、历史记录入口只出现一处；同时删除 `ToolboxPanel-tool-debug.spec.ts` 中已不再被父级引用的 `useDevicePrompts` mock 段；验证：`npx vitest run tests/ai-assistant/p0/` 全绿

## 4. 收口

- [x] 4.1 改动范围静态检查：改动文件 `npx prettier --check`（`src/` 侧全过；`tests/` 侧本仓既有用例一律不在 prettier 门禁范围内）、`npx eslint`（0 error，12 条 warning 全在未改动文件）、`npx vue-tsc --noEmit`（0 error）、`npm run lint:styles`（四批全过）
- [x] 4.2 三条行为以自动化用例覆盖（未做真实浏览器点击）：①「点某一份的编辑只有该份变成输入框」；②「保存一份时另两份取已保存值，不带入另一份未保存的草稿」；③「离开来源（组件卸载）时有改动的份自动落库（archive=auto）」。浏览器人工走查可选，未执行
- [x] 4.3 关单前按 `apps/AGENTS.md` 与根 `AGENTS.md` 的测试范围收敛口径向用户申请跑仓库门禁 `python run.py check`：用户选择不跑（方案 B），以相关单测 + 类型检查 + 样式门禁收口，全量门禁未执行
