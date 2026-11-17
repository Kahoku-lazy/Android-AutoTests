# AI 助手颜料片（专有：卡片 / 配置弹窗 / 对话页）

只服务 `frontend/src/modules/ai-assistant/`。不改全局 `tokens.css`，不扩散到其它模块。
参考 StyleKit Hand-Drawn Doodle 的 Five Marker Colors：**一卡一色、微倾、硬偏移阴影**。
上游「只用平涂、禁渐变」在这里有两处已批准的偏离，见 §2。

## 1. 笔色色板

色值只登记在 `frontend/src/modules/ai-assistant/tokens.css`，组件只引用变量名
（`helpers/marker.ts` 把后端 `marker` 键映射成行内 `--assistant-marker`）。

| 键 | 变量 | 色值 | 观感 |
| --- | --- | --- | --- |
| `teal` | `--assistant-marker-teal` | `#1f7a6a` | 深青绿（默认 / 回落值） |
| `ink` | `--assistant-marker-ink` | `#2c3a4a` | 墨蓝灰 |
| `amber` | `--assistant-marker-amber` | `#b2710c` | 赭橙 |
| `rose` | `--assistant-marker-rose` | `#b44a6a` | 玫红 |
| `moss` | `--assistant-marker-moss` | `#3d6b32` | 苔绿 |

派生值由消费它的组件**在自己身上**用 `color-mix` 现算，不落页面级：

```css
--assistant-marker-soft: color-mix(in srgb, var(--assistant-marker) 34%, var(--paper)); /* 渐变浅端 */
--assistant-marker-tint: color-mix(in srgb, var(--assistant-marker) 10%, var(--paper)); /* 浅底 hover */
```

> **为什么不能写在 `.ai-assistant-page`**：自定义属性的 `var()` 在声明它的元素上求值，
> 页面级声明会被算成默认笔色再往下继承——表现为「所有卡片共用一档浅色」。踩过。

笔色由后端在创建时按「上一张名片的 marker」轮转分配，相邻不同色、不按彩虹序；换头像不换色。

## 2. 允许偏离全站的两处

| 偏离 | 只允许 | 禁止 |
| --- | --- | --- |
| 虚线墨框 `2.5px dashed var(--ink)`（卡片外框）/ `1.5px dashed var(--ink)`（卡内动作） | `AssistantCard.vue` | 配置弹窗、对话页、输入框、其它模块 |
| 同色深到浅渐变 | 无头像中间圆、该助手对话页发送钮、对话页页头图标 | 卡片底、页面底、用户气泡、弹窗 |

卡片底、弹窗底、对话页底仍是纸色 / 白卡。笔色只做描边装饰、硬影、中间圆、当前栏与发送钮；
字体沿用全站，不换手写体。

## 3. 卡片：只显示三样

自上而下固定四层：**上边沿中心的笔色图钉 → 头像或笔色圆 → 显示名 → Agent 配置名**。
圆在上、名字在下（与上游 Five Marker Colors 的色卡同构）；早期把名字放最上面是错的，已按参考图纠正。

- 图钉：`12px` 圆点，`left: 50%` + `translateX(-50%)`、`top: -6px`（跨在虚线上），
  填充该助手笔色，`box-shadow: 0 0 0 3px var(--paper)` 把虚线断开——读作"钉在板上"。
  它只做身份标记，不承载信息、不响应点击、`aria-hidden`。
- 显示名：16px 重字重、单行省略；Agent 配置名：14px 次级色、单行省略。
- 工具、模型、编号、状态一律不上卡。

