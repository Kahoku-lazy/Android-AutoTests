# AI 对话主面板 Soft Glass 轻量改版

**日期**: 2026-07-21  
**级别**: 🟢 修补（UI）  
**范围**: `chat-main` 主面板视觉 + 输入区压缩 + 附件按钮图标化

## 目标

把 AI 对话页右侧 `chat-main` 从偏硬的白底木色面板，收成与全局 Soft Glass 一致的轻量玻璃卡片；输入区变矮，附件按钮改用 SVG 字符图标。

## 改动点

1. **ChatView.css — `.chat-main` 区域**
   - 毛玻璃背景、柔和边框、头部压缩
   - 消息区背景改浅色玻璃底，去掉厚重米色块感

2. **ChatInput.vue**
   - `📎` → `IconPaperclip`（项目 SVG 图标库）
   - textarea `rows: 3 → 2`，减小 padding / 字号 / 按钮高度（48→40）
   - 发送按钮同步压缩，与上传按钮对齐

3. **icons/index.js**
   - 复用已有 `IconPaperclip`（若缺失则补齐）

## 非目标

- 不改 SSE / 发送 / 上传业务逻辑
- 不改左侧会话列表布局结构
- 不新增第三方 UI 库

## 验收

- [ ] 附件按钮为 SVG 回形针图标，无 emoji
- [ ] 输入框默认高度明显变矮（约 2 行）
- [ ] `chat-main` 视觉与 Soft Glass token 协调
- [ ] 发送 / 上传 / Enter 行为不变
