## Why

平台前端已有 L0 令牌体系（`shared/styles/tokens.css` 七个皮肤维度 + Element Plus 变量映射）与 L0–L5 六层骨架，但实测模块侧仍在令牌之外漂着一块**平行色板**：模块内 250 处字面量色值中 **123 处（49%）用的是 tokens.css 未登记的色值**，另有 1 处 10px 文本字号（低于 12px 下限）、1 处 Element Plus 默认蓝被当作模块色、94 处 `@deprecated` 旧色别名仍在服役。同一份代码换个人评审会给出不同严重度，因为**量规里根本没有「平行色板 / 圆角字面量 / 分类色板」这几类**。

## What Changes

**① 量规回写（校准 §9：先补量规，再定级）**

- 在 `vue-frontend-check/references/calibration.md` §2 增补 5 类此前未覆盖的判罚类目（未登记色值的平行色板 / 数据编码分类色板散落 / 圆角字面量偏离非对称令牌 / `:root` 引入模块私有变量 / 废弃令牌别名继续使用），并在 §10 变更记录登记反例出处
- 依据：校准 §9 明写「§2 无对应类别 → 暂停定级；先补一行再定级」，本轮实测有四类偏差因量规缺类而无法定级

**② 语义色与字号收敛（清掉 5 条 🟠）**

- `dashboard/DashboardView.style.css`：`.subhead__tag` 的 `font-size:10px` → `var(--app-size-xs)`（<12px 一律 🟠，禁止降级）
- `ai-assistant/KnowledgeBase.vue`：删除按钮 hover 的 `#e74c3c`/`#fef0ef` → `--app-status-danger-text`/`--app-status-danger-bg`
- `device-inspector/components/PageElementsPanel.vue`：`#409eff`（EP 默认蓝）→ `--c-device`；`#a78bfa` → `--c-element`；`#fff` → `--app-text-inverse`；选中行 `rgba(167,139,250,.18)` → `color-mix(` 该模块色 `)`
- `case-manager`（`ProjectTree.vue` + `CaseFileSheet.vue`）：危险 / 中性 / 白底 / 强调文字等**语义字面量**改用 `--app-status-*` / `--app-bg-card` / `--app-text-*`；**7 色测试类型标签属于数据编码分类色板**，不改色相，改为在该文件内使用具名局部自定义属性集中声明一次（消除散落魔法值）
- `report-generator`（`CaseBreakdown.vue` + `ReportDetail.vue`）：通过 / 失败 / 危险字面量 → `--app-status-success-text` / `--app-status-danger-text` / `--app-status-danger-bg`（含 `#a03030` 这类「令牌值的字面量副本」）

**③ 复盘落盘**

- `dev_docs/05-开发与测试/设计方案与报告/设计方案-前端L0-L5骨架层级图.html` 增补「主题令牌与布局对齐实测」章节：三层判定、逐层核对表、量化证据、偏差清单（含本轮未收敛的登记观察项）、闭环计划

**未纳入本变更（登记为观察项，见报告）**：`:root` 内 37 个模块私有变量（`--ai-*`/`--case-*`）与 L0 §④.3 口径冲突、`--doodle-*` 家族 fallback 漂移、146 处单值圆角、94 处废弃别名、41 处自建空态。

## 关联文档

- `dev_docs/05-开发与测试/设计方案与报告/设计方案-前端L0-L5骨架层级图.html`：本轮复盘的落盘处与实测数据来源（含 L0–L5 骨架层级图）
- `.agents/skills/vue-frontend-check/references/calibration.md`：判罚量规真相源（§2 判罚表 / §9 口径回写流程）
- `frontend/AGENTS.md`：L0 速查（令牌与 `:root` 口径）· L3/L4 速查（数据块与分类色例外先例）
- `openspec/specs/frontend-l0-paper-doodle/spec.md`：L0 既有能力（纸面与涂鸦），本变更不修改它
- 说明：`dev_docs/文档编号对照表.md` 不存在；本变更为前端主题令牌收敛，不改业务需求

## Capabilities

### New Capabilities

- `frontend-l0-design-tokens`: 模块样式对 L0 设计令牌的消费口径——语义/状态色与文本字号 MUST 走令牌、EP 默认调色板不得当模块色、数据编码分类色板 MUST 集中声明为具名局部变量

### Modified Capabilities

（无）

## Impact

- 前端代码 7 个文件：`dashboard/DashboardView.style.css` · `ai-assistant/KnowledgeBase.vue` · `device-inspector/components/PageElementsPanel.vue` · `case-manager/components/ProjectTree.vue` · `case-manager/CaseFileSheet.vue` · `report-generator/CaseBreakdown.vue` · `report-generator/ReportDetail.vue`
- 工具链：`vue-frontend-check` 判罚量规（calibration.md §2/§10）
- 文档：上述 HTML 设计方案；不涉后端、不涉协议、不改 `tokens.css` 令牌定义
- 门禁：`vue-tsc --noEmit` · `vue-frontend-check` 过 7 个改动文件 · 颜色观感需浏览器复核（本变更只做令牌替换，不改布局）
