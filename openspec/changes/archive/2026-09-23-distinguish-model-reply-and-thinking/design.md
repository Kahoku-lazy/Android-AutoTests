## Context

现状（重排后的 `ModelDebugPage.vue` 助手消息，`li` 内三行）：

    <p class="md-msg-role">{{ model_name }}</p>
    <p class="md-msg-text" :class="{ err: item.error }">{{ item.content }}</p>
    <p v-if="thinkingOf(item)" class="md-msg-thinking">{{ thinkingOf(item) }}</p>

`.md-msg-text` 与 `.md-msg-thinking` 都是无标题文本块，样式只差字号与颜色，思考块紧跟结果之后。后端已经把两者分开：`run_role_chat` 返回 `reply: result.output` 与 `thinking: result.thinking`（`apps/ai_assistant/model_debug.py:257-265`），而 `thinking` 是 `list[str]`（`engines/ai/agentscope/model.py:175`，逐个 `ThinkingBlock`）——契约无需改动，问题纯在前端展示。

约束：只改本模块前端；页面加折叠态后仍须远低于 500 行；不新增共享件与依赖。

## Goals / Non-Goals

**Goals:** 结果与思考各自有可见标题；思考可折叠且折叠态逐条独立；无思考不渲染空块；文案单一来源。

**Non-Goals:** 不动 `thinking` / `reply` 字段与接口；不改消息顺序（结果仍在思考之前）；不做流式思考、不加耗时统计、不做 Markdown 渲染思考；不重排右栏对话版式。

## Decisions

**D1 在消息内拆两个子区块，不给消息加新壳。**
`.md-answer`（标题 + 正文）与 `.md-think`（折叠头 + 正文）。理由：层次问题用标题解决，可断言、可测、无需新组件。备选「只加一个『思考』前缀标签」——不足以表达层级，长思考仍无法收起。

**D2 思考默认展开，点击收起。**
理由：本页的存在意义就是判断「模型收到提示词后在想什么」，默认展开保证信息不消失，折叠只为长思考提供出口。备选「默认折叠」——用户诉求是**区分**而非隐藏，默认折叠会让人以为思考没了。

**D3 折叠态只记「被收起」的消息 id。**
默认展开 ⇒ 只需记录例外：`ref<number[]>` + `isThinkingOpen(id)` / `toggleThinking(id)`；按 id 判断，MUST NOT 用全局单值（两条消息会串状态）。`messages` / `role` 变化时清空该列表。

**D4 三个标题文案进 `constants.ts`。**
`MODEL_DEBUG_ANSWER_LABEL` / `MODEL_DEBUG_ANSWER_ERROR_LABEL` / `MODEL_DEBUG_THINKING_LABEL`；组件内无魔法字符串，单测引用常量而非字面量（改文案不会假失败）。

**D5 视觉区分全部取令牌。**
思考块 `border-top: 1.5px dashed var(--dot)` + `background: var(--app-bg-subtle)` + `white-space: pre-wrap`；结果块透明底、正文 `--app-size-sm` / `--ink`，与思考的 `--app-size-xs` / `--app-text-secondary` 形成层级。

**D6 折叠头是可点击可达的 `<button type="button">`。**
带 `aria-expanded`，与页面既有的提示词折叠头同写法（`md-group-head--toggle` 的同类交互）。

## 模块防火墙自检

- 只改 `frontend/src/modules/ai-assistant` 下的 ModelDebugPage.vue / .style.css / constants.ts；无跨 App import。
- HTTP 仍只经 `api/toolbox.ts` → `shared/api-client`；组件不碰网。
- 零后端改动：不碰 apps/、engines/、路由与 urls；无写库。
- 无新增共享件、无新依赖。

## Risks / Trade-offs

- [思考默认展开仍显冗长] → 折叠头常驻且字数可见，一键收起；不删数据、不改契约。
- [折叠态按 id 记录，清空消息后残留 id] → 残留仅占极少内存且不影响渲染（id 不复用）；`messages` / `role` 变化时一并清空。
- [文案常量与断言耦合] → 单测引用常量，改文案不会假失败。

## Migration Plan

无数据迁移、无接口变更。回滚 = 还原 ModelDebugPage.vue / ModelDebugPage.style.css / constants.ts 三个文件。

## Open Questions

（无）
