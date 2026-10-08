# 设计：模型服务收敛为 DeepSeek 与阿里百炼

## Context

- 现状清单：前端 `ModelConfigField.vue` 列 5 项（阿里百炼 / DeepSeek / OpenAI / Anthropic / 自定义）；后端 `provider_registry.PROVIDER_DEFAULTS` 与 `_PROVIDER_HOSTS` 各 6 项（多 Gemini）；引擎 `SUPPORTED_PROVIDERS = {deepseek, dashscope} | {openai, anthropic, gemini, custom}`。
- 一致性守护：`test_ai_engine_config.py` 断言「引擎可处理集合 == Django 合法集合」，并另有「OpenAI 兼容白名单 ⊆ 支持集合」的断言；`VALID_PROVIDERS = frozenset(PROVIDER_DEFAULTS)` 是 Django 侧唯一真相源（装配层 `engine_adapter` 与 `serializers` 都引用它）。
- 存量实测：库里唯一智能体（#10）三角色全为 `deepseek`，无任何其它 provider；线路键仅 `device_control`。
- 连带点（实测确认）：`provider_registry.get_provider_config()` 用 `PROVIDER_DEFAULTS["custom"]` 作兜底键（删 `custom` 会 `KeyError`）；`validate_base_url()` 有 `provider == "custom"` 的任意主机放行特例；`tools/register_agentscope_agents.py` 两处默认 `"custom"`；前端对拍用例用 `value: "custom"` 作段落结束锚点。
- 用户已定：**三层一起收敛**；**`custom` 一并去掉**。

## Goals / Non-Goals

**Goals:**

- 平台支持的 provider 恰为 `{deepseek, dashscope}`，界面、后端合法集合、引擎支持集合三者一致。
- 保持既有 fail-fast 口径：集合外 provider 在装配阶段报错并列出合法集合；引擎侧抛 `ConfigurationError`，无静默降级。
- 收敛过程中不引入"守卫变假绿"（前端清单对拍用例的识别锚点必须同步）。

**Non-Goals:**

- 不动 DeepSeek / 阿里百炼各自的分支实现与模型清单（上一单刚同步过 DeepSeek）。
- 不动认证、任务链路、数据库与前端其它表单。
- 不为"将来接第三方"预留代码位（用户已选择一并去掉；需要时另立一单重新引入）。

## Decisions

**D1 三层一起收敛（用户已定），保持 fail-fast 不变。**

前端清单、`PROVIDER_DEFAULTS`/`_PROVIDER_HOSTS`、引擎 `SUPPORTED_PROVIDERS` 同批收敛到两项；未知 provider 的报错行为**不变**（只改"合法集合"的内容），因此既不新增兼容分支，也不放松校验。

**D2 删"OpenAI 兼容 provider 分支"，但保留 DeepSeek 视觉档的 OpenAI 兼容客户端。**

`create_model()` 里有两处用到 OpenAI 兼容类，性质完全不同：
- `config.provider == "deepseek"` 且 `vision=True` → 用 `OpenAIChatModel` + `OpenAICredential`（**保留**，这是 DeepSeek 多模态档的实现方式）；
- `config.provider in OPENAI_COMPATIBLE_PROVIDERS` → 承接 openai/anthropic/gemini/custom（**删除**，连同常量）。
把两者混为一谈会误删视觉链路。

**D3 `get_provider_config()` 的兜底键改为不依赖 `custom`。**

原实现 `PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["custom"])` 在删除 `custom` 后直接 `KeyError`。改为在映射表内取默认（未知 provider 由上游 `VALID_PROVIDERS` 校验拦下，本函数不再承担兜底职责，也不静默给出错误地址）；`validate_base_url()` 删除 `custom` 特例后，白名单与"禁止本机地址"规则对两项 provider 依旧生效。

**D4 `ModelProvider` 枚举（`models/constants.py`）同步为两项。**

该枚举当前**零消费**（全仓无引用），改它不改任何行为；但作为"AI 模型提供商"的 SSOT 声明，若继续列 openai/anthropic/custom 会与实现背离。只改成员、不动枚举基类与数量，故 `models/` 的枚举门禁（数量下限、StrEnum 基类）不受影响。

**D5 前端对拍用例的锚点必须换（否则守卫假绿）。**

`test_ai_deepseek_model_catalog.py` 现在用正则 `value:\s*"deepseek".*?value:\s*"custom"` 截取 DeepSeek 段落；`custom` 删除后该正则会失配，而用例若只断言"集合相等"可能因截取失败而报另一种错——正是"识别规则退化"的典型。本次把锚点改为**不依赖任何将被删除的 provider**（以数组元素结尾为界），并保留规模下限断言。

**D6 旧注册脚本的默认 provider 由 `custom` 改为 `deepseek`。**

`tools/register_agentscope_agents.py` 两处 `a.model_provider or "custom"`：`custom` 不再是合法值，默认值改为 `deepseek`（与平台默认 provider 一致）。

## 模块防火墙自检

- 跨 App import：无新增（改动都在既有文件内，方向不变）。
- 写库路径：零写库改动；无迁移。
- 前端：只收缩一个下拉的选项；不新增 HTTP 出口、不改 api 层。
- 引擎边界：不 import `apps.*`；支持集合是引擎内部常量，与 Django 侧由一致性用例守护。
- 规格：本单**不设** `skip_specs`，delta 以 MODIFIED 更新 `ai-engine-protocol` 的 provider 需求（含全部原场景，避免归档丢场景）。

## Risks / Trade-offs

- [将来要接第三方 / 自建端点] → 已登记为代价：需重新引入 provider（含 `custom` 的任意主机放行与 `localhost` 例外），一次小改；本单不做预留位。
- [删 `custom` 触发 `KeyError`] → D3 先改兜底实现；并用"未知 provider 不静默给地址"的用例覆盖。
- [误删 DeepSeek 视觉链路] → D2 明确区分两类 OpenAI 兼容用法；用「deepseek + vision 仍构造成功」的既有用例把关。
- [前端对拍守卫失配后假绿] → D5 同步换锚点，并在用例中保留规模下限与"未定位到清单即失败"的显式断言。
- [文档与代码再次漂移] → 接口文档的提供商枚举、规格措辞与代码同批更新；关单时 grep 已移除的 provider 名（`openai`/`anthropic`/`gemini`/`custom`）确认仅出现在允许处（历史归档、测试反例、枚举迁移说明）。

## Migration Plan

1. 后端 `provider_registry`（映射 / 白名单 / 兜底 / 特例）→ 引擎支持集合与分支 → 前端清单 → 枚举与脚本默认值。
2. 同步测试（一致性断言、对拍锚点）与文档（接口文档、规格 delta）。
3. 验证：`manage.py check`、ruff（门禁范围）、相关用例最小集、边界检查、前端 typecheck/eslint/相关 vitest。
4. 回滚：纯常量与选项收缩、无数据迁移；`git revert` 单次提交即可（存量配置本就未使用被删 provider）。
