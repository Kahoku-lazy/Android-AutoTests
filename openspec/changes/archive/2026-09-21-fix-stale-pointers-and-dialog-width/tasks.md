## 1. 目录路径控件宽度

- [x] 1.1 `SaveToElementsDialog.vue`：删掉模板上的 `class="save-folder"`；CSS 改为 `.save-folder-field { width: 100% }` + `.save-folder-field :deep(.el-cascader), .save-page-select { width: 100% }`；验证：真机 `.el-cascader` 宽度 **218px → 394px**（= `.el-form-item__content` 宽 = 「选择页面」下拉宽），包裹层 394、内部 `input` 394、弹窗宽仍 **520px**、3 个 testid 齐备、0 pageerror
      （实施中修正：首版只写了 `:deep()` 而漏掉包裹层自身的 `width:100%`，包裹层收缩到内容宽 → 控件仍是 218px；补上包裹层宽度后达标。）
- [x] 1.2 全仓检索 `save-folder`：模板上只剩包裹层类名 `save-folder-field`（被 CSS 消费），旧 `.save-folder` 类彻底消失；验证：真机 `document.querySelector('.save-folder')` 为 `null`

## 2. 悬空文档指针

- [x] 2.1 `frontend/src/shared/styles/tokens.css` 注释：`硬性规范 §1.14` → `硬性规范 §1.7`；验证：`§1.14` 全前端命中 0、`§1.7` 命中 1
- [x] 2.2 `openspec/specs/frontend-l4-data-surface/spec.md`：移除「（`frontend/AGENTS.md` 硬性规范 §1.5）」；验证：该 spec 内 `§1.5` / `§1.14` 命中 0；规范正文其余逐字不变（仅删括号引用）

## 3. 门禁与归档

- [x] 3.1 `openspec validate fix-stale-pointers-and-dialog-width --strict`；验证：valid
- [x] 3.2 `npm run lint:styles`；验证：`LINT_EXIT=0`（含新增的 `:deep()` 规则）
- [x] 3.3 `npx vite build`；验证：退出码 0，`✓ built in 3m 51s`
- [x] 3.4 `npx vitest run tests/device-inspector`；验证：4 passed
- [x] 3.5 归档：delta 写入 `frontend-l4-data-surface`；验证：悬空引用消失、requirement 结构与场景数不变（1 requirement / 2 scenarios）
