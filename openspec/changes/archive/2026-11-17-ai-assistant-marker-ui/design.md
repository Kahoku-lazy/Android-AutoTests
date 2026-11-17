## Context

`ai-assistant-cards` 已把助手名片、工具目录与测试对话接通（`/ai-assistant` 网格 + `/ai-assistant/:assistantId/chat` + 配置弹窗），但三处界面只做到「能跑」：卡片动作用原生按钮、配置弹窗是裸表单、对话页是裸控件。doodle-craft 里已登记「AI 助手颜料片」一节，但只写了卡片一条，对话页与配置弹窗没有规格，实现也就没有跟随。

卡片上的「配置」实际打开的是空白新建表单（`@edit="editorOpen = true"` 丢掉了卡片），前端 api 层也没有 `PATCH` 封装，所以「改配置」这条路径目前不存在。

## Goals / Non-Goals

**Goals:**

- 三处界面共用同一套「一卡一色」视觉语言，且不污染全站 Doodle Craft。
- 配置弹窗可编辑：预填、保存回写、换/删头像。
- 对话页在保留多对话栏交互的前提下，用该助手的笔色做识别。
- 规格登记进 doodle-craft，后续复用有据可依。

**Non-Goals:**

- 不改计费口径、不改既有助手名片与消息表结构（对话栏复用现有 `AIAssistantThread` / `AIAssistantMessage`）。
- 不引入 `.sketch-kit`（手稿控件皮肤）到助手模块。
- 不做 SOP、不做消息富文本、不做流式输出。
- 不改全站 `tokens.css` 与其它模块的虚线白名单。

## Decisions

### 1. 笔色变量标在元素上，浅底与渐变在组件里现算

`--assistant-marker` 由 `helpers/marker.ts` 以行内样式写到卡片 / 对话页根（值为 `var(--assistant-marker-<key>)`，色值仍只在模块 `tokens.css`）。`--assistant-marker-soft` / `-tint` / `-gradient` **在组件 `<style>` 里就地声明**，从 `--assistant-marker` 用 `color-mix` 派生。

备选是在 `.ai-assistant-page` 上集中声明这三个派生变量。否决：自定义属性的 `var()` 在声明它的元素上求值，页面级声明会被算成默认笔色再往下继承，卡片上改 `--assistant-marker` 不会让派生值重算——表现为「所有卡片都同一档浅色」。

### 2. 虚线仍然只属于 `AssistantCard.vue`

卡片外框 `2.5px dashed var(--ink)`、卡内两个动作 `1.5px dashed var(--ink)`，都在 `AssistantCard.vue` 内声明（该文件在 `check-dashed-whitelist.mjs` 的 OWNERS 里）。配置弹窗、对话页、输入框一律实线。

### 3. 配置弹窗用主线实线控件，不挂 `.sketch-kit`

`.sketch-kit` 的输入框选择器只匹配 Element Plus 的 `.el-input__wrapper` / `.el-select__wrapper`。编辑器为了轻量与可测性仍用原生 `input` / `select`（现有 P0 用例按 `input` / `select` 交互）。把 `.sketch-kit` 挂上去只会让按钮变虚线、输入框仍是实线，正好踩中 kit 文档里「同一个表单一半虚线一半实线」的反模式。因此配置弹窗按主线皮肤做：2px 实线墨框 + 纸底 + 2px 圆角 + 硬影，动作按钮用共享 `DoodleBtn`。

### 4. 弹窗外壳用 `el-dialog`，编辑器只出表单本体

`index.vue` 持有 `el-dialog`（焦点陷阱、Esc、遮罩由 EP 提供），`AssistantEditor.vue` 只渲染表单并 `emit("close" | "saved")`。这样编辑器不需要 teleport 就能单测，符合「L5 覆盖层一律走 EP」。

### 5. 编辑模式与 `PATCH`

`AssistantEditor` 新增 `card?: AssistantCard | null`：有值时预填（工具取 `card.tools[0]` 的 `domain` / `preset`），保存走 `updateAssistant(assistant_id, payload)`（`PATCH`，multipart）。头像三态：保留原图（不发头像字段）、换图（发 `avatar` 文件）、移除（发 `clear_avatar=1`）。后端 `partial_update` 已实现这三条。

### 6. 对话页的助手名从路由 query 带入

`openChat` 现在带 `query: { marker, name }`。页面不再为了标题多请求一次列表；缺失时标题回落「对话」。`marker` 缺失回落到 `teal`。

### 7. 对话栏的重命名与删除各用一个端点，取消语义不动

- 重命名：`PATCH /api/ai/assistants/threads/{thread_id}/`，体 `{title}`。空标题落库成 `""`，前端回落「对话 N」。
- 删除：`POST /api/ai/assistants/threads/{thread_id}/delete/`（仓内既有动作式写法，如 `/ops/users/{id}/disable/`）。
- 取消仍是 `DELETE /api/ai/assistants/threads/{thread_id}/`，**不改**：前端已有调用、语义已在 `ai-assistant-cards` 里约定。把 `DELETE` 改成"删除记录"会让"取消只停当前栏"变成"取消即销毁"，是破坏性变更。

删除时若该栏在跑：先 `request_thread_cancel`，再删行。后台线程写回前会在 `finish_message` 里先查栏是否还在，不在就跳过——否则删除会留下 FK 报错日志。

### 8. 当前栏改用浅蓝填充

按需求方指定，选中态从"笔色描边 + 硬影"改为**浅蓝填充**（`color-mix(--c-workflow 40%, 白)`）+ 2px 墨框；「新建对话」改用 `DoodleBtn tone="teal"`。对话栏不再承载助手笔色，笔色只留在气泡、发送钮、页头图标与卡片。

## Risks / Trade-offs

- [query 里的中文名会被转义] → 只用于标题展示，刷新后仍在 URL 里，可接受。
- [原生 `select` 的下拉列表由系统绘制] → 只影响展开态的样式，收起态与全站输入框一致；换来不引入 EP 依赖与测试改写。
- [卡片笔色与 `--c-ai`（模块色）不是同一套] → 模块色只给页头图标与侧栏，卡片一卡一色是需求方点名的专有风格，二者各管一层。

## 模块防火墙自检

- 只动 `frontend/src/modules/ai-assistant/` 与 doodle-craft 技能文档；不跨模块 import。
- 笔色令牌留在模块 `tokens.css`，不进全局 `tokens.css`。
- 写接口复用既有 `PATCH /api/ai/assistants/{assistant_id}/`，前端不直连数据库、不自拼 URL。
