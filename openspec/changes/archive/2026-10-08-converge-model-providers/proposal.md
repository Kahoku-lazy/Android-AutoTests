# 模型服务收敛为 DeepSeek 与阿里百炼

## Why

平台当前的"模型服务"清单与实际能力不齐：

- **界面**列出 5 项：阿里百炼、DeepSeek、OpenAI、Anthropic (Claude)、自定义 (OpenAI 兼容)；
- **后端与引擎的合法集合是 6 项**（多一个 Gemini），且两侧被一条一致性用例强制相等、规格也写着"两侧集合一致"。
  于是界面不给选、接口仍能配 —— 一处既有的不一致。

需求是**只保留 DeepSeek 与阿里百炼**，其余去掉。前置核实（实测）：

- **库里没有任何存量在用其它 provider**：现有唯一一个智能体（#10）三个角色全部是 `deepseek`（部分角色未显式写 provider，走默认值），线路键只有 `device_control`。故本次收敛**不会打断任何现有任务**。
- **连带点已定位**（不处理会踩坑）：① 后端解析默认地址的函数把 `custom` 当兜底键，删掉 `custom` 会直接 `KeyError`；② 旧注册脚本默认写 `"custom"`；③ 已下线的 provider 分支在引擎里与"视觉档走 OpenAI 兼容客户端"是两件事，不能一起删（详见 design.md D2）；④ 前端清单的**对拍用例**用 `value: "custom"` 当段落结束锚点，删掉它会让守卫失配（详见 D6）。

## What Changes

- **前端**：模型服务下拉只留 **DeepSeek** 与 **阿里百炼 (DashScope)**。
- **后端**：`provider → base_url` 映射与主机白名单同步收缩到这两项；解析默认地址不再引用 `custom`；`custom` 的"任意主机放行"特例删除。
- **引擎**：可处理 provider 集合收缩为 `{deepseek, dashscope}`，删除 OpenAI 兼容 provider 分支与常量（**保留** DeepSeek 视觉档使用的 OpenAI 兼容客户端实现）。
- **保持 fail-fast**：集合外的 provider 仍在装配阶段报错并列出合法集合，引擎侧同样抛错——不新增任何静默降级。
- **一致性守护同步**：两侧集合相等的用例保留并更新断言；前端清单对拍用例的识别锚点改为不再依赖已删除的 provider。
- **顺带对齐**：`models/constants.py` 的 `ModelProvider` 枚举（当前零消费）同步为这两项，避免"提供商枚举"与实现继续背离。
- **文档**：接口文档中"提供商枚举"的列举同步；规格 `ai-engine-protocol` 的 provider 需求随"OpenAI 兼容白名单"消失而更新措辞。

## 关联文档

- 关联能力：`ai-engine-protocol`（provider 单一真相源与 fail-fast 口径）。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `ai-engine-protocol`：「provider 配置单一真相源」一条需要更新——原场景以「不在 OpenAI 兼容白名单内的 provider」描述兜底分支的行为，兼容分支与白名单本次被移除，措辞与约束需改为「集合外的 provider 一律报错、不存在任何兼容兜底」，并明确支持的 provider 恰为 DeepSeek 与阿里百炼。

## Impact

- 前端：`modules/ai-assistant/components/ModelConfigField.vue`（清单）。
- 后端：`apps/ai_assistant/provider_registry.py`（映射表 / 主机白名单 / 默认地址解析 / `custom` 特例）；`models/constants.py`（`ModelProvider` 枚举）。
- 引擎：`engines/ai/agents/base.py`（支持集合与 provider 分支）。
- 工具：`tools/register_agentscope_agents.py`（默认 provider 由 `custom` 改为 `deepseek`）。
- 测试：`tests/graybox/unit/test_ai_engine_config.py`（一致性断言）、`tests/graybox/unit/test_ai_deepseek_model_catalog.py`（对拍锚点）。
- 文档：`dev_docs/DEV_TEST/接口文档/API-AI助手.md` 的提供商枚举列举。
- **已登记的代价**：`自定义 (OpenAI 兼容)` 是私有化/自建 OpenAI 兼容端点的唯一入口，去掉后**不能再配置自建或第三方端点**（含 `localhost` 类地址）；将来要接需先重新引入该 provider（一次小改）。此为用户确认的取舍。
- 数据库 / 迁移 / 通道：零改动（存量配置不受影响，已实测）。
