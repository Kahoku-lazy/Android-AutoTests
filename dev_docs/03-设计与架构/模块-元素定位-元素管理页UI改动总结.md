# 元素管理页 UI 显示问题 — 改动总结

## 一、问题现象

**模块**：元素定位 → 元素管理（`ElementManager.vue`）

用户反馈分两个阶段：

| 阶段 | 现象 |
|------|------|
| 第一轮 | 筛选标签区（全部 / 可点击 / 已命名 / 测试点）显示异常，`animal-tabs__list` 宽度仅约 206px，表格数据看不全 |
| 第二轮 | 横向已正常，但纵向仍被裁切（`elements-panel` 高度约 350px），表格下方行无法看到，页面不能向下扩展 |

数据本身能加载（表头、首行 XPath 等可见），属于**纯 CSS 布局问题**，不是 API 或数据链路问题。

---

## 二、分析思路

按项目 `frontend.md` 的排查流程，走 **DOM 存在 → Computed 样式** 路径，而非先改模板：

### 1. 定位问题区域

DOM 路径显示双层嵌套结构：

```
index.vue（设备发现 / 元素管理 外层 Tabs）
  └── ElementManager.vue（内层筛选 Tabs + 表格）
        └── elements-panel → elements-subheader → element-tabs
```

布局问题出在**嵌套 Tabs + Grid 双栏**的组合，不是组件未渲染。

### 2. 对比参照实现

对照已正常工作的 `test-runner/index.vue`：
- 有完整的 flex 高度链（`doc-body` → `tabs-panel` → `animal-tabs` → `animal-tabs__content`）
- 明确区分「视口固定 + 内部滚动」vs「内容撑开 + 页面滚动」

### 3. 根因归纳（4 类）

**① CSS 选择器写错**
```css
/* 错误 */ .animal-tabs-list
/* 正确 */ .animal-tabs__list
```
`flex-shrink: 0` 等样式未生效。

**② 引用了不存在的 DOM 结构**
```css
/* 错误 */ .animal-card-body
```
`animal-island-vue` 的 `Card` 没有这层包裹，表格的 `overflow` / `padding` 控制全部失效。

**③ flex 高度链断裂**
嵌套场景缺少关键环节：
- 外层 `animal-tabs__inner` 未撑满
- 内层 `animal-tabs__inner`、`.doc-body` 未设 `min-height: 0`
- 多层 `overflow: hidden` 把高度锁死在视口内

**④ 滚动策略与用户预期不一致**
第一版采用「视口固定 + `.table-scroll` 内部滚动」，但 flex 链不完整导致内部滚动未生效，表现为纵向裁切；用户期望的是**内容随表格行数增高，区域可向下滚动**。

---

## 三、解决方案（两阶段演进）

### 阶段一：修复横向 + 建立 flex 链

**改动文件**：`ElementManager.vue`、`element-locator/index.vue`

| 修复项 | 做法 |
|--------|------|
| 选择器 | `.animal-tabs-list` → `.animal-tabs__list` |
| Card 样式 | 去掉 `.animal-card-body`，直接作用在 `.table-card` / `.pages-card` |
| flex 链 | 补全 `doc-body` → `animal-tabs__inner` → `table-scroll` |
| 外层 Tabs | `index.vue` 为 `animal-tabs__inner` 增加 flex 约束 |

横向显示在此阶段恢复正常。

### 阶段二：解决纵向裁切

**策略调整**：从「锁死视口 + 内部滚动」改为「内容自然撑高 + 外层滚动」。

**`index.vue`（外层 Tab）**
```css
.animal-tabs__content {
  overflow-y: auto;   /* 内容超出时在此滚动 */
  display: block;     /* 不再用 flex 锁高度 */
}
.animal-tabs__inner {
  min-height: min-content;  /* 随内容增高 */
}
```

**`ElementManager.vue`（内层）**
```css
/* 去掉 overflow: hidden / height: 100% 等高度锁定 */
.doc-page     → min-height: min-content
.main-layout  → align-items: start（不再拉伸裁切）
.table-scroll → overflow-x: auto（仅横向）；overflow-y: visible（纵向随内容撑开）
.pages-card   → max-height: calc(100vh - 280px)（左侧列表过长时独立滚动）
```

---

## 四、改动文件清单

| 文件 | 改动性质 |
|------|----------|
| `frontend/src/modules/element-locator/components/ElementManager.vue` | 主要：选择器修正、Card 样式、布局策略从固定视口改为内容驱动 |
| `frontend/src/modules/element-locator/index.vue` | 辅助：外层 Tab 内容区改为 `overflow-y: auto` |

`npx vite build` 已通过，无新增 linter 错误。

---

## 五、经验沉淀

1. **animal-island-vue 类名**：组件用 BEM 双下划线（`animal-tabs__list`），手写 CSS 需与源码一致。
2. **Card 无 body 层**：样式直接写在 `.table-card` 等挂载类上，不要用 `.animal-card-body`。
3. **嵌套 Tabs 要画清滚动边界**：外层管纵向滚动，内层表格只管横向；避免多层 `overflow: hidden` 叠加。
4. **先 DevTools 再改代码**：编译通过、API 正常 ≠ 渲染正常；flex 高度链问题不会被 `vite build` 捕获。
5. **滚动策略要对齐用户预期**：「内部滚动」和「页面向下扩展」是两种 UX，需在 flex 链完整的前提下明确选择，不能混用导致裁切。



## 执行引擎任务列表显示不了全部卡片问题

原因是任务列表区域用了多层 overflow: hidden，滚动又交给内部的 .card-grid，但 animal-island-vue 的 Tabs 在 animal-tabs__content 和插槽之间还有一层 animal-tabs__inner，flex 高度链在这里断了，所以 .card-grid 拿不到固定高度，13 张卡片会被直接裁切且无法滚动。

修改内容（对齐 element-locator 模块的已验证方案）：

将 animal-tabs__content 改为滚动容器（overflow-y: auto）
为 animal-tabs__inner 设置 min-height: min-content，让内容可以撑开
去掉 .card-grid 上无效的 flex: 1 和 overflow-y: auto
刷新页面后，在 Tab 内容区应能向下滚动查看全部 13 张任务卡片。若仍有问题，告诉我你的窗口宽度，我再排查窄屏下的布局