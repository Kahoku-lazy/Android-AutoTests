## Why

三处**声明与指向的失真**（同一主题：写的东西不成立或指不到）：

1. **「目录路径」控件不生效的宽度**：`SaveToElementsDialog.vue` 的 `.save-folder { width: 100% }` 从未匹配——`.el-cascader` 根节点上没有 `data-v-*` 作用域属性（scoped 规则打不中），实测该控件宽 **218px**，与同弹窗「选择页面」下拉的 **394px** 不一致，而作者显然写的是全宽意图。
2. **`tokens.css` 的字号判定语指到了不存在的 §1.14**：`frontend/AGENTS.md` 的「硬性规范」现只有 1–7 条，字号规则是**第 7 条**。
3. **`frontend-l4-data-surface` 的表单校验要求指到了不存在的 §1.5**：同一份 AGENTS.md 里没有任何校验文案规则，该括号引用是旧版编号的残留。

## What Changes

- `SaveToElementsDialog.vue`：删掉打不中的 `.save-folder { width: 100% }`（连同模板上无人消费的 `class="save-folder"`），改为在带作用域的包裹层上用深选择器兑现原意图：`.save-folder-field :deep(.el-cascader), .save-page-select { width: 100% }`
- `frontend/src/shared/styles/tokens.css` 的注释指针：`硬性规范 §1.14` → `硬性规范 §1.7`（字号是第 7 条）
- `frontend-l4-data-surface` 的表单校验要求：删掉悬空的「（`frontend/AGENTS.md` 硬性规范 §1.5）」括号引用，规范正文不变
- **BREAKING**：无（控件由窄变全宽是**兑现既有声明意图**；规范正文一句未改）

## 明确移出本变更范围

- 不改弹窗宽度（520px）与「选择页面」下拉
- 不改 `el-cascader` 的交互、`:props` 与 `clearable`
- 不在 `frontend/AGENTS.md` 里新增条款（不发明规则；只把指针指对或删掉）
- 不做全仓其它 `AGENTS.md §x.y` 指针的普查（本次只处理实际命中的这两处）

## 关联文档

- 需求编号：`PRD-03-设备检查器`
- 被修正的引用目标：`frontend/AGENTS.md`「硬性规范」（当前 1–7 条）
- 相关归档：`2026-09-21-remove-inspector-false-signals`（该单把「永不生效的 `.save-folder`」登记为伴随发现，本单兑现结论）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `frontend-l4-data-surface`: 修改「Form validation uses Element Plus rules」，仅移除悬空的 `frontend/AGENTS.md §1.5` 引用（规范正文不变）

## Impact

- `frontend/src/modules/device-inspector/components/SaveToElementsDialog.vue`（模板 1 行 + CSS 1 行）
- `frontend/src/shared/styles/tokens.css`（注释 1 行）
- `openspec/specs/frontend-l4-data-surface/spec.md`（1 句括号引用）
- 后端 / 端点 / 迁移：零改动
- 观感变化：「目录路径」控件由 218px 变为与「选择页面」一致的全宽（394px）——**唯一可见变化**，见 design D1 的依据