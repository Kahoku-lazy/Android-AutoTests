# SPEC — 前端模块重构规范

> 基于仪表盘（PRD-00）和设备管理（PRD-01）两次重构的经验总结。
> 目标：对其他模块（element-locator / case-manager / test-runner / report-generator / ai-assistant / workflow）应用相同逻辑时，有可复制的步骤清单。

---

## 阶段 1：基础设施统一

### 1.1 背景统一点阵纸纹

**问题**：各模块背景不一致（有的 `#d4cdc0` 点、有的 `transparent`、有的纯色）。

**修复**：全局 `style.css` 中 `.doc-page.wb-shell .doc-body` 设置：
```css
background: radial-gradient(circle, var(--app-paper-dot) 0.8px, transparent 0.8px);
background-size: 14px 14px;
background-color: var(--doodle-bg, #faf5ee);
```
一处修改，所有 `.wb-shell` 模块自动生效。

### 1.2 移除全局 max-width 限制

**问题**：`style.css` `.doc-body { max-width: 1600px; margin: 0 auto; }` 导致大屏两侧大量留白。

**修复**：从全局 `.doc-body` 删除 `max-width` 和 `margin: 0 auto`。模块如需限制宽度，自行在 scoped CSS 中添加。

### 1.3 验证规则

```
find frontend/src/modules/ -name "*.vue" | xargs grep "doc-body" | grep -v "scoped"
```
确保没有模块在全局层重复定义背景样式。

---

## 阶段 2：识别手写 UI 模式 → 提取为 Shared 组件

### 2.1 识别标准

满足以下任一条件 → 应进入 `shared/`：

| 条件 | 示例 |
|------|------|
| 被 2+ 模块手写同一 HTML 结构 | KPI 卡片在 3 个模块手写了 22 遍 |
| 被 2+ 模块跨模块 import | DeviceFilterTabs 被 test-runner 引入 |
| DESIGN_SYSTEM.md 已定义但无人用 | `patterns/ConfirmButton.vue` 已存在但 7 处手写 `ElMessageBox.confirm` |

### 2.2 提取步骤

1. **创建 shared 组件**：`shared/components/Xxx.vue` 或 `shared/components/patterns/Xxx.vue`
2. **Props 极简**：≤ 8 个 props，不含业务名词
3. **替换调用点**：逐模块 `import` 替换，旧内联 HTML + CSS 删除
4. **构建验证**：每次替换后 `vite build`

### 2.3 已完成的提取

| Shared 组件 | 替换的模块 | 替换数量 |
|------|------|:--:|
| `KpiCard.vue` | device-pool / test-runner / report-generator × 4 文件 | 22 处 |
| `FilterTabs.vue` | device-pool / test-runner | 2 处 |
| `ErrorState.vue` | dashboard | 1 处 |
| `SkeletonCard.vue` | dashboard StatsCard | 1 处 |
| `useECharts.js` | dashboard TrendBarChart + report-generator × 2 | 3 处 |

---

## 阶段 3：模块内布局重构

### 3.1 拆分为双区域

参考仪表盘和设备管理的页面结构：

```
┌─────────────────────────────────┐
│  WorkbenchHeader（共享组件）     │
├─────────────────────────────────┤
│  Section 1: 统计概览             │
│  - section 标题（手绘波浪下划线） │
│  - KPI 卡片（KpiCard × N）       │
├─────────────────────────────────┤
│  Section 2: 内容列表             │
│  - section 标题                  │
│  - 工具栏（筛选/操作/视图切换）   │
│  - 表格/卡片视图                 │
└─────────────────────────────────┘
```

### 3.2 模板结构

```html
<div class="doc-page wb-shell module-workbench">
  <WorkbenchHeader ... />

  <div class="doc-body">
    <!-- 统计概览 -->
    <section class="doc-section device-section">
      <div class="doc-section__header">
        <h3 class="doc-section__title">统计概览 <span class="doc-tag">Overview</span></h3>
        <span class="doc-section__label">简述</span>
      </div>
      <div class="kpi-row">
        <KpiCard v-for="..." />
      </div>
    </section>

    <!-- 内容列表 -->
    <section class="doc-section device-section--list">
      <div class="doc-section__header">...</div>
      <div class="device-toolbar">
        <!-- 筛选 + 操作 + 视图切换 -->
      </div>
      <!-- 表格/卡片 -->
    </section>
  </div>
</div>
```

### 3.3 标题样式（手绘波浪下划线）

```css
.doc-section__title {
  font-family: var(--app-font-display);
  font-size: var(--app-size-lg); font-weight: 700; color: var(--ink);
  display: inline-block; position: relative; margin-bottom: 4px;
}
.doc-section__title::after {
  content: '';
  position: absolute; bottom: -1px; left: 0; right: 0; height: 3px;
  background: url("data:image/svg+xml,...手绘波浪SVG...") repeat-x;
  background-size: 40px 3px;
}
```

---

