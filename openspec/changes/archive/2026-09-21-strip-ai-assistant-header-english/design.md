## Context

见 `proposal.md` - Why。现状：`frontend/src/modules/ai-assistant/index.vue` 的 `VIEW_META` 按 `viewMode`（路由 `/ai-assistant/agents|toolbox|knowledge|evaluator`）把 `title`/`subtitle` 传给共享件 `WorkbenchHeader`。四条 `title` 目前是「中文 + 空格 + 英文对照」。共享页头只渲染传入字符串，无 i18n 层。

## Goals / Non-Goals

**Goals:**

- 只改 `VIEW_META` 四条 `title` 字符串，使 `.brand-title` 与规格场景一致。

**Non-Goals:**

- 不抽 i18n、不改 `WorkbenchHeader`、不改副标题与其它 AI 子页页头。
- 不改 `routes.ts` 的 `meta.title`（侧栏/文档标题已是中文）。

## Decisions

- **改数据源而非组件**：标题来自页面常量；共享页头无语言拼接逻辑。备选是给 `WorkbenchHeader` 加 `titleEn` 再隐藏——会扩大共享件契约，否决。
- **「AI工具箱」保留「AI」**：去掉的是独立英文短语 `AI Toolbox`，不是产品名里的拉丁缩写。备选把标题改成「工具箱」会改变既有中文品牌词，否决。

## 模块防火墙自检

- 跨 App import：不涉及后端。
- 跨 App service/runner：不涉及。
- 写库收敛到 api.py：无写库。
- 前端不直连数据库：仅改展示文案。

## Risks / Trade-offs

- [书签/截图仍写旧双语标题] → 文案变更，无接口破坏；刷新即可。
- [测试若硬编码旧标题会失败] → 仓库内当前无此类断言；实现时再 grep 确认。
