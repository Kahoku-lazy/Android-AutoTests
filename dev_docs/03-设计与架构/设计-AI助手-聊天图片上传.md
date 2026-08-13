# 聊天图片上传与多模态发送 — 设计文档

日期：2026-08-10  
状态：已实现（2026-08-10）  
范围：AI 助手对话页（`frontend/src/modules/ai-assistant` + `apps/ai_assistant`）  
说明：`docs/` 被 gitignore，规格放在 `dev_docs/03-设计与架构/`

## 1. 目标

在聊天输入区增加独立「图片上传」能力：

1. 用户可选一张图片并在发送前预览；
2. 发送时以 AgentScope 多模态 `UserMsg`（`TextBlock` + `DataBlock(Base64Source)`）交给模型；
3. 用户气泡中展示该图片（即时发送与历史回放一致）。

非目标：多图、图+文件同时附件、模型视觉能力白名单拦截、图片 OCR。

## 2. 现状

| 环节 | 现状 |
|------|------|
| 输入区 | 仅回形针文件上传（txt/md/docx/xlsx/pdf 等），解析为文本后拼进消息 |
| 上传 API | `POST /api/ai/upload-file` 仅允许文档扩展名，返回 `content` 文本 |
| 流式聊天 | `POST .../chat/stream` body 仅 `{"message": string}`；`UserMsg(content=str)` |
| 用户消息入库 | 只存 `content` 字符串，不写 `blocks` |
| 气泡 | `MessageBubble` 对用户消息只渲染文本 |

AgentScope 已支持：

```python
UserMsg(name=..., content=[
    TextBlock(text="..."),
    DataBlock(source=Base64Source(data="...", media_type="image/png")),
])
```

## 3. 方案（已选：方案 1）

独立图片按钮 + base64 多模态 + 用户 `blocks` 持久化图片，用于展示与上下文恢复。

## 4. 交互设计

### 4.1 输入区

- 保留现有文件上传按钮（回形针），文案/title 明确为文件上传。
- 在其右侧新增图片上传按钮（图标区分，如图片框），`accept="image/png,image/jpeg,image/webp,image/gif"`。
- 选中图片后：输入区上方显示缩略图预览 + 文件名/大小 + 移除按钮。
- **互斥**：已有文件附件时再选图片 → 替换为图片（并提示）；反之亦然。同一时刻最多一种附件、一张图。
- 发送条件：有文本 **或** 有文件 **或** 有图片，且未在发送中。

### 4.2 对话框

- 用户消息气泡：若 `blocks` 含 `type: "image"`（或等价 data/image 结构），在文本上方/下方渲染缩略图。
- 点击缩略图可放大查看（Element Plus `el-image` preview 或等价）。
- 历史加载与即时发送共用同一套 `blocks` 渲染路径。

## 5. 数据流

```
选图 → POST /ai/upload-file (image)
     → { status, data: { filename, size, type, data_uri, media_type } }
     → 前端 pendingImage 预览

发送 → POST .../chat/stream
     body: {
       message: "<用户文本，可为空>",
       images?: [{ media_type, data }]   // data 为纯 base64，无 data: 前缀
     }
     → 后端：空文本+有图 → content 存 "[图片]"；写入 blocks
     → UserMsg([TextBlock?, DataBlock...])；无图则仍为纯字符串
     → SSE 流式回复（与现网一致）

前端气泡 → append 用户消息时带上 blocks（用 data_uri 立刻显示）
历史 → messages 返回 user.blocks → MessageBubble 渲染
```

## 6. API 契约

### 6.1 `POST /api/ai/upload-file`（扩展）

**新增允许扩展名**：`png` | `jpg` | `jpeg` | `webp` | `gif`  
**图片大小上限**：5MB（文档仍为现有 20MB）。

图片成功响应：

```json
{
  "status": true,
  "data": {
    "filename": "shot.png",
    "size": 12345,
    "type": "png",
    "media_type": "image/png",
    "data_uri": "data:image/png;base64,...."
  }
}
```

不返回 `content` 文本字段（或为空）。文档类型响应保持不变。

### 6.2 `POST /api/ai/conversations/{id}/chat/stream`（扩展）

```json
{
  "message": "这张图里有什么？",
  "images": [
    { "media_type": "image/png", "data": "<base64>" }
  ]
}
```

校验规则：

