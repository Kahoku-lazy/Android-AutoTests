# 设备管理前端 UI 规范与 Checklist

> 版本 v2 · 2026-08-18
> 适用范围：`frontend/src/modules/device-pool/`（index.vue / DevicePoolView.logic.ts / api.ts / constants.ts / helpers.ts / routes.ts / composables×3 / components×6）及共享依赖（WorkbenchHeader / KpiCard / FilterTabs / AppTable / EmptyState / ErrorState 等）
> 设计语言：清新简洁风（暖纸底 · 模块色点缀 · 统一圆角 · 轻阴影），继承 Doodle Craft 的 paper 底纹与设计令牌，但**收敛装饰**（去图钉/微旋转/粗边/手绘波浪线）
> 唯一真相源：`frontend/src/shared/styles/tokens.css`（令牌）、`frontend/CLAUDE.md` §2（风格规则）

---

## 1. 组件归属

| 项 | 说明 |
|----|------|
| 模块位置 | `frontend/src/modules/device-pool/` —— 路由 `/devices`（routes.ts，meta title「设备管理」） |
| 页面骨架 | `index.vue`（薄组件，仅渲染）→ `DevicePoolView.logic.ts`（`useDevicePoolView` 编排器，组合 composable + 展示配置） |
| 数据层 | `composables/useDevicePoolState.ts`（设备池状态）→ `useDeviceActions.ts`（操作编排）→ `useHeartbeat.ts`（30s 心跳轮询）→ `api.ts`（11 个端点） |
| 配置/工具 | `constants.ts`（纯配置）、`helpers.ts`（纯函数：statusTag / displayModel / connectionLabel / formatRelativeTime） |
| 业务组件 | `DeviceCard`（拍立得设备卡）、`DeviceStatusCell`（状态列 el-tag + Badge）、`DeviceActionsCell`（操作列按钮组）、`DisconnectDialog`（删除确认）、`NetworkConnectDialog`（局域网连接表单） |
| 共享依赖 | `WorkbenchHeader`（页面顶栏）、`KpiCard`（统计卡）、`FilterTabs`（筛选标签）、`AppTable`（表格）、`EmptyState` / `ErrorState`（空/错态）、`shared/icons`、`shared/composables/usePagination` |
| 架构约束 | **device-pool 是管理模块（有写操作）**，区别于 dashboard 的只读聚合：scan/connect/lock/release/disconnect 均走 `api.ts` → djangoClient，组件不直连 HTTP |

---

## 2. 字体规范

### 2.1 字体系列（3 个 font 变量，2 种字体栈）

| 字体 | CSS 变量 | 用途 | 字重限制 |
|------|----------|------|---------|
| Cascadia Mono + 思源黑体（display） | `--app-font-display` | 章节标题、卡片组标题 | 700 |
| Cascadia Mono + 思源黑体（正文） | `--app-font` | 正文、按钮、表格、标签、状态 | 400–800 |
| Cascadia Mono 等宽 | `--app-font-mono` | 设备序列号、卡片组计数 | 600 |

> display 与正文同栈（英文 Cascadia Mono + 中文 Noto Sans SC），mono 为无中文回退的等宽栈，用于序列号等需要对齐的内容。

### 2.2 字号层级（设计系统最小 12px）

| 字号 | 写法 | 元素 |
|------|------|------|
| 32px | `var(--app-size-2xl)` ✅ | KPI 数字（KpiCard 共享组件） |
| 20px | `var(--app-size-lg)` ✅ | 章节标题（doc-section__title）、卡片组标题（card-group-title） |
| 14px | `var(--app-size-sm)` ✅ | 表格单元格、卡片名、序列号、连接类型、最后在线、卡片 info、表单标签/提示 |
| 12px | `var(--app-size-xs)` ✅ | doc-tag、章节 label、筛选标签、视图切换、工具栏、表头、Badge、操作按钮、图钉区序列号 |

> ⚠️ 低于 12px 无（本模块全部 ≥12px）；KpiCard 内部装饰字符 `~` 为 17px 字面量（共享组件）。

### 2.3 字重规则

