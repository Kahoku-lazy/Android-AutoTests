# AGENTS.md

## 平台架构定位（Model + Harness）

**结论先行：** 本平台的核心是 **Agent**。前端负责展示；后端是通道与记账；**`engines/` 集中平台全部可执行能力**。一个 Agent **角色** = **Model + Harness**。

### 三层分工

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 展示 | `frontend/` | 任务、花费、能力与运行状态的可视化 |
| 通道与记账 | `backend/`（含 `apps`） | 任务下发、权限与会话接入；把角色花费、能力与任务写入数据库；不承载核心自动化能力实现 |
| 能力核心 | `engines/` | 平台能力全集：Agent 运行时 + Harness + 设备/串口/视觉等支撑 |

依赖方向：**backend →（注入）→ engines**；`engines` **禁止**反向依赖 `apps.*` / `django.*`。

### Agent = Model + Harness

- **Model**：推理与生成（如 DeepSeek、Dashscope / Omni 等），由角色配置选用。
- **Harness**：角色跑起来所需的外围能力，集中在 `engines/agents/`：
  - **工具** `tools/` + `tools_config.py`
  - **技能** `skills/`
  - **知识库** `rag/`（及 MCP 等扩展配置 `mcp_config/`）
  - **记忆与上下文**：会话/历史与当轮上下文装配（含 messaging、语音 session/pipeline 等；RAG 结果只注入当轮，不写进长期历史）
  - **提示词** `prompts/` + `prompt_config.py`
- **角色** `role/`（继承 `BaseRole`）：把选定的 Model 与上述 Harness 装配成可下发、可计量的 Agent。
- **工作流** `workflow/`：SOP 步骤与单次运行；不在此创建角色或旁路绑定工具/提示词。

### Harness 的控制与数据底座

`engines/device`、`engines/uart_log`、`engines/vision` 为 Harness 提供控制与感知（设备动作、串口日志、OCR 等），经 `tool_*.py` 暴露给角色，而不是由业务层直接绑实现。

### 花费、任务与展示闭环

角色的**花费、能力与任务下发**经后端写入数据库并记录；再由前端展示。engines 负责产生可观测事件与用量（如 messaging / billing、语音 `model_usage`），**不在 engines 内写业务库**。

### 文档落点

- **本文件**：平台总思路（本节）。
- **架构说明书**：[dev_docs/ARCH_PRD/ARCH-平台架构设计.md](dev_docs/ARCH_PRD/ARCH-平台架构设计.md)
- **创建 Agent 清单**：[dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md](dev_docs/ARCH_PRD/GUIDE-创建Agent清单.md)（新增角色必循）
- **落地与红线**：[`engines/AGENTS.md`](engines/AGENTS.md) 及子目录 AGENTS（agents / rag / realtime_vocie）；风格正文见 [`.agents/rules/engines-code-style.md`](.agents/rules/engines-code-style.md)。

---
## 行为规范

1. **必须** 遵循`OpenSpec` 规范驱动流程的四步（`/opsx:explore`、 `/opsx:propose <change-id>`、 `/opsx:apply`、`/opsx:archive`）开发功能

3. **必须** 遵循结论先行原则，；先给出总的结论，再给出详细说明，最后罗列需要我决策的内容。

## GitHub 版本控制与提交

1. **单主干 `Kahoku`**：仓库只有这一个长期分支。
2. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。一次提交只做一件事；**禁止 `git add -A`** —— 历史上有一次退役提交用它把未申报的目录改名一起带进去，导致已删除的包复活。
3. **没有 PR 流程**：改动直接推 `Kahoku`，不经 PR，不再要求 PR 与状态检查。
4. **CI 是唯一的质量闸门**：推送后必须确认 `ci-phase1.yml` 的 6 个 job 全绿
5. **禁止强推**：`Kahoku` 是唯一主干，禁止 `--force`。已推送的提交要改，用新提交修正，不改写历史。
6. **提交前先跑本地门禁**：`python run.py check`（与 CI 同一批检查，阻塞项失败即退出码 1）。不跑全量回归。
```bash
python run.py check                # 本地门禁
git add <具体文件>                  # 逐文件暂存，不用 -A
git commit -m "feat(scope): ..."
git push origin Kahoku             # 推送后确认 6 个 CI job 全绿
```

## Python代码编写要求

### 代码编写要求

1. 模块与方法必须有注释，注释格式参考下文中的"注释格式模板"。

2. 相同业务功能封装在一个模块(`.py`)中, 例如 设备控制工具全部放在`engines/agents/tools/tool_device.py`中；串口日志相关的放在了`engines/agents/tools/tool_serial.py`中

3. 参考模块`engines/agents/role/config.py`中的编写方法，采用单一职责划分出模型配置，Agent角色配置与创建模型功能；一个模块（类、函数、组件）只做一件事，内部元素紧密相关，职责清晰；

4. **要保证**模块之间依赖尽量少、尽量简单。改一个地方，不容易牵连一大片

### 注释格式模板

1. **模块** 注释模板如下：

```python
"""
python -m 调试路径: engines.agents.<子包>.<模块>

本模块的业务功能如下：
1. <类或功能名>: <一句话说明>。
"""
```

2. **类** 的助手模板如下
```python
class RoleSpecConfig:
    """
    功能设计说明

    Attributes:
        参数说

    Raises:
       异常情况。
    """
```

3. **函数** 注释模板如下：
```python
def method(self, content: str):
    """
    一句话说明这个方法做什么。

    Args:
        content: 参数说明。

    Returns:
        返回值说明。

    Raises:
        ValueError: 触发条件。
        RuntimeError: 触发条件。
    """
```

## 项目文档与工具

### 文档位置

1. 临时生成的代码与文件、临时生成的测试数据 **必须**放到 `temps/` 中，不要在项目根目录下生成临时文件
2. 设计方案与报告，接口文档在 `dev_docs\DEV_TEST`目录中，文件名举例：XXX.md/XXX.html
3. 需求文档与架构文档放在 `dev_docs\ARCH_PRD` 中，文件名举例：ARCH-XXX.md/ARCH-XXX.html 或 PRD-XXX.md/PRD-XXX.html


### 项目工具

1. 启动/停止/检查平台： `python run.py start / stop / status`
2. 本地质量门禁： `python run.py check` 
3. 测试统一入口： `python -m pytest -c tests/pytest.ini` — 测试资产全部在 `tests/` 下（`pytest.ini` / `test_settings.py` / 用例）。
