## Context

模型调试页正文为左配置 / 右对话两栏（见已归档变更 `2026-09-23-widen-model-debug-chat-panel`：分栏 1fr : 2fr，断点 1200px）。右栏结构为：标题 + 范围说明 + 消息区（`ul.md-msgs`，`max-height: 66vh; overflow-y: auto`，无消息时换成 `div.md-empty`）+ 输入区（`.md-chat-input`，含设备下拉、`textarea`、清空 / 发送）。左栏「生效装配」的工具面板把每个分类的工具用 `p.md-group-sub`（分类名 + 启用数 / 总数）+ `ul.md-tools` 平铺渲染。

## Goals / Non-Goals

**Goals:**

- 对话区纵向约为原来的两倍，且**无消息时也占同样高度**（左右两栏高度差不再悬殊）。
- 工具分类默认收起，页面默认长度大幅缩短；展开后信息与现在完全一致。

**Non-Goals:**

- 不改分栏比例、断点、对话栏宽度。
- 不改工具数据来源、分组算法（`groupToolsByCategory`）、只读 / 写与启用标记的取值。
- 不改知识库 / Skill 面板、系统提示词折叠、角色分段入口与任何接口。

## Decisions

**D1：固定高度落在「消息区」这个语义上，有消息与无消息两种状态共用同一个 `md-chat-body` class。** 做法：`ul.md-msgs`（有消息）与 `div.md-empty`（无消息）各加 `md-chat-body`，由该 class 声明 `height: 132vh; overflow-y: auto`；`ul.md-msgs` 去掉 `max-height` / `overflow-y`，只保留列表排版。理由：两者由 `v-if/v-else` 渲染，同一时刻只存在一个，因此滚动归属始终唯一，无需额外包裹层（也就避免了把 50 多行消息模板整体缩进的改动）。空态之所以不能直接给 `.md-empty` 加高度，是因为该 class 在工具 / Skill / 知识库三处空态复用。备选：额外套一层 `div.md-chat-body` 包裹——语义更直白，但要改动整块缩进且引入一层无样式意义的 DOM，弃用。

**D2：分组组头用真按钮 + `.md-caret` 字符。** 组头由 `p.md-group-sub` 改为 `button.md-group-sub.md-group-sub--toggle`，内含 `aria-hidden` 的插入符 + 文案，与页内既有的「系统提示词」折叠头（`.md-group-head--toggle` + `.md-caret`）保持同一套写法。备选：用 CSS `::before` 画插入符——`.text()` 更干净，但与页内既有折叠头写法不一致，且无障碍靠 aria-expanded 已足够，弃用。

**D3：展开态存在页面组件的 `ref<string[]>`，按分类名索引，角色切换时清空。** 采用白名单（记录已展开的分类）而非黑名单，天然满足「默认全部收起」与「切换角色重置」；与页内既有的 `promptOpen` / `thinkingCollapsed` 同一种状态写法。备选：`el-collapse`——需按 doodle 主题重写皮肤，且与页内自绘折叠头两套观感，弃用。

## 模块防火墙自检

- 跨 App import：无（只动一个前端模块内的页面、样式与测试文件）。
- 引擎边界：不涉及 `engines/`、不涉及设备句柄。
- 通信通道：不新增 / 不修改任何 HTTP、WebSocket、SSE 调用。
- 前端不直连数据库、不新增写操作。

## Risks / Trade-offs

- [132vh 消息区会把输入框顶到折线以下，发消息需要先滚动页面] → 需求方已明确选择「按字面做两倍」并接受该代价；输入框始终在对话栏内消息区之下，位置关系不变。
- [无消息时 1.3 屏的空白区域可能显得空] → 空态提示与示例问法保留在该区域顶部；这是「左右两栏等高」诉求的必然结果。
- [默认收起后，原有测试里对工具名 / 徽标的可见性断言会失效] → 同步改测：`mountLoaded` 改为等角色带就绪，工具相关断言先点开对应分类再断言，并新增默认收起 / 展开 / 逐组独立的用例。

## Migration Plan

纯前端样式与组件状态调整，无数据迁移。回滚方式：还原 `ModelDebugPage.vue` 与 `ModelDebugPage.style.css` 两处改动。
