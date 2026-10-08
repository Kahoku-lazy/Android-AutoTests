## 1. 引擎侧：模型目录、装配提醒、价目

- [x] 1.1 `engines/ai/agents/config.py` 新增 DeepSeek 模型目录常量（正式模型名 → 是否支持图片输入：`deepseek-flash` = 支持、`deepseek-v4-pro` = 不支持）与能力判断函数 `model_supports_image(provider, model_name) -> bool | None`（未知返回 `None`）；注释写明依据来自 `GET /v1/models` 的 `input_modalities` 与官方价目页。验证：`python -c "..."` 输出支持 / 不支持 / `None`。**验证结果**：目录 `{deepseek-flash: True, deepseek-v4-pro: False}`；`model_supports_image` 对 deepseek 两模型返回 True/False，对 `deepseek-v4-flash`（旧名不在目录）、`dashscope`、空名一律返回 `None`（用例 `test_model_supports_image_only_knows_catalog` 覆盖）。
- [x] 1.2 `engines/ai/agents/base.py` 的 `AgentRole._assemble`：当 `spec.vision` 为真且 `model_supports_image(...)` 明确为 `False` 时，记一条含**角色名 + 模型名**的 `logger.warning`；不抛错、不阻断装配。验证：新增用例断言"视觉角色 + 纯文本模型"会触发告警、且装配仍成功。**验证结果**：用例 `test_vision_role_bound_to_text_only_model_logs_warning` 断言告警含 `装配提醒` + `executor` + `deepseek-v4-pro` 且角色对象仍构造成功；反例用例 `test_no_warning_for_matching_or_unknown_models` 覆盖「多模态模型 / 非视觉角色 / 未知模型名」三种情形均**不告警**。
- [x] 1.3 `engines/ai/billing/billing.py`：价目收敛为两个正式条目（`deepseek-flash` = 命中 0.02 / 未命中 1 / 输出 4；`deepseek-v4-pro` = 0.15 / 4.5 / 13.5）；`_DEEPSEEK_MODEL_ALIASES` 把 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp`、`deepseek-chat` 指向 `deepseek-flash`，`deepseek-reasoner` → `deepseek-v4-pro`；`_DEFAULT_DEEPSEEK_MODEL` = `deepseek-flash`。验证：`_resolve_price("deepseek-v4-flash-vision-exp") == _resolve_price("deepseek-flash")`，且目录键全部命中正式条目。**验证结果**：价目解析断言（`_resolve_price(name) is DEEPSEEK_PRICING[name]`，证明非默认档兜底）与目录⊆价目用例均通过；旧名与正式名同价由 `test_legacy_flash_names_bill_at_flash_rate` 覆盖。

## 2. 后端侧同步

- [x] 2.1 `apps/ai_assistant/deepseek_billing.py`：与 1.3 逐键一致的同样改动（价目 / 别名 / 默认档）。验证：新增用例断言两份价目表逐键相等（含别名映射与默认档）。**验证结果**：`test_two_price_tables_are_identical` 断言价目、别名、默认档、高峰倍率四项两侧完全相同 → 通过。
- [x] 2.2 `tools/register_agentscope_agents.py` 的默认模型名由 `deepseek-v4-flash` 改为 `deepseek-flash`。验证：`grep` 正式清单无旧名残留。**验证结果**：`grep -n "deepseek-v4-flash" tools/ apps/ engines/` → 仅剩 `apps/ai_assistant/deepseek_billing.py` 与 `engines/ai/billing/billing.py` 的**别名映射表**、以及 `engines/ai/agents/config.py` 的注释说明（均为有意保留）；正式清单与默认档已无旧名。
- [x] 2.3 文档与注释同步：接口文档计价说明、引擎内模型名示例注释改为正式名。验证：文档中不再以旧名作为当前模型示例。**验证结果**：`API-AI助手.md` 计价说明改为「无分模型用量时按 `deepseek-flash` 计费；旧名按厂商口径折算到 `deepseek-flash`」；`ModelConfigField` 与引擎目录注释中的示例名同步为 `deepseek-flash`。（`API-仪表盘.md` 的示例 `deepseek-v4-pro` 仍是有效模型，未改。）

## 3. 前端：能力标注与提醒

- [x] 3.1 前端模型清单改为两个正式模型并逐项标注能力；新增布尔入参「本角色是否需要图片」，为真时显示固定提示「本角色需要多模态模型（可读截图）」。验证：相关用例断言清单与标注。**验证结果**：清单改为 `deepseek-flash`（多模态 · 支持图片）/ `deepseek-v4-pro`（纯文本）；判定逻辑按仓库规范下沉到纯函数 `helpers/model-capability.ts`（`modelOptionLabel` / `isKnownTextOnly`），新增用例 `model-capability.spec.ts`（2 项）通过；选中已知纯文本模型时提示文案升级为告警措辞。
- [x] 3.2 调用方 `AgentRouteConfig.vue`：为执行模型与验收模型两个区块传「需要图片」，规划区块不传。验证：用例断言规划区块无该提示。**验证结果**：执行 / 校验（验收）两个 `ModelConfigField` 带 `needs-image`，规划区块不带；「不需要图片则 `isKnownTextOnly` 结果不影响渲染」由 `needsImage` 短路保证，纯函数用例覆盖判定边界。
- [x] 3.3 前端类型与门禁：`npm run typecheck` 通过；本次涉及的前端用例按文件跑通，不发起全量前端测试。**验证结果**：`npm run typecheck`（vue-tsc --noEmit）无错误；`npx eslint` 三个改动文件零告警；`npx vitest run tests/ai-assistant/p0/model-capability.spec.ts` → **2 passed**（单文件，非全量）。

## 4. 一致性守护用例

- [x] 4.1 新增「前端清单 ≡ 引擎目录」对拍用例（读源码范式）：从 `ModelConfigField.vue` 解析出 deepseek 清单，断言与 `DEEPSEEK_MODELS` 键集合相等；登记扫描量下限防规则退化。验证：用例通过；任一侧多写一个模型名会红。**验证结果**：`test_frontend_list_matches_engine_catalog` + `test_frontend_multimodal_flags_match_engine_catalog` 通过（含 `MIN_MODELS = 2` 下限、正则失配即报"未定位清单"）；能力位也与引擎目录逐项相等。
- [x] 4.2 新增「目录 ⊆ 价目表正式条目」与「两份价目表逐键相等」用例。验证：用例通过；删掉一个价目条目会红。**验证结果**：`test_every_catalog_model_hits_formal_price_entry`（并用 `is` 断言解析不是默认档兜底）、`test_legacy_names_alias_to_a_formal_model`、`test_two_price_tables_are_identical` 全部通过。
- [x] 4.3 更新既有用例：`test_deepseek_billing.py` 期望值随官方新价重算；以旧模型名作桩且语义代表"当前模型"的用例改为正式名。验证：改动涉及的单元测试全绿。**验证结果**：flash 价改为 0.02 / 1 / 4、模型名改 `deepseek-flash`，并新增「旧名按 Flash 计费」断言；4 项全绿。其余以 `deepseek-v4-flash` / `deepseek-chat` 作**桩数据**的用例语义上不依赖价目（如 provider 分支、装配契约），保持原样即通过（48 项验收集全绿）。

## 5. 验证与归档

- [x] 5.1 后端自检与静态检查：`python manage.py check` + 门禁范围 `ruff check` + `ruff format --check`。验证：全部通过。**验证结果**：`System check identified no issues (0 silenced)`；门禁范围 `ruff check`（含两个改动测试文件）→ All checks passed。
- [x] 5.2 边界检查：`python tools/gen_arch_stats.py --check-boundaries`。验证：零违规。**验证结果**：`✅ 模块边界检查通过 — 零违规`。
- [x] 5.3 相关用例最小集：本次改动的用例文件 + `test_deepseek_billing.py` + `test_ai_engine_config.py` + `test_ai_role_tool_subsets.py` + `test_ai_debug_assembly_entry.py` + `tests/arch/test_channels.py -q`。验证：全部通过（不发起全量回归）。**验证结果**：**48 passed**（13.12s）。
- [x] 5.4 端到端实证（不需要设备）：用平台密钥再问一次 `/v1/models`，确认平台清单与 API 实际返回的 id 集合一致。验证：两侧集合相等。**验证结果**：实测 `API: {deepseek-flash: True, deepseek-v4-pro: False}` ≡ `平台目录: {deepseek-flash: True, deepseek-v4-pro: False}`，**一致 = True**（能力位也一致，取自 `input_modalities`）。
- [x] 5.5 关单与归档：汇总改动清单、守护用例结果、费用重算影响面；`openspec validate` 通过后归档（delta 并入 `ai-agent-model-config`）。验证：`openspec validate "2026-10-08-sync-deepseek-models"` 通过并完成归档。**验证结果**：改动清单 = 引擎 3 文件（目录/告警/价目）+ 后端 1 文件 + 工具脚本 1 处 + 前端 3 文件（组件×2 + 新 helper）+ 前端用例 1 + 后端用例 2（新增 1、更新 1）+ 接口文档 1 处；`openspec validate --strict` 通过；已归档（delta 并入主规格）。
