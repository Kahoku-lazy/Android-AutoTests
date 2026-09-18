## Why

批 3 的剩余项里，只有一小部分属于**真零风险**（不改行为、不改外观），其余（断点 9→3 档、侧栏 228/260 取值、6 个页面迁骨架、48 处滚动规则归一）都会改变可见行为，需先决策或视觉确认。本变更只做前者：① 清理 `.doc-page` 里被覆盖的**失效声明**（它是"读 CSS 会误判滚动归属"的根源）；② 把 `overflow-y/overflow` 滚动容器**登记成清单**，作为后续归一的输入。

## What Changes

- **删除失效声明**：`.doc-page` 的 `height:100%` 与 `overflow-y:auto`（被 `App.vue` 的 `.main-content :deep(.doc-page)` 覆盖，权重更高）→ 改为注释说明"定高与滚动由外壳 `.main-content` 承担"
  - 等价性：所有 13 处 `.doc-page` 都是 `.main-content` 内的页面根，覆盖恒成立，故**视觉零变化**
- **新增滚动容器审计**：`temps/scroll-audit.mjs`（postcss 解析，只读）+ 产出 `temps/scroll-containers.md` 清单（49 条规则：是否配 `min-height:0`、是否在骨架内、是否用 `overflow` 简写）
- **不做的部分（明确边界）**：不改任何仍生效的滚动声明、不动模板、不动断点取值

## 关联文档

- 无 PRD/ARCH；设计系统批 3 的"零风险分支"，承接 `2026-09-11-layout-tokens-and-explicit-scroll-strategy`

## Capabilities

（无 / 无）→ `skip_specs: true`

## Impact

- 改动 1 个源文件（`style.css`：1 条规则、2 个失效声明）+ 1 个临时审计脚本与清单（`temps/`，不入库）
- 验证：postcss **95 块 / 0 错误** · Vite dev server `style.css` **200** 且含 `doc-page--fixed` · `vue-tsc` **35 条既有错误不变** · 字号门禁通过
- **审计结论（后续归一的工作输入）**：滚动规则 **49 条** → 其中**未配 `min-height:0` 21 条**（flex 链上有潜在裁切风险）、**骨架内 10 条**、**`overflow` 简写 11 条**；集中在 ai-assistant（SkillViewerPage 3 / TaskDetailPage 3 / index.style 2）、style.css 3、case-manager CaseFileSheet 2、device-inspector 2、device-pool 2、report-generator 2
- 登记待决（均会改行为/外观，需你确认）：断点 9 个值 → 3 档；侧栏 `--side-w` 228 vs JS 默认 260；6 个无骨架页面（case-manager / element-locator）是否迁移；48 条滚动规则是否抽 `.doc-scroll` 原语（需动模板）
