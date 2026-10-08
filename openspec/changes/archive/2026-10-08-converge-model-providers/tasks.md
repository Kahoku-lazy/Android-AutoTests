## 1. 后端：provider 真相源收缩

- [x] 1.1 `apps/ai_assistant/provider_registry.py`：`PROVIDER_DEFAULTS` 只保留 `dashscope` 与 `deepseek`；`_PROVIDER_HOSTS` 同步删除 `openai` / `anthropic` / `gemini`；`validate_base_url()` 删除 `provider == "custom"` 的任意主机放行特例（保留"禁止本机地址"与白名单校验）。验证：`VALID_PROVIDERS == {"dashscope", "deepseek"}`，且对 `openai` 的 base_url 校验因 provider 不在白名单而拒绝。**验证结果**：映射表与白名单均只剩两项（`VALID_PROVIDERS = frozenset(PROVIDER_DEFAULTS)` 自动跟随）；`custom` 特例已删；一致性用例 `test_supported_providers_match_valid_providers` 通过（引擎集合 == Django 集合 == 两项）。
- [x] 1.2 `get_provider_config()` 的兜底键改为不依赖 `custom`（原 `PROVIDER_DEFAULTS["custom"]` 在删除后会 `KeyError`）。验证：`get_provider_config("deepseek")` 返回默认地址；对未知 provider 不抛异常、也不静默返回其它 provider 的地址（由上游校验拦截）。新增/更新用例覆盖。**验证结果**：兜底改为 `PROVIDER_DEFAULTS.get(provider, "")`——不再抛 `KeyError`，也不会把未知 provider 静默解析成别的端点地址；未知 provider 仍由装配层与序列化层的 `VALID_PROVIDERS` 校验拦下并报错（`test_unknown_provider_rejected_at_assembly` 覆盖文案含合法集合）。
- [x] 1.3 `models/constants.py` 的 `ModelProvider` 枚举同步为 `DASHSCOPE` / `DEEPSEEK`（该枚举当前零消费，只做与实现对齐；不动基类与枚举数量）。验证：`models/` 枚举门禁用例（数量下限 + StrEnum 基类）全绿。**验证结果**：`tests/graybox/unit/test_ssot_enum_strenum.py` 4 项全绿（枚举数量与基类门禁未受影响）；全仓 `ModelProvider.OPENAI/ANTHROPIC/CUSTOM` 零引用（本就零消费）。

## 2. 引擎：支持集合与分支

- [x] 2.1 `engines/ai/agents/base.py`：删除 `OPENAI_COMPATIBLE_PROVIDERS` 与 `config.provider in OPENAI_COMPATIBLE_PROVIDERS` 分支；`SUPPORTED_PROVIDERS = frozenset({"deepseek", "dashscope"})`；**保留** `provider == "deepseek"` 且 `vision=True` 时使用 `OpenAIChatModel` + `OpenAICredential` 的实现（该链路是多模态档的实现方式，与"openai provider"无关）。验证：`deepseek + vision` 仍能构造模型；`openai`/`anthropic`/`gemini`/`custom` 一律抛 `ConfigurationError` 且错误文案列出合法集合。**验证结果**：新增参数化用例 `test_removed_providers_are_rejected`（4 个已移除 provider 逐一断言抛 `ConfigurationError` 且文案含该名）；既有 `test_deepseek_vision_constructs`（多模态档）与 `test_all_supported_providers_construct`（两项各自构造）全绿。**过程记录**：本次首次编辑误把兼容分支复制成 4 份，靠上一单新增的未定义名检查（F821）与随后的导入用例当场发现并改正——守卫生效。
- [x] 2.2 `tools/register_agentscope_agents.py`：两处默认 provider 由 `"custom"` 改为 `"deepseek"`。验证：脚本内不再出现 `"custom"`。**验证结果**：两处均已改为 `deepseek`；代码域复扫 `"custom"` 零命中。

## 3. 前端：清单收敛