| 维度 | 规格 |
| --- | --- |
| 外框 | 纸底 · `2.5px dashed var(--ink)` · 圆角 `2px` · 内距 `24px 16px 16px` |
| 图钉 | `12px` · 笔色填充 · `top: -6px` · 纸色 3px 光晕 · 居中 |
| 硬影 | `4px 4px 0 0 var(--assistant-marker)`；hover `6px 6px` |
| 微倾 | 按序号 `-0.8° / 0.6° / -0.3°`；hover 回正并 `translate(-2px,-2px)` |
| 头像 / 笔色圆 | `88px` · `2.5px solid var(--ink)` · 头像 `object-fit: cover` · 无头像 `linear-gradient(165deg, marker, soft)` |
| 动作 | 两枚 `30px` 高小按钮：`1.5px dashed var(--ink)` · 透明底 · 12px 重字重；hover 笔色 10% 浅底 + `2px 2px` 影 |
| 焦点 | `outline: 2px solid var(--c-dashboard); outline-offset: 2px` |
| 动效降级 | `prefers-reduced-motion: reduce` 下取消位移与过渡 |

「配置 / 对话」是动作不是信息字段，保留常显；卡内按钮同样受虚线白名单约束（由 `AssistantCard.vue` 渲染）。

### 3.1 工作流便签卡（同一组件，2026-11-17）

`AssistantCard.vue` 的另一个形体：**Tape Strip 便签卡**（参考 StyleKit Hand-Drawn Doodle 的
Notebook Artifacts → Tape Strip）。它和颜料片共用**同一个文件**（虚线白名单按文件判定），
但视觉是另一张卡：不图钉、不硬影、不居中；改用顶部胶带 + 白卡 + 浅墨虚线框 + 左对齐文字。

| 维度 | 规格 |
| --- | --- |
| 外框 | 白卡底 `var(--app-bg-card)` · `2px dashed color-mix(ink 32%, transparent)` · 圆角 `var(--app-radius-md)` · 内距 `32px`（`--app-space-xl`） |
| 列宽 | 网格 `repeat(auto-fill, 280px)`（**2026-11-17 需求方按红框指定为固定 280px**；原来的 `minmax(280px, 360px)` 会把单卡拉到 360px、右侧空一大片，已废弃） |
| 胶带 | `88×26`、`top: -12px`、居中、`rotate(-2deg)`、**无描边**；**半透明笔色自浅向下渐隐**（见 §3.2），`42% → 14%` |
| 阴影 | 静止无影；hover 才出 `3px 3px 0 0 color-mix(笔色 28%, transparent)`，同时回正并 `translate(-2px,-2px)` |
| 标题 | 工作流名，20px 重字重墨色，单行省略 |
| 正文 | **三行**：名称 / `执行者：…` / `验收者：…`；后两行 14px 次级色、行高 `normal`、单行省略；卡片内元素间距 `8px` |
| 底部一排 | 三块**同尺寸**（`min-width: 56px`、高 `26px`、`1px` 墨框 `22%`、圆角 `5px`、**无硬影**）：`配置` 天蓝渐变、`任务` 薰衣草紫渐变（均 `linear-gradient(180deg, color-mix(--c-workflow/--c-element 20%, 纸), … 5%, 纸)`），第三块是笔色 30% 浅底、描边透明（**无文字、无交互、`aria-hidden`**） |
| 可点感 | 靠 hover：`translate(-1px,-1px)` + `2px 2px 0 0 color-mix(ink 20%)` 浅影；`:active` 归零。静息态不许再挂 `2px 墨框 + 2px 黑影`（那会把便签卡读成"卡里放三个按钮"） |
| 微倾 | 与颜料片同一套 `-0.8° / 0.6° / -0.3°` 三值轮转；`prefers-reduced-motion` 下取消 |

信息仍只有「名称 + 两名片名」；第三块不是信息字段，不得往上写文案，也不得做成可点。
纸底比 StyleKit 文档页的白底更暖，所以填充不照抄参考的 40–50% 透明度，改用 78–85% 的模块色保住辨识度。

### 3.2 胶带：半透明浅色渐变（2026-11-17 需求方指定）

胶带不用条纹、不用实色，用**同一支笔色的半透明竖向渐变**：上端稍浓、往下渐隐，
叠在白卡上仍能看见纸色底。

```css
background: linear-gradient(
  180deg,
  color-mix(in srgb, var(--assistant-marker) 34%, transparent) 0%,
  color-mix(in srgb, var(--assistant-marker) 10%, transparent) 100%
);
border: 1px solid color-mix(in srgb, var(--assistant-marker) 26%, transparent);
```

