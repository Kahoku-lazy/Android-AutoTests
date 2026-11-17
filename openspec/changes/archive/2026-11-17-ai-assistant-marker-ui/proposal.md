## Why

`/ai-assistant` 的三处界面（助手颜料片网格、配置弹窗、测试对话页）已按 `ai-assistant-cards` 打通数据与交互，但视觉还停在浏览器默认控件：卡片上的两个动作是原生 `<button>`，配置弹窗是裸 `<label><input>`，对话页是裸输入框加未着色的段落。助手专有笔色只在卡片圆点与发送按钮上出现一次，没有形成「一卡一色」的识别度。

另有一处行为缺口与「卡片显示 Agent 配置的名称」矛盾：卡片上的「配置」打开的是空白新建表单，既没有预填也没有保存修改的调用，改一次配置只能重建一位助手。

本变更把这三处收进已登记的「AI 助手颜料片」专有风格，并补齐配置的编辑往返；不改全站 Doodle Craft，不改后端接口与计费口径。

## What Changes

- 助手页壳改为 `doc-page--fixed` + `WorkbenchHeader` + `.doc-body` + `.doc-section`，与其它模块同骨架；三态用共享件（加载 `SkeletonCard` / 失败 `ErrorState` / 空 `EmptyState`）。
- 颜料片：纸底 + `2.5px dashed` 墨框 + 该助手笔色的 `4px 4px 0` 硬影 + 按序号微倾（`-0.8° / 0.6° / -0.3°`，hover 回正抬起）；名称 16px、中间 88px 头像或笔色深到浅圆、配置名 14px；两个动作改成 30px 手绘小按钮（`1.5px dashed` 墨框、笔色浅底 hover、键盘焦点环）。
- 配置弹窗改 `el-dialog`，表单走主线实线控件（2px 墨框、纸底、2px 圆角、14px label），头像带圆形预览与「移除」；`配置` 打开即预填（名称 / Agent 配置 / 工具域 / 预设 / 头像），`保存` 走 `PATCH /api/ai/assistants/{assistant_id}/`（新增 `updateAssistant`）。
- 对话页保留左栏多对话 + 右栏消息流：页头只留助手名；返回入口移到正文顶部；当前对话栏用**浅蓝填充**标出；「新建对话」用 Teal 键；每个对话栏支持**就地重命名与删除**（后端补 `PATCH .../threads/{id}/` 与 `POST .../threads/{id}/delete/`）；助手气泡用笔色描边、用户气泡保持纸色；发送钮用笔色深到浅渐变；补消息空态与「这一轮还在跑」状态行。
- 笔色令牌仍只在模块 `tokens.css`；渐变与浅底由组件内 `color-mix` 现算，不新增全局令牌，不改 `shared/styles/tokens.css`。
- 登记进 doodle-craft：扩写 `references/components/assistant-marker-card.md`（卡片 / 配置弹窗 / 对话页三段规格 + 反模式），在 `SKILL.md` 组件目录补一行，便于后续复用。

## Capabilities

### Modified Capabilities

- `ai-assistant-marker-style`: 从「卡片一处笔色」扩到「卡片 + 配置弹窗 + 对话页」三处一致的落位，并写清渐变、虚线、浅底的允许范围。
- `ai-assistant-card`: 卡片动作与配置弹窗的视觉规格；新增「配置打开即编辑并预填、保存回写」的行为要求。
- `ai-assistant-test-chat`: 对话页版式与笔色落位（页头、左栏、气泡、发送钮、空态），交互（多栏、发送才进行中、取消只停当前栏）不变。

## 关联文档

- `.agents/skills/doodle-craft/references/components/assistant-marker-card.md`（本变更扩写）
- StyleKit `hand-drawn-doodle` 的 Five Marker Colors（卡片一卡一色、微倾、硬偏移阴影）

## Impact

- 前端：`frontend/src/modules/ai-assistant/` 的 `index.vue`、`chat.vue`、`components/AssistantCard.vue`、`components/AssistantEditor.vue`、`tokens.css`、`api/assistants.ts`，新增 `helpers/` 与 `components/AssistantLanePanel.vue`。
- 后端：`ai_assistant` 补对话栏重命名（`PATCH .../threads/{id}/`）与删除记录（`POST .../threads/{id}/delete/`）；取消仍走 `DELETE .../threads/{id}/`，既有语义不变。
- 技能：doodle-craft 的 `SKILL.md` 与 `references/components/assistant-marker-card.md`。
- 不触碰：全站 `tokens.css`、`sketched-kit.css`、其它模块的虚线白名单、SOP、钱与配额口径。
