## Context

`ai_assistant` 的域状态字面量与设备域同构（枚举零消费 + 字面量散落），但歧义更多：`"user"` / `"system"` / `"completed"` / `"failed"` 这些词在本 App 里大量用于**字典键、响应键与 Django 属性名**。故沿用「逐行定点 + 显式 skip 名单」，不用全局替换。

## Goals / Non-Goals

**Goals:**

- `AIAgent.status` / `AITask.status` / `AIMessage.role` 的取值一律取 `models.constants` 的枚举成员
- 让 `AgentStatus` / `TaskStatus` / `MessageRole` 从「零生产消费」变为真实 SSOT

**Non-Goals:**

- 不动 `ModelProvider`（枚举缺 `deepseek`/`gemini`，收敛会写错；见 proposal 的登记项）
- 不改 `models.py` 的字段默认值（避免迁移）
- 不改与枚举同形的**非状态字面量**（dict/响应键、Django 属性名、引擎原始状态）

## Decisions

### 1. 直连 `models.constants`，不在本 App 新造转发模块

- **选择**：五个文件各加 `from models.constants import ...`
- **理由**：D4 规定的 SSOT 位置就是 `models/`；`device_pool/contracts.py` 之所以存在是因为该 App 本就有「数据契约」模块（`apps/device_pool/AGENTS.md` 规定）。`ai_assistant` 没有这样的模块，为一次收敛新造一个转发层属过度设计

### 2. `ModelProvider` 整块排除，而不是「顺手补两个成员」

- **选择**：本单不碰 provider 相关字面量
- **理由**：补成员会让 `ModelProvider` 与 `PROVIDER_DEFAULTS` 从「两处定义」变成「两处需要保持同步」，仍不是 SSOT；真正的修法是让注册表**以枚举为键**，那会改到 `get_provider_config` / `validate_base_url`（安全相关）与写入口校验，属独立裁决面

### 3. `result.status == "success"` 的 `"success"` 保持不变

- **选择**：只把**结果赋值**的 `"completed"` / `"failed"` 换成 `TaskStatus`，判定用的 `"success"` 留字面量
- **理由**：`TaskStatus` 没有 `SUCCESS` 成员；`"success"` 是**引擎返回**的状态（`engines.ai` 契约），不是本 App 的域状态。混用会让两个域的状态口径纠缠

## Risks / Trade-offs

- [状态字段口径漂移] → `AITask.status` 是前端轮询依据；替换只把字面量换成等值成员，写库值不变（新测试钉住「读回普通取值串」）
- [误改响应契约] → skip 名单已在 proposal 逐条列出并给理由；替换后复扫，剩余命中必须 == skip 名单
- [新增 import 被 `ruff --fix` 当 F401 删掉] → 上一单踩过这个坑（`contracts.py` 转发名）；本单每个 import 都在本文件**真实使用**，替换后仍复跑 `manage.py check` 兜底

## Migration Plan

1. 五文件加 import → 18 行定点替换
2. 新增不变量测试；跑单测 / 全量 / 边界
3. 复扫字面量，确认剩余命中 == skip 名单
4. 归档；回滚 = `git checkout` 五个文件 + 删测试