- `message` 与 `images` 至少一个有效：无图时 `message` 非空（现有行为）；有图时 `message` 可为空，后端存库用 `"[图片]"` 占位。
- `images` 最多 1 项；`media_type` 必须是允许的 image MIME；`data` 为可解码 base64；解码后体积 ≤ 5MB。
- 无 `images` 时行为与现网完全一致。

用户消息入库：

| 字段 | 值 |
|------|-----|
| `content` | 用户文本；空则 `"[图片]"` |
| `blocks` | `[{ "type": "text", "text": "..." }, { "type": "image", "source": { "type": "base64", "media_type": "...", "data": "..." } }]`；无文本时可不含 text block，仅 image |
| `flow` | `sse`（与现网一致） |

### 6.3 历史消息 API

现有 messages 列表已返回 `blocks` 字段；确认用户消息的 `blocks` 一并序列化给前端（若当前仅 assistant 有值，需保证 user 也透出）。

## 7. 后端实现要点

| 文件 | 改动 |
|------|------|
| `views/file_views.py` | 图片扩展名分支：读文件 → base64 → 返回 `data_uri`/`media_type`；校验 5MB |
| `views/chat_views.py` | 解析 `images`；`save_message` 写入 blocks；构造多模态 `UserMsg` |
| `views/chat_views.py` `_restore_context` | user 消息若 `blocks` 含 image，重建 `TextBlock`/`DataBlock`，而非纯字符串 |
| `api.save_message` / serializers | 允许 user 带 `blocks`；空文本+有图时通过校验 |
| `_dicts_to_blocks` | 支持 `type: "image"` → `DataBlock(Base64Source(...))`（与 AgentScope 存储形态对齐） |

AgentScope 构造示例：

```python
blocks = []
if text:
    blocks.append(TextBlock(text=text))
for img in images:
    blocks.append(DataBlock(source=Base64Source(data=img["data"], media_type=img["media_type"])))
next_input = UserMsg(name=user_id, content=blocks if images else text)
```

无图时继续 `UserMsg(..., content=user_message)`，避免无谓改变格式器路径。

## 8. 前端实现要点

| 文件 | 改动 |
|------|------|
| `components/ChatInput.vue` | 文件按钮 title 标明文件；新增图片按钮 + hidden input；预览区区分文件/图片 |
| `ChatView.vue` | `pendingImage` 状态；上传/移除/发送时组装 `images`；与文件互斥 |
| `composables/useSSE.ts` | `sendStreamMessage` 增加可选 `images`，写入请求 body；占位用户消息带 `blocks` |
| `api/conversations.ts` / agents upload | 类型补充 |
| `components/MessageBubble.vue` | 用户消息渲染 image block 缩略图 |
| `helpers/message-normalizer.ts` | 规范化 user blocks 中的 image |
| `shared/types/ai.ts` | `ChatMessage.blocks` / image block 类型 |

按钮视觉：与现有 `upload-btn` 同尺寸，沿用模块既有边框/hover，不新开设计语言。

## 9. 错误处理

| 场景 | 行为 |
|------|------|
| 非图片类型 / 超 5MB | 上传接口 400，前端 `ElMessage.error` |
| base64 损坏 | stream 接口 400 |
| 模型不支持视觉 | 不前端拦截；错误经现有 SSE error / 消息提示路径 |
| 上传中点击发送 | 按钮 disabled（与文件上传一致） |

## 10. 验收标准

1. 输入区可见「文件上传」与「图片上传」两个入口。
2. 选 png/jpg/webp/gif（≤5MB）可预览；可取消；与文件附件互斥。
3. 仅图 / 图+文字均可发送；模型侧收到多模态 `UserMsg`。
4. 发送后用户气泡立即显示缩略图；刷新对话后仍显示。
5. 无图时现有纯文本与文件上传行为回归不变。

## 11. 测试建议

- 后端：图片上传成功/超限/非法扩展名；stream 带图保存 blocks；`_restore_context` 重建 DataBlock。
- 前端：预览、互斥、气泡渲染、历史回放。
- 手工：对接实际视觉模型发一张图提问，确认回复与图相关。

## 12. 风险与约束

- base64 入库会增大 `ai_messages.blocks`；单图 5MB 上限控制体积。
- 上下文恢复会把历史图片再次喂给模型，长对话可能触达供应商 token/大小限制；本版不裁剪历史图，若后续有问题再加「仅最近 N 条带图」策略。
