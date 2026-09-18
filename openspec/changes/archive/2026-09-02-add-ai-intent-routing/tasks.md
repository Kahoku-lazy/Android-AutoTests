## 1. 数据模型与序列化

- [x] 1.1 在 `apps/ai_assistant/models.py` 的 `AIAgent` 新增 `vision_model_name = models.CharField(max_length=100, default="", blank=True)`，执行 `python manage.py makemigrations ai_assistant` 生成迁移；验证：迁移文件生成且 `python manage.py makemigrations --check` 无未生成迁移
- [x] 1.2 在 `apps/ai_assistant/serializers.py` 的 `AgentInputSerializer` 与 Agent 输出 DTO 增加 `vision_model_name` 字段（与 `model_name` 同规则，`required=False, allow_blank=True`）；验证：`python manage.py check` 通过、`ruff check apps/ai_assistant/serializers.py`

## 2. 意图分类器

- [x] 2.1 新增 `apps/ai_assistant/agent_scope/intent_router.py`：定义 4 类意图的 Prompt（含 few-shot 正反例）+ `classify(pro_model, user_message, history)`，内部用 `await pro_model(messages)`（`__call__`，不强制 tool_choice）取 `TextBlock.text`；验证：模块可 import，`ruff check` 通过
- [x] 2.2 实现容错 JSON 解析 `_tolerant_parse`：正则提取 JSON → 校验 `intent` 枚举白名单（`phone_control/workflow/test_case/other`）→ `confidence` 数值化 → 失败降级 `other`；验证：单测覆盖「合法 JSON / 非 JSON / 幻觉枚举 / 缺字段」四种输入
- [x] 2.3 新增意图→工具白名单常量（`phone_control`→设备/截图工具、`workflow`→页面流/元素工具、`test_case`→用例/执行工具、`other`→空）；验证：白名单内的工具名均存在于 `tool_registry.TOOL_SCHEMAS` 的 name 集合（单测断言）

## 3. 模型路由与工具裁剪

- [x] 3.1 修改 `agent_factory.build_agent` 增加 `intent: str = "other"` 形参，新增 `_INTENT_MODEL` 映射（`phone_control`/`workflow` → `agent_model.vision_model_name or agent_model.model_name`，`test_case`/`other` → `agent_model.model_name`），`_build_model` 按映射后的 model_name 构建；验证：`ruff check` + 单测断言各 intent 选中的 model_name 正确（含未配置 vision 时回退）
- [x] 3.2 修改 `_build_toolkit` 按 intent 白名单过滤平台工具（`other` 不装配任何业务工具）；验证：单测断言 `other` 意图的 toolkit 不含平台工具、`phone_control` 只含设备/截图工具

## 4. 对话流程接入

- [x] 4.1 修改 `chat_views._agent_stream`：在 `build_agent` 前构建 pro 模型并调用 `classify()`，把 intent 传入 `build_agent`；分类失败时降级 `other` 不中断对话；验证：`python manage.py check` + `ruff check`，SSE 对话仍能正常流式返回
- [x] 4.2 处理跨模型上下文：当本轮 intent 为 `test_case`/`other`（文本模型）时，`_restore_context` 恢复历史时裁剪截图 DataBlock（保留文本）；验证：切 pro 后对话历史无大 base64 图片块，token 下降且不报错

## 5. 前端视觉模型配置

- [x] 5.1 在 `frontend/src/modules/ai-assistant/AgentDetail.vue` 增加「视觉模型」下拉框（选项复用 `getModelOptions`，deepseek 列表已含 `deepseek-v4-flash-vision-exp`），提交时带上 `vision_model_name`；验证：`npm run build` 通过 + `vue-frontend-check` 门禁 + 真实页面可保存视觉模型（注：typecheck 无 ai-assistant 错误；`npm run build` 因沙箱 esbuild EPERM 无法运行，需终端自行验证）

## 6. 全链路验证

- [x] 6.1 跑后端门禁：`python manage.py check && ruff check && pytest tests/ai_assistant -m "unit or integration"`，确认无回归；验证：命令全绿
- [x] 6.2 跑架构红线：`python tools/gen_arch_stats.py --check-boundaries`（跨模块 import/写库合规）与 `--check-md`（文档落后检测）；验证：两命令均无新增违规
- [ ] 6.3 端到端手测（≥2 次）：真实对话分别输入「点击涂鸦」（应走视觉模型 + 设备工具）、「新建页面流抓取元素」（应走视觉模型 + 工作流工具）、「测试制冰机功能」（应走文本模型 + 用例工具）、「你好」（应纯对话不调工具）；验证：4 类意图路由正确、SSE 流式正常、截图回显正常