| 元素 | 字重 |
|------|------|
| 章节标题 / 卡片组标题 / KPI 标签 / 表头 / Badge / 操作按钮 / 状态 tag | 700 |
| KPI 数字 | 800 |
| 辅助文字（章节 label / 筛选计数 / 连接类型 / 最后在线 / 卡片 info） | 600 |
| 序列号（mono） | 600–700 |

---

## 3. 颜色规范

### 3.1 必须使用 token，禁止硬编码色值

| 用途 | Token | 值 |
|------|-------|-----|
| 描边 / 文字（主） | `var(--ink)` | #1e1e24 |
| 模块色（薄荷绿） | `var(--c-device)` | #6BCB77 |
| 白纸卡底 | `var(--app-bg-card)` | #ffffff |
| 辅助文字 | `var(--app-ink-muted)` | #999 |
| 内部浅分割线（表格 th/td、视图切换分隔） | `var(--app-border-light)` | #e8ecf1 |
| 更浅分割线（表格 td） | `var(--app-border-lighter)` | #f0ede8 |
| 微妙底色（表头底、卡片组计数底、禁用态） | `var(--app-bg-subtle)` | #f8f6f2 |
| hover 荧光黄 | `var(--app-highlight)` | #FFE066 |
| 状态色系列 | `var(--app-status-success/-danger/-warning-bg/-purple/-purple-bg/-purple-border)` | #6BCB77 / #FFB5A7 / #FFF9E0 / #C9B6F2 / #E8DDF8 / #A78BFA |
| 状态文本 | `var(--app-status-success-text/-danger-text/-purple-text)` | #2d7a2d / #a03030 / #5a3fa0 |
| 删除语义色 | `var(--app-disconnect-text)` | #c53030 |
| 图钉（二阶） | `var(--app-pushpin-light/-dark)` | #e8e0d5 / #a09080 |
| 纸点（滚动条） | `var(--app-paper-dot)` | #d4cdc0 |
| 阴影 | `var(--app-shadow-sm/md/lg)` | 2px 2px 0 / 2px 3px 0 / 3px 4px 0 扁平 |

**白名单字面量**（沿用既有惯例，与 token 同值或装饰性）：

- `#fff`：白纸卡底（`--app-bg-card` 同值）
- 装饰 rgba：卡片阴影 `rgba(0,0,0,0.05/0.08)`、图钉投影 `rgba(0,0,0,0.08)`、照片区 badge 底 `rgba(255,255,255,0.7)`（见 §8 已知偏差，待收敛为 `--app-shadow-*`）
- 设备绿半透明 `rgba(107,203,119,0.04/0.2/0.15)`（section 底/边/表卡投影，见 §8）

### 3.2 状态色映射（constants.ts `DEVICE_STATUS_MAP` → el-tag type → 实际渲染）

| 设备状态 | el-tag type | 文本 | 实际渲染（DeviceStatusCell 覆盖） |
|---------|:-----------:|------|----------------------------------|
| `ONLINE` | success | 在线 | 绿：`--app-status-success-bg` 底 + `--app-status-success-text` 字 |
| `BUSY` | warning | 使用中 | 粉：`--app-status-danger-bg` 底 + `--app-status-danger-text` 字 |

> ⚠️ 注意 `warning` type 被覆盖为粉（BUSY）。改状态色时需同步 DeviceStatusCell.vue 的 `:deep(.el-tag--*)` 覆盖块。

状态 Badge（执行中/占用中/已锁定）映射：执行中=粉（danger）、占用中=黄（`--app-status-warning-bg` + `--c-dashboard` 边）、已锁定=紫（`--app-status-purple-bg` + `--app-status-purple-border`）。操作列锁定按钮为「已锁定 / 公开」切换（仅局域网设备显示，USB 设备无此按钮）。

### 3.3 KPI 卡配色（index.vue → KpiCard `color` prop）

| 卡片 | color | 形状 | 对应状态 |
|------|-------|------|---------|
| 在线 | `var(--app-status-success)` ✅ | diamond | ONLINE |
| 使用中 | `var(--app-status-danger)` ✅ | triangle | BUSY |
| 总计 | `var(--app-ink-muted)` ✅ | circle | 全部 |

---

## 4. 风格语言（Doodle Craft × Paper/Polaroid）