- 蓝笔色 → 浅蓝往下渐隐；其它笔色同理，**不得**写死某个颜色。
- 禁 `backdrop-filter`（全站禁令）；透明度只靠 `color-mix(..., transparent)`。
- 运行日志卡（§5.2）与 `DoodleNote` 的胶带仍是条纹 / 实色口径，本次只改工作流便签卡。

## 4. 配置弹窗（新建 / 编辑）

- 外壳用 `el-dialog`（`width="min(520px, 92vw)"`）。**不要 `append-to-body`**：弹窗一旦 teleport 到
  `body` 就脱离 `.ai-assistant-page`，`--assistant-marker-*` 取不到，头像预览圆会变成空白。
- 表单走**主线实线控件**，不挂 `.sketch-kit`：kit 的输入框选择器只匹配 Element Plus 的
  `.el-input__wrapper`，而这里为轻量与可测性用原生 `input` / `select`，挂 kit 只会得到
  「按钮虚线 + 输入框实线」的半套皮肤。
- 字段顺序固定：**头像 → 名称 → Agent 配置 → 工具域 → 预设**（选了工具域才出现）。头像在最上方，
  与卡片「中间那个圆就是身份」一致；把名称放前面会让弹窗阅读顺序和卡片阅读顺序相反。
- 头像提示文案分两态：新建「不上传就显示创建时分配的笔色渐变圆」，编辑「不上传就显示该助手的笔色渐变圆」。
- 控件：`2px solid var(--ink)` · 圆角 `2px` · 高 `36px` · 14px；`select` 加 `appearance: none`
  并自绘 8px 墨色双边框箭头（不用图片、不写色字面量）。
- 头像预览 `64px` 圆，与卡片同一套笔色语言；标题 14px medium 墨色；错误行 14px danger 色。
- 动作：右对齐，`DoodleBtn` `paper` 取消 / `yellow` 保存；按钮顺序固定「取消在左、保存在右」。
- 编辑语义：点「配置」预填该名片；保存走 `PATCH /api/ai/assistants/{id}/`；头像三态为
  保留（不发字段）/ 换图（发 `avatar`）/ 移除（发 `clear_avatar=1`）。编号与笔色不可改。

## 5. 对话页

| 位置 | 规格 |
| --- | --- |
| 页头 | `WorkbenchHeader`，标题 = 该助手显示名（缺省回落「对话」），`icon="bot"`，`icon-gradient` 用 marker → soft；**页头不放任何动作按钮** |
| 返回入口 | `DoodleBtn`（`paper`）「‹ 返回助手」，放在 `.doc-body` 顶部工具条（`.ai-chat__toolbar`）左端，与页头分开 |
| 两栏分隔 | 纵向虚线分隔条从「对话栏面板」右侧 12px 处起、拉满整列高度（`right: -12px` + `top/bottom: 0`），由 `AssistantLanePanel.vue` 自己声明；**不得贴着或压住面板边框** |
| 左栏 | `AssistantLanePanel.vue`（`240px`）：纸色虚线卡，见下方 §5.1 |
| 对话栏条目 | `40px` 高 · `1px` 24% 墨框 · 14px；右侧状态 12px 次级色 |
| 当前栏 | `2px solid var(--assistant-marker)` + `3px 3px 0 0` 笔色硬影 |
| 状态 | `idle 空闲 / running 进行中 / done 已完成 / cancelled 已取消 / interrupted 已中断`；`running` 用笔色浅底 |
| 助手气泡 | 白卡底 · `2px solid var(--assistant-marker)` · 左对齐 · `max-width: 72ch` |
| 用户气泡 | 纸色底 · `2px solid var(--ink)` · 右对齐（**不用笔色填充**） |
| 气泡时刻 | 气泡下方 `12px` 次级色 `HH:mm`（`helpers/time-label.ts` 的 `clockLabel`，只取墙上时间）；与**自己那条气泡**同侧对齐（用户靠右、助手靠左），不按列表位置猜 |
| 发送钮 | `36px` · `2.5px solid var(--ink)` · 笔色深到浅渐变 · `3px 3px 0 var(--ink)` 硬影；禁用转灰底无影 |
| 取消 | `2px solid var(--app-status-danger-text)` 描边 + 纸底红字 |
| 输入框 | `2px solid var(--ink)` · `36px` · 纸底白；composer `position: sticky; bottom: 0` |
| 布局 | 内容短时输入框贴底、内容长时由 `.doc-body` 滚动：`.ai-chat .doc-body { display:flex; flex-direction:column }` + `.ai-chat__stream { flex:1 }`，**不新增第二层纵向滚动** |
| 空态 | 「这个对话栏还没有消息，发送第一句开始。」一行 14px 次级色 |
| 运行日志 | 工具条「日志」按钮（`DoodleBtn` `paper`，`aria-expanded`）开关；日志卡在**左栏、对话栏下面**（`AssistantLanePanel` 默认插槽），展开时左栏 `240px → clamp(320px, 30%, 420px)`、聊天列收窄，见 §5.2 |
| 日志卡 | `ThreadLogPanel.vue`：**一轮一张** —— `1.5px dashed` 笔色（70% + 纸色）· 顶部居中胶带 · `4px 4px 0 0` 笔色硬影（26%）· `--app-radius-md` · 白卡底 · **0° 不倾斜**；卡内首行时间（`MM-DD HH:mm`）+ 一句话结果，右端「查看 / 还在写」；进行中不可点、不显示时间 |

