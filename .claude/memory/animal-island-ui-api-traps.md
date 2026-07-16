---
name: animal-island-ui-api-traps
description: animal-island-vue 与 Element Plus 的 API 差异速查
metadata: 
  node_type: memory
  type: project
  originSessionId: b05814f4-5f5d-4bc7-9238-26a81baf151e
---

animal-island-vue ≠ Element Plus，禁止凭 Element Plus 经验写代码。已验证的陷阱：

| 需求 | ❌ Element Plus 思维 | ✅ animal-island-vue |
|------|---------------------|---------------------|
| 红色按钮 | `type="danger"` | `type="primary" danger`（danger 是布尔属性） |
| 红色描边按钮 | `type="danger" plain` | `danger plain` 或 `type="primary" danger plain` |
| Tabs 内容 | 自闭合 `<Tabs />` + 内容放外面 | 必须用具名 slot `#[tab.key]` 放内部 |
| Modal 确认 | `@confirm` | `@ok` |
| Modal 内用 Select | `Select` 组件 | 必须用 `el-select`（Select 下拉被 Modal clip-path 裁剪） |

写完代码后自查：
```bash
grep -rn 'type="danger"' frontend/src/modules/   # 应改为 danger 布尔属性
grep -rn '<Tabs.*/>' frontend/src/modules/        # 应为非自闭合 + slot
```

**Why:** 历史高频错误（2+ 次），每次都是 Element Plus 思维惯性导致。

**How to apply:** 使用 animal-island-vue 组件前，先查 `.claude/rules/animal-island-ui.md` API 表，再 grep 已有正确用法。详见 [[frontend-rules]]。
