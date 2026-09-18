## 1. 判罚量规回写（校准 §9：先补量规再定级）

- [x] 1.1 `.agents/skills/vue-frontend-check/references/calibration.md` §2 增补 5 类未覆盖量规：未登记色值的平行色板（交互/状态色 🟠、纯装饰 🟡）· 数据编码分类色板散落 🟡 · 圆角字面量偏离非对称令牌 🟡 · `:root` 引入模块私有变量 🟡 · 废弃令牌别名继续使用 🟡；每条写明反例出处；验证：§2 的 🟠 行含「平行色板落在语义位置上」（反例 `KnowledgeBase.vue:312` / `PageElementsPanel.vue:236`），🟡 行含四类并各带反例路径（`CaseFileSheet.vue:537-543` · `ReportDetail.vue:445` · `tokens.css` `--ai-*`/`--case-*` · `CaptureForm.vue:51`）
- [x] 1.2 同文件 §10 变更记录追加一行（2026-09-15 五类回写摘要）；验证：变更记录表首行为本轮日期

## 2. 语义色与字号收敛（清 5 条 🟠）

- [x] 2.1 `dashboard/DashboardView.style.css`：`.subhead__tag` 的 `font-size:10px` → `var(--app-size-xs)`；验证：模块内 `font-size` 字面量由 2 处降至 1 处，仅剩 `ProjectTree.vue:640` 的 18px 树图标例外
- [x] 2.2 `ai-assistant/KnowledgeBase.vue`：删除按钮 hover 的 `#e74c3c` / `#fef0ef` → `var(--app-status-danger-text)` / `var(--app-status-danger-bg)`；验证：该文件两字面量命中 0
- [x] 2.3 `device-inspector/components/PageElementsPanel.vue`：`#409eff`→`var(--c-device)`、`#a78bfa`→`var(--c-element)`、徽标文字 `#fff`→`var(--app-text-inverse)`、选中行 `rgba(167,139,250,.18)`→由 `--c-element` 派生的 `color-mix`；表头 dump/OCR 的 `<script>` 侧色值同改（`#e8f4fd`→`--app-page-active-bg`、`#f3efff`→`--app-icon-purple-bg`）；验证：模块内 `#409eff`/`#67c23a`/`#f56c6c`/`#e6a23c` 命中 **0**
- [x] 2.4 `case-manager/components/ProjectTree.vue` + `case-manager/CaseFileSheet.vue`：白底 `#fff`→`--app-bg-card`、中性 `#c0bbb0`→`--app-text-muted`、危险 `#ffe8e8`/`#e85d5d`→`--app-status-danger-bg`/`-text`、青/黄 tint 改由 `--c-case`/`--c-dashboard` 的 `color-mix` 派生；7 色测试类型标签收敛为 `CaseFileSheet.vue:515-521` 的 14 个 `--tag-*` 具名变量（色相不变），消费规则全部改引用变量；验证：`#e85d5d`/`#ffe8e8`/`#c0bbb0` 命中 0，`--tag-*` 仅在声明块出现字面量
- [x] 2.5 `report-generator/CaseBreakdown.vue` + `report-generator/ReportDetail.vue`：`#a03030`（`--app-status-danger-text` 的字面量副本）/ `#c0392b` / `#4a9a20` / `#fff0ee` → `--app-status-danger-text` / `--app-status-success-text` / `--app-status-danger-bg`；验证：`#a03030`/`#c0392b`/`#4a9a20`/`#fff0ee` 在两个文件命中 0
- [x] 2.6 全仓复核：模块内 `font-size` 字面量仅剩 18px 例外；`#409eff` 命中 0；残留字面量均有登记归类（`ScreenshotView.vue` canvas 绘制色 2 处=画布例外 · `TaskReport.vue` `var(--token,#a03030)` fallback 2 处=量规 🟡 · `device-inspector/index.vue:55` 装饰渐变 1 处 · `CaseFileSheet.vue` 表头蓝三色=表面色）；验证：复核输出记录于归档说明

## 3. 复盘落盘（设计方案文档）

- [x] 3.1 `dev_docs/05-开发与测试/设计方案与报告/设计方案-前端L0-L5骨架层级图.html` 在归属表与 footer 之间增补「复盘：主题令牌与布局对齐实测」章节（三层判定卡 · 逐层核对表 · 量化证据表 · 共享件采用率 · 5 条 🟠 收敛表 · 未收敛观察项 · 闭环计划 · 判定边界声明）；验证：新增 `sub-title` / `verdict` / `pill` / `bar` / `loop` 组件样式，章节位于 334–425 行，文件由 471 行增至 590 行，末尾层级开关脚本（`setVariant`/`applyState`）完好
- [x] 3.2 更新该文档 footer 的依据行与复核日期；验证：footer 含「2026-09-15 静态扫描实测（无浏览器核验）」与变更名 `converge-module-theme-tokens` 及 spec 路径

## 4. 门禁与归档

- [x] 4.1 `cd frontend && npm run typecheck`；验证：`TOTAL_ERRORS=34` 与基线一致（0 新增）；7 个改动文件命中的 13 条中 3 条为 `ProjectTree.vue:430-434` el-tree 既有类型错、9 条为 grep 模式误匹配 `tests/dashboard/*` 既有错误
- [x] 4.2 用 `vue-frontend-check` 过 7 个改动文件（calibration §7 强制扫描 + 新增行扫描）；验证：新增强制扫描已执行；**本变更 16 处编辑全部为「字面量 → 令牌」方向，新增行内 `var(--…)` 93 次**；唯一新增字面量是 `CaseFileSheet.vue` 的 14 个 `--tag-*` 分类色板声明（即需求要求的「集中声明一次」）；`DashboardView.style.css:121` 的 `background:#fff` 经 hunk 归属核验属本会话更早的「仪表盘章节钉板」变更，非本变更引入
- [x] 4.3 `openspec validate --strict` 通过后经 `openspec-archive-change` 归档；验证：`openspec/specs/frontend-l0-design-tokens/spec.md` 生成（1 条需求 / 5 场景），变更进入 archive
