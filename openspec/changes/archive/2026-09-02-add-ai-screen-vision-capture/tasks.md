## 1. 后端：工具 schema 与 handler

- [x] 1.1 在 `tool_registry.py` 新增 `screenshot_page` schema（设备检查器分类、只读、参数 serial + method 可选）并注册 handler：调 `device_inspector.api.capture_snapshot` 取 `screenshot_path`，按 `Path(settings.MEDIA_ROOT)/screenshot_path` 读文件转 base64，返回图片 + 摘要。验证：`python manage.py check && ruff check apps/ai_assistant/agent_scope/tool_registry.py`
- [x] 1.2 扩展 `in_process_tool.py` 结果格式化：支持 handler 返回图片标记 → 构造 `ToolChunk([TextBlock, DataBlock(Base64Source)])`。验证：`pytest apps/ai_assistant -k tool`

## 2. 后端：持久化与上下文还原

- [x] 2.1 扩展 `chat_views._dicts_to_blocks`：将 `tool_result.output` 列表内 text/data 字典还原为 `TextBlock`/`DataBlock`，使视觉模型后续轮次可引用截图。验证：`pytest apps/ai_assistant/tests.py`

## 3. 前端：工具结果图片渲染

- [x] 3.1 `ToolCallCard.vue` 渲染 `tool_result.data`（base64）→ data URI 图片（`el-image` + `preview-src-list`）。验证：`npm run build` + `vue-frontend-check`
- [ ] 3.2 历史消息加载路径确认 `tool_result.data` 图片正常展示。验证：真实页面重开含截图的对话

## 4. 全链路验证与门禁

- [ ] 4.1 真实视觉模型（`deepseek-v4-flash-vision-exp`，平台内自动走 openai formatter）+ 在线设备端到端：让 AI「查看当前页面」，确认模型基于像素作答且对话回显截图。验证：人工 E2E
- [x] 4.2 `python tools/gen_arch_stats.py --check-boundaries` 通过（跨模块写/import 合规）。验证：命令 0 违规
