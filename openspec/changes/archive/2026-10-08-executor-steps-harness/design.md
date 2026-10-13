## Context

动机见 `proposal.md` - Why。方案需要的事实（已核对代码）：

- 执行模型在引擎侧就是 `ExecutorRole`：`run(serial, action, idx, total, retry_hint="")` 返回 `RoleResult`，其中 `output`（最终 JSON）、`thinking`（思考片段列表）、`tool_usage`（工具调用与返回行）、`screenshot_path`、`usage`（token）、`cost`（本轮费用）都是现成的。
- 引擎自带设备工具由登记清单提供（`device_tool_specs(output_root)`），角色装配时会自动挂上，因此**不需要平台注入任何工具**即可真机执行。
- 工具调用记录的形状：`{"type":"call","name","input"}`、`{"type":"result","name","state","output","screenshot_path"?}`、`{"type":"image","media_type"}`。
- 模型连接（provider / 模型名 / 密钥 / base_url）属于平台配置；引擎不读库，所以跑测工具必须自己拿配置——用环境变量，默认 `deepseek` + `https://api.deepseek.com/v1`。

## Goals / Non-Goals

**Goals:**

- 一个 JSON 多条步骤，循环执行，逐步打印思考 / 工具记录 / 截图路径 / 输出 / 费用，末尾给总计。
- 只依赖引擎侧能力；不建任务、不落库、不依赖平台服务。

**Non-Goals:**

- 不写断言判定（那是验收模型的事）、不改引擎与平台代码、不进默认 CI 全量跑（缺配置即跳过）。

## Decisions

**D1 入口与命名**：`tests/engines/test_executor_steps.py`，既可直接 `python tests/engines/test_executor_steps.py <json>` 当命令行工具跑，也作为 pytest 用例收集；pytest 下缺配置/缺 steps 就 `skip`，保证默认套件零影响。

**D2 配置来源**：环境变量优先（`EXECUTOR_PROVIDER` / `EXECUTOR_MODEL` / `EXECUTOR_API_KEY` / `EXECUTOR_BASE_URL`），默认 provider=deepseek、model=deepseek-flash、base_url=`https://api.deepseek.com/v1`；密钥缺失时抛可读提示（含设置示例）。密钥**不落盘**。

**D3 执行与上下文**：每个步骤独立一轮（与工作流一致：一步一次执行），但**共用一个角色实例与事件循环**，避免重复装配；步骤序号与总数按 JSON 顺序给出，与生产口径一致。

**D4 输出**：逐步打印 + 汇总；每步写一份 JSON 行到 `tests/reports/engines/run-<时间戳>.jsonl`（含 thinking / tool_usage / output / screenshot_path / usage / cost），截图落 `tests/reports/engines/shots/`（相对路径与平台链路同形）。

**D5 失败语义**：单步异常不中断整轮（打印错误后继续下一步），末尾汇总含失败步数与总费用。

## 模块防火墙自检

- 测试代码不写库、不起服务、不改产品代码；只 import `engines.*`（与 `tests/` 既有用法一致）。
- 不新增跨 App 调用；`apps/` 零改动；前端零改动。

## Risks / Trade-offs

- [测试依赖真机与付费密钥，默认套件不该跑] → D1 的 skip 规则 + 只在显式提供 steps 与密钥时执行。
- [密钥误提交] → 只从环境变量读，不写文件；运行记录落在 git 忽略的 `tests/reports/`。
- [录到的工具输出可能很长] → 打印按上限截断，完整内容仍写入 JSONL 记录。

## 迁移与回滚

- 无迁移；删除两个新增文件即可回滚。