### 5.1 对话栏面板（`AssistantLanePanel.vue`）

参考 Five Marker Colors 的 **Wavy Underline** 卡：浅墨虚线框 + 名称 + 笔色双波浪线，**不倾斜**。

| 维度 | 规格 |
| --- | --- |
| 外框 | 纸底 · `1.5px dashed color-mix(in srgb, var(--ink) 38%, transparent)` · 圆角 `--app-radius-md` · 内距 `16px` · **四边闭合** |
| 板块分隔 | `.lane-column__split`：`1.5px dashed` 浅墨竖线，`position: absolute; right: calc(var(--app-space-lg) / -2); top/bottom: 0`，落在两栏 24px 间距的**中线**（与面板右边框留 12px），拉满整列高度，`role="separator"` |
| 倾斜 | **0°**：面板与面板内条目都不做 rotate / hover 位移（虚线已经足够"手绘"，再倾斜会读成错位） |
| 名称 | 标题「对话栏」14px 重字重 + 右侧数量 12px 次级色（`2 个`） |
| 双波浪线 | 内联 SVG，两条 `2.5px` 圆头波浪（`viewBox 96×18`）：上波 `var(--assistant-marker)`（身份色），下波 `var(--c-ai)`（模块色，做第二支彩笔）；`aria-hidden`，只做身份装饰 |
| 条目 | `40px` · `1px` 24% 墨框 · 14px · 白底；悬停转墨框；`:focus-within` 走 `--c-dashboard` 环 |
| 当前栏 | **浅蓝填充** `color-mix(in srgb, var(--c-workflow) 40%, var(--app-bg-card))` + `2px solid var(--ink)`（需求方指定；不再用笔色描边 + 硬影） |
| 新建对话 | `DoodleBtn tone="teal"`（参考 Sketched UI Kit 的 Teal 变体：`--c-case` 底 + 2.5px 墨框 + 3px 墨色硬影） |
| 条目动作 | 行内右侧浮出 `✎`（重命名）/ `✕`（删除）两个 24px 幽灵按钮：`opacity 0` → `:hover` / `:focus-within` 显现，`@media (hover: none)` 常显；底色 `background: inherit` 跟随白底 / 浅蓝底 |
| 就地改名 | 该行切成输入框（几何不变，`min-height: 38px`），Enter 提交、Esc 取消、失焦提交；空标题 = 恢复默认名 |
| 删除 | 先 `ElMessageBox` 二次确认；删的是当前栏则切到剩余第一栏，没有剩余就新建一栏 |
| 状态文案 | 由 `helpers/thread-status.ts` 统一：`idle 空闲 / running 进行中 / done 已完成 / cancelled 已取消 / interrupted 已中断` |