| 风格元素 | 规格 | 应用处 |
|---------|------|--------|
| KPI 统计卡 | 白底 + **统一圆角 `--app-radius-md`** + 1px 浅边 + 轻阴影 + 模块色几何图形（白描边）+ hover 抬升 | KpiCard（共享收敛） |
| 设备卡 | 白底 + `--app-radius-md` + **顶部 4px 状态色点缀条** + 轻阴影，标题区状态色底 | DeviceCard |
| 状态色渲染 | 999px 圆角 el-tag + Badge，状态色底/边（`--app-status-*`） | DeviceStatusCell |
| 视图切换 / FilterTabs | 分段控件 + pill 选中态（`--app-bg-subtle` 底 + ink 边） | FilterTabs（共享收敛）/ view-toggle |
| 数据卡（表格） | 白底 + `--app-radius-md` + 1px 浅边 + 轻阴影 | table-card |
| 点阵纸底 | radial-gradient 点阵 / `--doodle-bg` | doc-page 全局 |
| doc-tag | 英文小标签 12px/700、圆角 999px、1px 浅边 | 章节标题右侧 |
| 空态/错误态 | 居中 EmptyState / ErrorState + 重试 | 整页 / 表格空态 |
| 禁止项 | ❌ 模糊阴影 ❌ 对称大圆角（统一 `--app-radius-*`）❌ 玻璃态（backdrop-filter）❌ 全屏 spinner ❌ 手绘装饰（图钉/微旋转/波浪线/粗边） | — |

---

## 5. 布局规格

| 区域 | 规格 |
|------|------|
| 页面骨架 | `wb-shell`：wb-header（96px，`flex-shrink:0`）+ `doc-body`（`flex:1; min-height:0; overflow-y:auto`，padding 24px，gap 32px） |
| 章节流 | 统计概览 → 设备列表（`gap: 32px`），`device-section` 透明底无边框 |
| KPI 网格 | `repeat(3, 1fr)` gap 16px；**≤900px 断点** → 2 列 |
| 工具栏 | FilterTabs + 右侧（视图切换 / 设备计数 / 局域网 / 刷新），`flex-wrap: wrap` |
| 表格视图 | `table-card`（1px `--app-border-light` 边 + 圆角 `--app-radius-md` + 轻阴影）+ `device-table-wrapper`（横向滚动窗口，滚动条**蓝色常驻** `--c-workflow` 锚定卡片底部，8px 细分滚动条；el-table `min-width:max-content` 列按总宽平铺）；表头 `--app-bg-subtle` 底、正文白色 |
| 卡片视图 | `card-group-grid` `repeat(3, 1fr)` gap 16px；**≤900px** → 2 列；按状态分组（🟢在线 / 🔴使用中） |
| 滚动出口 | `doc-body` 纵向滚动（页面级）；卡片组视图 `overflow-y:auto`；表格**高度跟随 pageSize 行数**：首屏完整显示所选行数（5/10/20），超出屏幕由 `doc-body` 页面滚动查看 |
| 分页联动 | `usePagination`（`PAGE_SIZE_OPTIONS=[5,10,20]`）：`setPageSize` 重置至第 1 页并响应式重算 `pagedItems`/`totalPages`，切换行数**表格高度随之变化**并显示对应行数 |
| 键盘可达 | DeviceCard 有 `role="button"` + `tabindex="0"` + Enter/Space；其余交互为原生 button / el-button / router-link（无 div @click） |

---

## 6. 数据与协议（管理模块，含写操作）