- [x] 3.1 `frontend/src/modules/ai-assistant/components/ModelConfigField.vue`：providers 只保留 阿里百炼 (DashScope) 与 DeepSeek（删除 OpenAI / Anthropic (Claude) / 自定义）。验证：用例断言清单恰为这两个 `value`。**验证结果**：清单恰为 `dashscope` + `deepseek`；**新增对拍用例** `test_frontend_provider_list_matches_backend_valid_providers` 断言「前端清单 ≡ 后端合法集合」（含规模下限与"未定位到清单即失败"），把"界面不给选、接口仍能配"这类不一致从此钉死。
- [x] 3.2 **对拍用例换锚点**：`tests/graybox/unit/test_ai_deepseek_model_catalog.py` 现用 `value: "custom"` 作为 DeepSeek 段落结束锚点，`custom` 删除后会失配 → 改为不依赖任何将被删除 provider 的界定方式，并保留规模下限与"未定位到清单即失败"的断言。验证：用例通过；把前端清单多写一个模型名会红。**验证结果**：锚点改为「从 `value: "deepseek"` 到数组结尾 `]`」，不再依赖任何 provider；9 项全绿（含规模下限 `MIN_MODELS` 与定位失败断言）。

## 4. 规格与文档

- [x] 4.1 规格 delta（`ai-engine-protocol` 的 provider 需求，MODIFIED 含全部原场景）：删去"OpenAI 兼容白名单"措辞，明确支持的 provider 恰为 DeepSeek 与阿里百炼、集合外一律报错且无任何兼容兜底。验证：`openspec validate`（含归档时并入主规格）通过。**验证结果**：`openspec validate --strict` 通过；归档时 delta 并入主规格（原始 4 个场景全部保留，其中"兜底分支不再吸收未知 provider"改写为"已移除的 provider 不再被接受"）。
- [x] 4.2 `dev_docs/DEV_TEST/接口文档/API-AI助手.md` 的"提供商枚举"列举改为 `dashscope/deepseek`。验证：文档中不再列举已移除的 provider。**验证结果**：枚举行改为「dashscope/deepseek（平台只支持这两项）」；同文档的 base_url 白名单错误说明里"非 custom 且主机不符"也一并改为「主机与所配 provider 不符」；另清掉引擎内 3 处把已移除 provider 当示例的措辞（模块 docstring、`ModelConfig` 注释、`model_supports_image` 注释）。

## 5. 验证与归档

- [x] 5.1 后端自检与静态检查：`python manage.py check` + 门禁范围 `ruff check` / `ruff format --check`。验证：全部通过。**验证结果**：`System check identified no issues (0 silenced)`；`ruff check apps/ config/ gateway/ shared/ models/ engines/` → All checks passed；改动文件 `ruff format --check` → 6 files already formatted。
- [x] 5.2 相关用例最小集：`test_ai_engine_config.py` + `test_ai_deepseek_model_catalog.py` + `test_ai_role_tool_subsets.py` + `test_ai_debug_assembly_entry.py` + `tests/arch/test_channels.py` + `test_ssot_enum_strenum.py`。验证：全部通过（不发起全量回归）。**验证结果**：**48 passed**（30.69s；其中模型目录对拍与计费用例另轮 48 项亦全绿）。
- [x] 5.3 前端门禁（按文件）：`npx prettier --check` / `npx eslint` 改动文件 + `npm run typecheck` + 相关 vitest 用例。验证：全部通过。**验证结果**：prettier → All matched files use Prettier code style；eslint → 零告警；vue-tsc → 无错误；`npx vitest run tests/ai-assistant/p0/model-config-field.spec.ts` → 2 passed。
- [x] 5.4 边界检查：`python tools/gen_arch_stats.py --check-boundaries`。验证：零违规。**验证结果**：`✅ 模块边界检查通过 — 零违规`。
- [x] 5.5 全仓复扫已移除 provider：确认仅出现在允许处（历史归档 / 测试反例 / 本变更文档）。验证：逐处核对通过。**验证结果**：代码域复扫（apps / models / tools / engines 非技能代码）命中项逐处核对——`OpenAIError`（SDK 异常类名，保留）、`OpenAICredential`/`OpenAIChatModel`（DeepSeek 多模态档实现，保留）、说明性注释与"已移除 provider 被拒"的用例参数（有意保留）；另修掉 3 处把已移除 provider 当示例的措辞。`docs/openspec 归档/外观技能文档` 里的命中属历史记录，未改。
- [x] 5.6 关单与归档：汇总改动清单与用例结果；`openspec validate` 通过后归档（delta 并入 `ai-engine-protocol`）。验证：`openspec validate "2026-10-08-converge-model-providers"` 通过并完成归档。**验证结果**：改动清单 = 后端 2 文件（provider_registry、models/constants）+ 引擎 2 文件（base、config 注释）+ 工具脚本 1 + 前端 1 + 测试 2 + 文档 1；`openspec validate --strict` 通过；已归档（delta 并入 `ai-engine-protocol`）。
