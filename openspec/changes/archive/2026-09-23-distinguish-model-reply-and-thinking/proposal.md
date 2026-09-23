## Why

模型调试页的助手消息把两块内容堆在同一个 `<li>` 里：`.md-msg-text`（模型返回结果）与 `.md-msg-thinking`（思考过程）。两者都没有标题、没有分隔，样式上只有字号（14px / 12px）与颜色（`--ink` / `--app-text-muted`）之差，思考块还紧贴在结果正下方——用户看到 `//*[@id="app"]/div/main/div[2]/div/div/div/div/aside/ul/li[2]` 时无法判断哪段是「返回的结果」、哪段是「模型的思考过程」。后端其实已经分开（`thinking: list[str]` 与 `reply` 是两个字段），问题只在前端展示。

## What Changes

- 助手消息拆成**两个各自带标题的独立区块**：返回结果（标识「回复」；调用失败时为「调用失败」）与思考过程（标识「思考过程」+ 字数）。
- 思考过程区块**可折叠**（默认展开，点击标题收起/展开），折叠状态**逐条消息独立**。
- 思考过程区块与结果正文**视觉区分**（虚线分隔 + 独立底色 + 保留换行），MUST NOT 与结果混为一体。
- 无思考过程时 MUST NOT 渲染空的思考区块。
- 三个区块标题文案收敛到 `constants.ts` 常量（唯一真相源），组件内不留魔法字符串。
- 用户消息不变（身份行已是「我」，内容即提问）。
- **零后端改动**：`thinking` / `reply` 字段与接口契约、权限、5 分钟超时、不落库、不挂工具全部不动。
- **不**改工具箱来源卡片、平台工具调试页与其它页面；消息顺序不变（结果仍在思考之前）。

## 关联文档

- PRD-需求总纲（AI 助手条目）
- 前置变更：add-model-debug-console（本单只改其对话消息的展示）、relayout-model-debug-page（右栏对话版式）
- 诊断现场：用户报告的元素 `//*[@id="app"]/div/main/div[2]/div/div/div/div/aside/ul/li[2]`（右栏对话第 2 条 = 助手消息）

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- ai-model-debug: 新增「调试对话须区分回复与思考过程」要求——两个带标题的独立区块、思考可折叠且折叠态逐条独立、无思考不渲染空块。既有行为需求（配置读取 / 对话 / 权限 / 超时 / 不落库 / 不挂工具 / 页面三层层级）不变。

## Impact

- 前端（唯一改动面）：frontend/src/modules/ai-assistant/ModelDebugPage.vue、ModelDebugPage.style.css、constants.ts（新增 3 个标题常量）。
- 测试：frontend/tests/ai-assistant/p0/useModelDebug.spec.ts 增断言（两区块标题、思考默认展开与收起、无思考不渲染、失败标识）。
- 后端 / 接口 / 路由 / 迁移 / 依赖：无。