| 项 | 说明 |
|----|------|
| 写操作收敛 | 组件 emit → `useDevicePoolView`（logic.ts）→ `useDeviceActions` → `api.ts` → djangoClient → `/api/devices/*`；**组件不直连 HTTP** |
| 信封 | `{status, data}` 或 `{status, message}`；各 action 解包后调用 `fetchDevices()` 刷新列表 |
| 端点（8） | `GET /devices`、`POST /devices/scan`、`POST /devices/{serial}`（connect）、`POST /devices/{serial}/activate`、`POST /devices/{serial}/lock`、`POST /devices/{serial}/release`、`POST /devices/{serial}/disconnect`、`GET /devices/heartbeat` |
| 字段（snake_case） | `serial` / `model` / `brand` / `screen` / `status` / `connection_type` / `locked_by` / `occupied_by` / `last_seen` / `user_id` / `waited_seconds` |
| 状态枚举 | `ONLINE` / `BUSY`（离线设备即删除，不保留；`DEVICE_STATUS_MAP` 是唯一映射源） |
| 锁定 / 公开 | `locked_by` 标记锁定者；锁定 = 仅管理员 + 锁定者可见可用，其他用户列表不显示；公开 = 所有用户可见可用。USB 设备恒公开（无锁定按钮），局域网设备默认已锁定；登录用户只能操作自己配置的局域网设备 |
| 三态 | loading（AppTable `:loading`）/ error（ErrorState + 重试）/ 空态（EmptyState，区分「无设备」与「筛选无匹配」） |
| 心跳轮询 | `useHeartbeat` 每 30s（`HEARTBEAT_INTERVAL`）`doHeartbeat()`，失败仅 debug 日志不打断 UI |
| 列表动效 | 表格行入场 staggerReveal（`LIST_ANIMATION`，translateY 16→0，350ms） |

---

## 7. 前端 Checklist（改设备管理必查）

### 7.1 字体

- [ ] 标题/卡片组标题用 `--app-font-display`，正文用 `--app-font`，序列号/计数用 `--app-font-mono`，无第四字体
- [ ] CSS 字号全部走 `--app-size-*`（≥12px），无 <12px 字面量
- [ ] KPI 数字（32px）走 `--app-size-2xl`，章节标题走 `--app-size-lg`

### 7.2 颜色

- [ ] 无新增硬编码 hex/rgba（grep `#[0-9a-fA-F]{3,8}` / `rgba(`，仅 §3.1 白名单；新增偏差登记 §8）
- [ ] 模块主色走 `--c-device`，不新造薄荷绿字面量
- [ ] 状态色走 `--app-status-*` 系列 + `DEVICE_STATUS_MAP`，改状态色同步 DeviceStatusCell `:deep(.el-tag--*)`
- [ ] KPI 卡颜色走 token（或语义色），不硬编码 hex（§8 #1 收敛前不新增同类）

### 7.3 风格

- [ ] 设备卡三要素齐备：白底 + 顶部 4px 状态色点缀条 + 统一圆角 `--app-radius-md` + 轻阴影（无图钉/微旋转/粗边）
- [ ] KPI 卡：白底 + 统一圆角 + 1px 浅边 + 轻阴影 + 模块色几何图形，无 `~` 水印
- [ ] 章节标题有模块色图标 + doc-tag（无手绘波浪线 ::after）
- [ ] 无玻璃态 / 手绘装饰（图钉/微旋转/波浪线/粗边）/ 全屏 spinner / 模糊阴影

### 7.4 布局与交互

- [ ] `doc-body` 滚动出口保持：`flex:1; min-height:0; overflow-y:auto`
- [ ] 900px 断点实测：KPI 2 列、卡片组 2 列，无横向溢出
- [ ] 表格 wrapper 双向滚动正常，长内容列不溢出
- [ ] 可点击元素键盘可达（role/tabindex/Enter/Space 或原生 button/a），无 div @click
- [ ] 三态完整：loading / error 重试 / 空态（无设备 vs 筛选无匹配）
- [ ] 视图切换（表格↔卡片）后布局仍可用，分页/筛选状态不串

### 7.5 验证方式

- [ ] 浏览器实测（非仅看代码）：DevTools computed style 抽查字号/字体/颜色
- [ ] 缩窗验证 900px 断点 + 表格横向滚动
- [ ] 写操作（锁定/释放/删除）走 api.ts 通道，组件无 fetch/axios
- [ ] 检查测试未依赖被改样式（`grep -rn "device-card\|device-section\|device-table\|status-cell\|action-bar" frontend/tests/`）

---

## 8. 已知偏差（待收敛，当前不阻塞）

