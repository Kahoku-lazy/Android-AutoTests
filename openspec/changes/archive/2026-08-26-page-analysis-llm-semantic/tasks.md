## 1. llm_semantic 改纯校验模块（移除 LLM 调用）

- [x] 1.1 重写 `apps/ai_assistant/agent_scope/llm_semantic.py`：删除 `extract()` 与 `generate_structured_output` 调用、`_trim_element` 裁剪，保留 Pydantic 模型 + 新增 `validate_semantic(semantic, input_elements)`（rid 真实性 + metrics 枚举 + 结构清洗），验证 `python manage.py check` 通过
- [x] 1.2 重写 `tests/ai_assistant/test_llm_semantic.py`：删除 extract 假 model 测试，改测 validate_semantic（正常 / 幻觉 rid 置空 / 非法 metrics 剔除），验证 `pytest tests/ai_assistant/test_llm_semantic.py` 全绿

## 2. 移除 model 透传（原方案撤销）

- [x] 2.1 撤销 `agent_factory.py` 的 model 透传（`_build_toolkit` 去掉 model 形参，`build_platform_tools` 去掉 model 实参），验证 `python manage.py check` 通过
- [x] 2.2 撤销 `in_process_tool.py` 的 model 透传（`InProcessPlatformTool.__init__`/`call`/`build_platform_tools` 去掉 model），验证 `python manage.py check` 通过

## 3. analyze_page 改为纯规则 + 新增 save_page_semantic

- [x] 3.1 改 `tool_registry.py` 的 `_inspector_analyze`：删除 `_model` 形参与 `extract` 调用，只 capture + analyze_snapshot 返回纯规则结构，验证 `python manage.py check` 通过
- [x] 3.2 TOOL_SCHEMAS 新增 `save_page_semantic`（module=inspector, action=save_semantic, read_only=False），入参 snapshot_id/page_summary/elements/cards，验证 `python manage.py check` 通过
- [x] 3.3 实现 `@_register("inspector", "save_semantic")` handler：校验 snapshot_id 存在 + validate_semantic 清洗 + 合并返回，验证 `python manage.py check` 通过

## 4. 测试与门禁

- [x] 4.1 新增 `save_page_semantic` handler 单测（校验通过 / 幻觉 rid 置空 / snapshot 不存在报错），验证 `pytest tests/ai_assistant/test_llm_semantic.py` 全绿
- [x] 4.2 全量门禁：`python manage.py check` + `ruff check`（改动文件）+ `pytest tests/ai_assistant/test_llm_semantic.py tests/device_inspector/ tests/algorithms/` + `python tools/gen_arch_stats.py --check-boundaries` 全绿
- [x] 4.3 契约同步：`apps/ai_assistant/AGENTS.md` 更新（去 model 透传说明，补 save_page_semantic 工具）；`ARCH-08-AI助手.md` 工具计数 27→28（+save_page_semantic），验证 `--check-md` 无遗漏
