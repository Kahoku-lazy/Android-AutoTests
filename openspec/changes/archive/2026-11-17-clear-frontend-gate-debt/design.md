## Context

见 `proposal.md` 的 Why。两个超标文件的性质不同：

- `chat.vue`：244 行是 `<style scoped>`（对话页气泡、输入框、日志卡占位），拆出去零风险。
- `model-configs.vue`：311 行脚本里「模型名称草稿行」自成一块（行增删、单值/多值切换、发现模型、地址校验、切类型收行），但它和抽屉表单共享一个 `form` ref，抽走要靠组合式。

## Goals / Non-Goals

**Goals:**

- 两个文件回到 500 行以内，且给 prettier 格式化留出余量（格式化平均 +8%）。
- 抽屉交互、保存语义、类型切换后的收行行为一字不变。

**Non-Goals:**

- 不动 `model-configs.vue` 的表格、分页、删除确认。
- 不把 `chat.vue` 拆成子组件（它没超那么多，拆组件会牵动对话轮询状态）。
- 不新增或删除白名单条目。
- 不改 `tokens.css` 的令牌值（只接受 prettier 的换行）。

## Decisions

1. **样式一律外置成 `*.style.css`。** 与模块内既有写法一致（`ops-console/index.vue` 已经用 `<style src="./index.style.css" scoped>`）。备选是把样式留在 `.vue` 里只抽逻辑：`chat.vue` 抽不出足够逻辑。
2. **名称草稿行抽成组合式 `useModelNameDraft(form)`，并在页面里按原名字解构。** 这样模板（`nameRows` / `loadingNames` / `discoverHint` / `singleModelName` / `addNameRow` / `removeNameRow` / `loadNames`）与 `save()` 的调用点零改动，回归面只剩「组合式内部实现」。备选是把抽屉整块拆成子组件：props/emits 十几个，且会把 `form` 的深层 v-model 变成事件转发，风险更大。
3. **切类型收行的 watch 跟着逻辑一起搬进组合式。** 页面只保留「切类型归一厂商」的 watch；两个 watch 同源互不干扰，各自职责单一。
4. **格式化只跑 prettier，不跑 `--write` 之外的自动修复（如 eslint --fix）。** 一次变更只做一件事，避免把 lint 修复混进格式提交。
5. **格式化的取舍**：`tokens.css` 与 `sketched-kit.css` 也在被格式化的范围内——它们是手写对齐的 CSS，重排会产生较大 diff，但令牌值不变、风格的唯一真相源不变。

## 模块防火墙自检

- 只改 `frontend/src/**` 与格式化 `frontend/tests/**`，不动后端、不动 `engines/`。
- 新增组合式与样式文件都在各自模块内，不跨模块引用。
- 没有把 `ops-console` 的私有逻辑挪进 `shared/`。

## Risks / Trade-offs

- [格式化后行号漂移，文档里的 `file:line` 引用失效] → 接受；文档改动不在本次范围，proposal 已记为已知影响。
- [组合式抽取若漏掉某个响应式依赖，抽屉行为会漂] → 由 `tests/ops-console`（31 条，覆盖类型/厂商联动、多模型名称、发现模型）兜底；失败即回退该抽取。
- [大范围格式 diff 掩盖真实改动] → 提交时按「格式」与「拆分」分开说明，review 时先看 `.vue` 行数与 `useModelNameDraft.ts`。

## Migration Plan

1. 先拆 `chat.vue` 样式 → `tests/ai-assistant` 全绿。
2. 再抽 `useModelNameDraft.ts` 并改编 `model-configs.vue` → `tests/ops-console` 全绿 + `vue-tsc` 通过。
3. 再外置 `model-configs.style.css` → `--check-frontend` 通过。
4. 最后跑 prettier 全量 → `prettier` / `prettier-ts` 转绿，再跑一次 `python run.py check`。

回退：三步都是文件级改动，无数据迁移；按步骤反向还原即可。

## Open Questions

无。
