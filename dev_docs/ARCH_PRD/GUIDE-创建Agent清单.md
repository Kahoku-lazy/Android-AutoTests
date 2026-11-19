# GUIDE — 新增一项 Agent 能力

> 目标：能力进 `ae_harness`，角色与流程进 `backend_bridge`。不要把逻辑写进 Django View 或前端。
> 必读：根 [`AGENTS.md`](../../AGENTS.md)「平台架构定位」· [`engines/AGENTS.md`](../../engines/AGENTS.md) · [`engines/ae_harness/AGENTS.md`](../../engines/ae_harness/AGENTS.md) · [`engines/backend_bridge/AGENTS.md`](../../engines/backend_bridge/AGENTS.md)

## 0. 先判定落点

| 你想做的事 | 落点 | 不要做的事 |
| --- | --- | --- |
| 新工具（一个动作） | `engines/ae_harness/tools/<域>/`，并在 `catalog.py` 登记 | 在工具里编排多步，或在 View 里调设备 |
| 新角色、新提示词、新流程 | `engines/backend_bridge/`；提示词与连接参数由调用方传入 | 在 `ae_harness` 写提示词文件或角色脚本 |
| 只改任务下发、落库、展示 | `backend/apps/` | 在 engines 里写 Django ORM |
| 新设备、串口、OCR 原子能力 | `engines/device` / `uart_log` / `vision`，再经工具暴露 | 上层直接 import uiautomator2 |

`ae_harness` 只造智能体和提供工具。它不保存角色、提示词或具体流程。

## 1. 最小必做清单

1. **工具**
   - 放 `engines/ae_harness/tools/<域>/`，一个函数只做一个动作。
   - 在 `tools/catalog.py` 登记域、全部预设与只读预设。
   - 文本工具返回 JSON，带 `timestamp` 与 `status`。

2. **装配**
   - 在 `backend_bridge` 调 `create_agent`，传入名称、提示词正文、`provider`、`api_key_env`、`model_name`、`base_url`。
   - 再按调用方的勾选挂工具。验收侧只取勾选与只读目录的交集。
   - 不在 `ae_harness` 新增 `agent_<role>.py`，也不新增提示词文件。

3. **流程（若是 SOP）**
   - 步骤由调用方提供 YAML，经 `load_spec` 加载，经 `run_sop` 执行。
   - 不在 `ae_harness/workflow/` 写死具体流程，也不另写一套编排循环。

## 2. 自检

人工核对：

- [ ] 提示词由调用方传入，`ae_harness` 没有新的提示词文件
- [ ] 模型经 `create_model(provider, api_key_env, model_name, base_url)`，没有模型短名
- [ ] 工具在 `tools/<域>/`，并登记进 `catalog.py`
- [ ] 角色装配在 `backend_bridge`，只经 `create_agent`
- [ ] 本次 engines 改动没有 `import apps` / `django`
- [ ] 没有在 View 里嵌 SOP 循环或设备操作

## 3. 反模式（看到就停）

- 在 DRF View / `api.py` 里直接 `Agent(` 或调用 uiautomator2
- 在 `ae_harness` 新增角色脚本、提示词文件或写死的流程
- 恢复 `engines/agents/`、模型短名、`role_sys_prompts`、`prompts/*.md`
- 把工具文件堆在 `tools/` 根上
- 为图省事 `git add -A`

## 4. 参考实现

| 场景 | 参考 |
| --- | --- |
| 造智能体 | `engines/ae_harness/agents/creator.py` |
| 设备工具 | `engines/ae_harness/tools/adb/` |
| 名片绑定的一对角色 | `engines/backend_bridge/workflow/bound_roles.py` |
| 一次 SOP | `engines/backend_bridge/workflow/bound_sop.py` |
| 单角色会话 | `engines/backend_bridge/agents/ui_executor.py` |
