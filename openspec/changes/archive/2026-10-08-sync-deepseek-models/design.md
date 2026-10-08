# 设计：同步 DeepSeek 模型清单与多模态能力标注

## Context

- **权威事实（本单实测，非推测）**：
  - `GET https://api.deepseek.com/v1/models`（用平台自己的密钥，HTTP 200）返回两个模型：`deepseek-flash`（`input_modalities: ["text","image"]`）与 `deepseek-v4-pro`（`["text"]`）；两者 `context_window` = 1048576、`max_output_tokens` = 393216。
  - 官方价目页：Flash 空闲价 输入命中 **0.02** / 未命中 **1** / 输出 **4**（元/百万 tokens），Pro 0.15 / 4.5 / 13.5；高峰 = 空闲 ×2（与平台 `_PEAK_MULTIPLIER = 2` 一致）。页脚注明：模型名请用 `deepseek-flash`；旧名 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` 仍可调用但模型已下线、按 Flash 计费。
- **平台现状（三处漂移）**：
  1. 前端模型清单硬编码在 `components/ModelConfigField.vue`（`deepseek-v4-pro` / `deepseek-v4-flash` / `deepseek-v4-flash-vision-exp`），只有名字、没有能力位；
  2. 两份价目表（`apps/ai_assistant/deepseek_billing.py` 与 `engines/ai/billing/billing.py`）为旧价，且**互相之间没有一致性测试守护**（只有引擎侧 docstring 写着"调价需同步"）；
  3. `_DEFAULT_DEEPSEEK_MODEL` 与 `_DEEPSEEK_MODEL_ALIASES["deepseek-chat"]` 都指向 `deepseek-v4-flash`（已不在 API 正式清单内）。
- **已存在但不够用的能力**：`POST /api/ai/models/detect/` 会拉 `/models` 并把结果缓存到 `AIAGENT.available_models`，但 `_extract_model_ids()` **只保留 id**，能力字段被丢弃；且该结果只用于连通性校验，不驱动下拉。
- 用户已定的三个口径：① 更新**内置清单**（不改成跟随探测）；② 标注 + **装配期提醒**；③ 旧名**作别名**指向 `deepseek-flash` 并采用官方新价。

## Goals / Non-Goals

**Goals:**

- 配置页只列正式模型名，并标明多模态能力；需要图片的角色有明确提示。
- 两份价目表与官方现价一致；默认档与别名指向正式模型名。
- 用机械守卫防止"三处清单再次漂移"，并堵住"清单里有模型却没有价目、静默走默认档计费"的隐患。

**Non-Goals:**

- 不改模型探测接口与缓存形状（不把能力字段落库、不让下拉跟随探测）——用户已选择保持内置清单。
- 不改视觉通道的实现方式（执行 / 验收仍走 OpenAI 兼容 + 思考模式），本单只加"能力不匹配"的提醒。
- 不改角色配方（谁的 `vision=True` 不变）、不改提示词、不改工具子集。
- 不校正 `ai-agent-model-config` 既有三条过时需求（主推理 / 视觉 / 强模型）——属既有漂移，另行立单。

## Decisions

**D1 模型目录放引擎侧 `agents/config.py`，前端镜像它，用对拍测试守住。**

目录内容 = 「当前正式模型名 → 是否支持图片输入」。放引擎的理由：决定"是否走视觉通道"的判断在引擎（`RoleSpec.vision` + `create_model(vision=...)`），装配告警必须发生在同一层，引擎又不能 import `apps.*`。
前端保持内置清单（用户已定），但**新增对拍用例**断言「前端 `ModelConfigField.vue` 的 deepseek 清单 ≡ 引擎目录键集合」，用仓库既有的"契约对拍测试（读源码）"范式，防止再次漂移。
备选：让前端经新端点取目录 —— 消除镜像但新增 HTTP 面与离线回退，用户已选择不做；否决。

**D2 目录与价目互为守护：目录键必须都是价目表的正式条目。**

新增用例断言「目录键 ⊆ 价目表键」且「目录键不是靠 `_DEFAULT_DEEPSEEK_MODEL` 兜底命中的」。这条直接堵住本单发现的隐患：旧 `deepseek-v4-flash-vision-exp` 已不在正式清单里却仍留在价目表中，任何出现它的用量都靠默认档兜底计费、静默无感。
同时补一条「两份价目表逐键相等」的用例——它们被文档要求同步，此前**没有任何测试守护**。

**D3 旧名作别名，价目与默认档收敛到正式名。**

`DEEPSEEK_PRICING` 只保留两个正式条目（`deepseek-flash` / `deepseek-v4-pro`）；`_DEEPSEEK_MODEL_ALIASES` 增加 `deepseek-v4-flash`、`deepseek-v4-flash-vision-exp` → `deepseek-flash`（与厂商"旧名按 Flash 计费"一致），并把 `deepseek-chat` 也指到 `deepseek-flash`；`_DEFAULT_DEEPSEEK_MODEL` = `deepseek-flash`。
**已知副作用（显式登记）**：费用按当前价目重算，因此历史任务的 DeepSeek 费用显示会随本次调价下降（Flash 档为主）。这是平台既有口径（"调价只改价目表"），非本单引入的新机制。

**D4 多模态提醒分两处落，都不新增接口。**

- **配置界面**：模型清单每项带能力标注；执行 / 验收区块显示固定提示「本角色需要多模态模型（可读截图）」。组件新增一个布尔入参（是否需要图片），由调用方按角色传入——静态提示，不做角色×模型的动态判断。
- **引擎装配**：`AgentRole._assemble` 在 `spec.vision` 为真且模型已知为纯文本时 `logger.warning`，含角色名与模型名；不抛错、不阻断装配（符合用户口径"提醒"而非"拦截"）。
备选：在 Django 装配层做拦截 —— 会让"看得到提醒"的人（管理员）与"能改配置"的地方分离，且要新增角色→vision 的前端/后端映射；否决。

**D5 只认已知能力，未知模型不告警。**

目录只覆盖 DeepSeek 正式模型；其他 provider / 自定义模型名一律**不告警**（避免对 qwen、claude 等误报）。判断函数取名 `model_supports_image(provider, model_name) -> bool | None`，`None` = 未知 → 不提醒。

## 模块防火墙自检

- 跨 App import：无新增。引擎只加自身常量与一个 logger 告警；价目表的"两份同步"关系不变（apps 与 engines 各一份，由测试守护）。
- 写库路径：零写库改动；无迁移、无新端点。
- 前端：只改模型清单与提示文案，仍经既有表单提交路径；不新增 HTTP 出口。
- 引擎边界：不 import `apps.*`；新增能力目录是引擎内部常量。
- 规格：本单**不设** `skip_specs`，delta 并入 `ai-agent-model-config`。

## Risks / Trade-offs

- [前端清单与引擎目录再次漂移] → 对拍用例（读源码）断言两者键集合相等；改任一侧不齐即红。
- [价目漏配导致静默按默认档计费] → 断言目录键 ⊆ 价目表键且非兜底命中；另加两份价目表逐键相等用例。
- [历史任务费用显示变化被当成 bug 上报] → 在 proposal 与关单汇报中显式登记该副作用及其既有口径依据。
- [多模态告警对未知模型误报] → 只对目录内明确"纯文本"的模型告警；未知返回 `None` 不告警。
- [前端提示与角色错位（把提示挂错区块）] → 提示由调用方按角色传入布尔入参，用例断言执行 / 验收区块有提示、规划区块没有。
- [官方再次改名] → 本单不做自动跟随；目录与价目表的改动点已收敛为三处 + 一条对拍用例，下次同步是机械操作。

## Migration Plan

1. 引擎侧：目录常量 + 能力判断函数 + 装配告警；价目 / 别名 / 默认档。
2. 后端侧：价目 / 别名 / 默认档（与引擎逐键一致）。
3. 前端：清单带能力标注 + 执行 / 验收区块提示。
4. 测试：新增三条守护用例（前端对拍、目录⊆价目、两份价目相等），并更新既有以旧价/旧名作期望的用例。
5. 文档：接口文档计价说明、引擎内注释示例。
6. 回滚：纯常量与文案改动、无迁移；`git revert` 单次提交即可（费用显示会随之回到旧价）。