| # | 位置 | 偏差 | 建议 |
|---|------|------|------|
| 1 | ~~`index.vue` KPI 卡 `#6BCB77`/`#FFB5A7`~~ | 硬编码 hex（「总计」却用 `var(--ink)`，写法不一致） | ✅ v2 已改为 `var(--app-status-success/-danger)` + `--app-ink-muted` |
| 2 | `constants.ts` `PAGE_HEADER.iconGradient` `#95D5B2/#52b788` | 硬编码渐变 hex | 收敛为 `var(--c-device)` 衍生或登记为白名单 |
| 3 | ~~`DevicePoolView.style.css` `rgba(107,203,119,0.04/0.2/0.15)`~~ | 设备绿硬编码 rgba（section 底/边/表卡投影） | ✅ v2 已移除（section/表卡改透明 + `--app-border-light`） |
| 4 | `DeviceCard.vue` `rgba(0,0,0,0.05/0.08)` + `rgba(255,255,255,0.7)` | 硬编码阴影 / 照片区 badge 底 | ✅ v2 已改用 `--app-shadow-sm/md`（图钉/照片区已移除） |
| 5 | `NetworkConnectDialog.vue` `#e8998a` + `rgba(232,153,138,0.14)` | 错误红硬编码（`--ac-red` fallback 带硬编码值） | 收敛为状态 token（如 `--app-error`） |
| 6 | `FilterTabs.vue`（共享组件）`#e8ecf1`/`#FFE066` | 共享组件硬编码（非本模块） | ✅ 已收敛为 `--app-border-light`/`--app-bg-subtle` |

### 8.1 待实现（PRD 新需求，尚未落地）

| # | 需求 | 实现缺口 |
|---|------|---------|
| 1 | 设备唯一性（§2.1）：无线设备序列号用 `ro.serialno` | 当前无线设备 `serial` 存的是 `IP:port`，需拆分「序列号」与「连接地址（IP:port）」两字段；连接列显示「局域网连接：IP 地址」 |
| 2 | 表格新增「设备连接时间点」列 | 当前模型仅 `created_at` / `last_seen`，无「连接时间点」字段，需明确映射或新增 |
| 3 | 去重提示「被谁添加」 | 当前设备表无「添加人」字段，需新增 |

---

## 9. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-14 | 文档创建 v1：组件归属 / 字体 / 颜色 / 风格 / 布局 / 数据协议 / checklist / 已知偏差，全部基于现有代码实测值 |
| 2026-08-17 | 移除离线设备：KPI 4→3 卡、筛选 4→3 tab、卡片 3→2 组、状态 4→2（在线/使用中）、去离线灰 token；信封统一 `{status,data}`（DRF 化） |
| 2026-08-17 | 设备锁定语义重构：由「用户独占」改为「锁定 / 公开」可见性（USB 恒公开无锁定、局域网默认锁定、仅管理员 + 锁定者可见、登录用户只操作自己的局域网设备） |
| 2026-08-17 | 登记待实现项（§8.1）：设备唯一性（serial 拆分）、设备连接时间点字段、被谁添加字段 |
| 2026-08-18 | 方向 A 落地 v2：整版收敛装饰改「清新简洁风」——共享 KpiCard 去 3px ink 粗边/`~` 水印（白底+统一圆角+轻阴影+模块色几何）；共享 FilterTabs 去粗边（pill 选中态）；全局 AppTable 表头 2.5px ink → 1px；设备卡去图钉/微旋转/粗状状态边改顶部点缀条；section 去模块绿底/2.5px 边；表格卡去 2.5px 模块边；KPI 卡硬编码 hex 收敛 token；操作按钮/状态标签圆角柔和化 |
| 2026-08-18 | 表格交互增强：`device-table-wrapper` 为滚动窗口，横向滚动条**蓝色常驻**（`--c-workflow`）并锚定卡片底部，便于左右滑动；表格高度自适应（首屏显示当前页行数，内容超过卡片才上下滚动）；新增「开发调试」按钮开关（`useDevicePoolState.toggleDevMock`），开启注入 60 条模拟设备测分页/横向滚动，关闭回拉真实后端 |
| 2026-08-18 | 表格高度随 pageSize 行数变化：去掉「表格占满剩余高度(flex:1)」语义，改 `.device-section--list`/`.table-card`/`wrapper` 内容自适应 + `doc-body` 页面级滚动；选择 5/10/20 行时组件高度随之变化并在首屏完整显示所选行数，超出屏幕由页面滚动；el-table `min-width:max-content` 横向滚动交 wrapper（蓝色常驻锚底） |