「新建对话」按钮沿用 `DoodleBtn`（`teal`），排在标题与波浪线之后、列表之前。

### 5.2 运行日志卡（`ThreadLogPanel.vue`）

对话页特有，**一轮一张虚线卡**（需求方 2026-11-16 给的手绘参考图：虚线外框 + 顶部胶带 + 偏移阴影），位置在**左栏、对话栏面板下面**：`AssistantLanePanel` 开默认插槽，左栏本身是 `flex-direction: column` + `--app-space-lg` 间距，日志卡跟着对话栏同列堆叠。

- **为什么不在对话区**：塞在消息流里会把消息往下顶，而助手气泡只占 `72ch`（约 590px），右侧会空出一大片（2026-11-16 截图红框）；放进 `.ai-chat__body` 当第三个网格子项又会换行，把对话区挤进 240px 左栏。
- **展开 / 收起**：日志展开时 `.ai-chat__body` 挂 `is-logs-open`，左栏 `240px → clamp(320px, 30%, 420px)`、聊天列等量收窄（`transition: grid-template-columns`，reduced-motion 下取消）；收起回 `240px` 且不渲染日志卡。左栏是两栏里唯一会被 `--assistant-marker` 与虚线同时使用的地方，但不加第二层滚动。
- **卡规格**：`1.5px dashed color-mix(笔色 70%, 纸色)` + `--app-radius-md` + 白卡底 + `4px 4px 0 0 color-mix(笔色 26%, transparent)` 硬影；胶带 `56×14`、`top: -8px`、居中、笔色 26% + 纸色，**卡与胶带都不倾斜**（需求方明确不要斜）。hover 只做 `translate(-1px,-1px)` + 阴影加一档，`:disabled` 转浅墨虚线、去硬影。
- **时间**：首行左侧 `MM-DD HH:mm`，来自该轮助手消息的 `created_at`（后端给本地 ISO，带 `+08:00`）；老数据缺时间才回落报告编号（`helpers/time-label.ts` 的 `logCardTime`）。进行中的一轮没有时间，显示 `—`。
- **三态**：加载 `SkeletonCard variant="list"`；失败 `ErrorState`（带重试）；空 `EmptyState`（「这一栏还没有运行日志」）。
- **滚动**：卡片列表自身不滚；左栏随日志条数变长，纵向滚动仍只归 `.doc-body`。
- **准入**：本卡是虚线白名单的第三个落点（OWNERS 已登记），笔色只做描边 / 胶带 / 硬影，不铺底。

## 6. 反模式

- ❌ 在 `.ai-assistant-page` 上预置 `--assistant-marker-soft` / `-tint` / `-gradient`（不重算，全卡同色）。
- ❌ 给配置弹窗、对话页气泡 / 输入框加虚线：本模块只有 **颜料片**、**对话栏面板**、**运行日志卡** 三个虚线落点。
- ❌ 给日志卡或它的胶带加倾斜：参考图是规整卡，需求方明确不要斜；hover 只做位移回正。
- ❌ 给对话栏条目加倾斜 / hover 位移：参考图是规整卡，倾斜会读成错位。
- ❌ 把「当前栏」又画回笔色描边：选中态的唯一信号是**浅蓝填充 + 墨色描边**。
- ❌ 把颜料片或对话栏面板的虚线 CSS 抄进别的组件（白名单按文件判定，抄过去不算数）。
- ❌ 弹窗 `append-to-body`（丢模块令牌，笔色预览空白）。
- ❌ 用 `--c-ai`（模块色）冒充笔色：模块色只给侧栏与页头默认图标。
- ❌ 卡片上补工具清单、模型名、编号、状态角标。
- ❌ 把笔色铺成气泡底或页面底（只做描边、硬影、中间圆、发送钮）。
- ❌ 用户气泡用笔色填充；它必须保持纸色。
- ❌ 把运行日志列表直接塞进 `.ai-chat__body`：多一个网格子项就换行，240px 左栏会吃掉整个对话区（2026-11-16 线上表现：日志按钮铺满右半屏、气泡挤成窄条）。
