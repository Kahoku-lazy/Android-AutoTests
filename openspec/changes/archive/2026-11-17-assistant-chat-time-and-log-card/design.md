## Context

`ai_assistant_messages` 已有 `created_at`，但 `GET /ai/assistants/threads/<id>/` 只回 `role` 与 `content`，前端 `ThreadMessage` 也就没有时间字段。日志接口 `list_thread_logs` 回的是 Django `DateTime` 对象，经 DRF 渲染成默认 ISO（带 `Z` 或 `+00:00`，取决于时区设置），而卡片时间目前是从报告编号（`YYYYMMDD_HHMMSS`）反推的。

日志 UI 目前是一个 `max-width: 72ch` 的实线面板 + 行列表。需求方给了手绘风格参考图（虚线外框 + 顶部胶带 + 偏移阴影），并要求**日志记录卡片**照此做、**不要倾斜**、**要时间戳**；对话气泡同样要时间戳。

## Goals / Non-Goals

**Goals:**

- 每条消息、每一轮日志都能在页面上读到"什么时候"。
- 日志一轮一张卡，卡片观感对齐参考图（虚线 + 胶带 + 偏移阴影），且不倾斜。
- 时间只有一个来源：消息的 `created_at`；编号解析只做缺省回落。

**Non-Goals:**

- 不做时区切换 / 用户偏好；平台是单时区（Asia/Shanghai）。
- 不改报告 HTML 本身，不改日志文件命名。
- 不给其它模块的气泡、卡片加虚线（准入清单只多一个文件）。

## Decisions

### 1. 时间由后端给，前端只取墙上时间

service 统一输出 `timezone.localtime(...).isoformat()`（带 `+08:00`）；前端 helper `clockLabel(iso)` 直接从 ISO 里取 `HH:mm`，**不做时区换算**。理由：平台单时区，换算只会在浏览器时区不同时把已有时间显示错；单测也不需要依赖运行机器时区。

### 2. 一个时间来源，编号只做回落

日志卡时间 = 该轮助手消息的 `created_at`；只有老数据缺 `created_at` 时才回落到报告编号里的 `YYYYMMDD_HHMMSS`（`MM-DD HH:mm`）。进行中的一轮还没有消息时间，卡片只显示「还在写」。

### 3. 一轮一张虚线卡，面板退成容器

卡片是有边界的实体：`1.5px dashed color-mix(笔色 70%, 纸色)` + 顶部居中胶带（笔色 26% 纸色，`top: -8px`）+ `4px 4px 0 0 color-mix(笔色 26%, transparent)` 硬影 + `--app-radius-md` + 白卡底；**0° 不倾斜**（需求方明确）。面板本身去掉描边，只留标题行（`运行日志 N 轮` + `收起`）与列表。

### 4. 虚线准入清单 +1 个文件

`ThreadLogPanel.vue` 登记进 `check-dashed-whitelist.mjs` 的 OWNERS，同时改模块 `AGENTS.md` 的线型条款与 doodle-craft 技能表。这是需求方确认过的准入清单变更（2026-11-16），影响面仅对话页日志卡；回退 = 卡片改回实线并同步撤掉三处登记。

### 5. 日志卡住左栏，展开时只加宽左栏

日志卡放在左栏、对话栏下面（`AssistantLanePanel` 开默认插槽，左栏是 flex 列）。日志展开时 `.ai-chat__body.is-logs-open` 把左栏 `240px → clamp(320px, 30%, 420px)`，聊天列等量收窄；收起回 `240px` 并卸载日志卡。

理由：消息只占 `72ch`，对话列 1010px 时右侧会空出一大片（用户截图红框）；把日志放进这段空间、同时把对话列压到 ~870（1582 视口），空白从 420px 收到约 280px，且日志与「这一栏」同列、不再把消息往下顶。不选「对话区内展开」是因为它只解决遮挡、不解决空白；不选「右侧第三栏」是因为会把左栏对话栏与日志拆到页面两端。

## 模块防火墙自检

- 写库仍只在 `services/assistant_threads.py`；view 继续只做分发（消息行整理走 service 的 `message_rows`）。
- 时间字段只经助手接口出，前端不拼磁盘路径。
- 不新增跨模块依赖；虚线只落在 `modules/ai-assistant`。

## Risks / Trade-offs

- [浏览器时区与服务端不一致] → 卡片与气泡显示的是"服务端本地时刻"；跨时区使用时显示的是平台时间，不是用户本地时间。单时区平台可接受，若要跨区需另立"用户时区"变更。
- [卡多时阴影叠加] → 每条卡 `4px` 硬影，日志多时视觉偏重；用 `gap: var(--app-space-md)` 与浅色阴影（笔色 26%）控制。
- [虚线扩散] → OWNERS 白名单按文件判定，其它文件出现 `dashed` 仍直接 exit 1。