## 阶段 4：KPI 卡片设计规范

### 4.1 使用 shared KpiCard

```html
<KpiCard
  :value="stats.online"
  label="在线"
  color="#6BCB77"
  shape="diamond"    <!-- diamond | triangle | square | circle -->
/>
```

### 4.2 颜色与图形约定

| 数据含义 | 推荐颜色 | 推荐图形 |
|------|------|:--:|
| 在线 / 通过 / 成功 / 正常 | `#6BCB77` 绿 | ◆ 菱形 |
| 忙碌 / 警告 / 等待中 | `#FFB5A7` 粉 / `#F7C948` 黄 | ▲ 三角 |
| 离线 / 失败 / 异常 | `#d4d8dc` 灰 / `#FFB5A7` 粉 | ■ 方块 |
| 总计 / 概览 / 综述 | `var(--ink)` 黑 / 模块主色 | ● 圆 |

### 4.3 KPI 卡片微旋转

```css
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 18px;
}
.kpi-row > :nth-child(1) { transform: rotate(-0.8deg); }
.kpi-row > :nth-child(2) { transform: rotate(0.5deg); }
.kpi-row > :nth-child(3) { transform: rotate(-0.4deg); }
.kpi-row > :nth-child(4) { transform: rotate(0.6deg); }
.kpi-row > :hover { transform: rotate(0deg) scale(1.03) !important; z-index: 5; }
```

---

## 阶段 5：模块颜色收束

### 5.1 识别跨模块颜色泄漏

每个模块应使用自己的模块主色（`--c-device`、`--c-runner` 等），不应借用其他模块的颜色。

**检查**：`grep -rn "var(--c-workflow)" modules/device-pool/` → 命中 = 泄漏

### 5.2 模块色映射

| 模块 | CSS 变量 | 色值 |
|------|------|:--:|
| dashboard | `--c-dashboard` | `#F7C948` 柠黄 |
| device-pool | `--c-device` | `#6BCB77` 薄荷绿 |
| element-locator | `--c-element` | `#A78BFA` 薰衣草紫 |
| case-manager | `--c-case` | `#4ECDC4` 青绿 |
| test-runner | `--c-runner` | `#FFB5A7` 桃粉 |
| report-generator | `--c-report` | `#7C6F83` 灰紫 |
| ai-assistant | `--c-ai` | `#E879F9` 柔粉 |
| workflow | `--c-workflow` | `#89CFF0` 天蓝 |

---

## 阶段 6：跨模块 import 消零

### 6.1 检查

```bash
grep -rn "@/modules/" modules/ --include="*.vue" --include="*.js" \
  | grep -v "modules/[^/]*/api.js\|modules/[^/]*/routes.js"
```

### 6.2 修复

跨模块引用的组件 → 迁入 `shared/components/`。双方改为从 shared 平等引用。

---

## 阶段 7：架构原则验证

### 7.1 单向依赖检查

```
组件层 (.vue)
  → 逻辑层 (composables/)
    → 数据层 (api.js)
      → 基础设施层 (shared/api-client.js)
```

箭头永远向下。检查 `index.vue` 没有 import `api.js` 以外的模块内部文件，`api.js` 没有 import composable。

### 7.2 高内聚低耦合检查

```bash
# 谁 import 了本模块？（不应有非 api.js 的引用）
grep -rn "@/modules/{name}/" modules/ --include="*.vue" --include="*.js" | grep -v "modules/{name}/"
```

---

## 阶段 8：PRD 更新

参照 PRD-00（仪表盘）和 PRD-01（设备管理）的 v5.0 格式：

1. 标题格式：`# PRD-XX — 模块中文名 (English Name)`
2. 版本行：版本号 + 日期
3. §1 功能定位：一句概括
4. §2 设计目录：完整文件树 + 每个文件职责/行数 + 架构特征
5. §3 核心功能：按页面区域逐模块展开——每个子区域写清组件名/Props/数据来源
6. §4 数据流：API → composable → 子组件分发链路
7. §5 验收汇总表
8. 附录A 测试优先级
9. 附录B 实施状态（含本次重构完成项）
10. 附录C 已知问题与改进项

---

## 执行总览

| 阶段 | 内容 | 影响范围 | 预估工时 |
|:--:|------|------|:--:|
| 1 | 背景 + max-width 统一 | 全局 style.css | 已修复 |
| 2 | 手写 UI → shared 组件 | 逐模块替换 | 已提取 5 组件 |
| 3 | 模块内双区域布局 | 单模块 scoped | 1-2h/模块 |
| 4 | KPI 卡片设计规范 | 全局 shared 组件 | 已制定 |
| 5 | 模块颜色收束 | 单模块 CSS | 0.5h/模块 |
| 6 | 跨模块 import 消零 | shared + 双模块 | 已修复 |
| 7 | 架构原则验证 | 单模块检查 | 15min/模块 |
| 8 | PRD 更新 | 文档 | 1h/模块 |
