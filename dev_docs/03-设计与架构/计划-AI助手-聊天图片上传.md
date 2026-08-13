# 聊天图片上传 Implementation Plan

> **For agentic workers:** Execute task-by-task. Steps use checkbox syntax.

**Goal:** 聊天输入区增加图片上传；多模态发给模型；用户气泡展示图片。

**Architecture:** 扩展 `/upload-file` 返回 base64；`/chat/stream` 接收 `images`；`UserMsg` 用 TextBlock+DataBlock；用户消息 `blocks` 持久化供展示与上下文恢复。

**Tech Stack:** Django + AgentScope (`DataBlock`/`Base64Source`) + Vue 3 ChatInput/MessageBubble/useSSE

## Global Constraints

- 单图；与文件附件互斥；png/jpg/jpeg/webp/gif；图片 ≤5MB
- 无图时行为与现网一致
- 不新增模型视觉白名单

---

### Task 1: Backend upload image branch
- [ ] `file_views.py`：IMAGE_EXTENSIONS + 5MB；返回 data_uri/media_type

### Task 2: Backend chat stream multimodal
- [ ] `chat_views.py`：解析 images；save blocks；多模态 UserMsg；`_restore_context` + `_dicts_to_blocks`
- [ ] `api.save_message` / serializers：user 可带 blocks；空文本+图通过

### Task 3: Frontend input + send + bubble
- [ ] ChatInput 图片按钮与预览
- [ ] ChatView pendingImage / 互斥 / 发送
- [ ] useSSE 传 images；占位消息带 blocks
- [ ] MessageBubble 渲染 image；types/normalizer

### Task 4: Verify
- [ ] 关键检查；无图回归路径目视确认
