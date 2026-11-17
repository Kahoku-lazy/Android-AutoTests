# 设计：操作带与内容之间的分区虚线

## Context

`ProjectList.vue` 的 `.doc-body` 是纵向 flex（`gap` 由页面骨架给），首个子节点是 `.project-toolbar`（右对齐的「新建项目」，`margin-bottom: 16px`），其后是 `EmptyState` 或 `.project-grid`。两者之间没有分隔，视觉上连成一片。

doodle-craft 的线型规则里，虚线只允许出现在白名单组件上，其中就有 **`SectionDivider`**——「两段并列内容之间的一条 `1.5px dashed` 浅墨横线，只做分区；外边距由使用方给，组件不预设」。

## Goals / Non-Goals

**Goals**：用一条已登记的分区虚线把「动作带」与「内容」分开；间距读起来是「贴着上面、离开下面」。

**Non-Goals**：不改卡片（SketchCard 的虚线边框是它自己的皮肤）、不改按钮、不改空态文案、不在页面里就地写 `dashed`。

## Decisions

### D1 用共享件，不手写虚线

```vue
<SectionDivider class="project-divider" />
```

`SectionDivider` 内部就是 `border-top: 1.5px dashed color-mix(in srgb, var(--ink) 38%, transparent)`，与 `tests/check-dashed-whitelist.mjs` 的 OWNERS 一一对应；在页面里手写同款虚线会被门禁判违规。

### D2 间距给在上、下两侧，方向不对称

```css
.project-toolbar { margin-bottom: var(--app-space-sm); }  /* 8px */
.project-divider { margin-bottom: var(--app-space-md); }  /* 16px */
```

`SectionDivider` 自身不带外边距（组件约束），所以距离全由使用方给。上 8 / 下 16 让分隔线属于「上面的操作带」，而不是飘在中间平分。

### D3 空态时同样分隔

虚线插在 `EmptyState` 与网格之外（两者互斥渲染），所以「没有项目」时也有一条线把动作与空态分开，版式在有无数据之间保持一致。

## Risks / Trade-offs

- [页面里多一条线]：只在项目列表页出现，且是浅墨 38%，不参与层级竞争。
- [`.doc-body` 自身的 `gap` 会叠加外边距]：实测按钮→虚线 24px、虚线→卡片 32px，方向正确，不必强行压平。

## Migration Plan

纯模板 + 样式。回退 = 删掉 `SectionDivider` 节点、import 与两条样式。

## Open Questions

无。
