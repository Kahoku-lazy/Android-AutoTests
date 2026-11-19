# AGENTS.md

## 平台架构定位（Model + Harness）

**结论先行：** 本平台的核心是 **Agent**。前端负责展示；后端是通道与记账；

### 三层分工

| 层 | 位置 | 职责 |
| --- | --- | --- |
| 展示 | `frontend/` | 任务、花费、能力与运行状态的可视化 |
| 通道与记账 | `backend/`（含 `apps`） | 任务下发、权限与会话接入；把角色花费、能力与任务写入数据库；不承载核心自动化能力实现 |
| 能力核心 | `engines/` | 平台能力全集：Agent 运行时 + Harness + 设备/串口/视觉等支撑 |

依赖方向：**backend →（注入）→ engines**；`engines` **禁止**反向依赖 `apps.*` / `django.*`。
---
## 行为规范

1. **必须** 遵循`OpenSpec` 规范驱动流程的四步（`/opsx:explore`、 `/opsx:propose <change-id>`、 `/opsx:apply`、`/opsx:archive`）开发功能

2. **必须** 遵循结论先行原则，；先给出总的结论，再给出详细说明，最后罗列需要我决策的内容。

3. **禁止带着不确定性的因素去行动**-- 发现有冲突的、有疑惑的、或者前后矛盾等问题必须要先提出来，解决后再执行；

4. **改规则必须先请示（硬约束）**-- 下列四类改动**必须先提交「变更申请」并经需求方确认，才能动代码与文档**，**不得先改后报**：
   - 修改任何 `AGENTS.md`（含各级子目录）的**红线 / 禁止事项 / 准入清单 / 依赖边界**条款；
   - **新增自定义异常类**（`engines/` 红线要求先在对应子 AGENTS 立项）；
   - 放宽或收紧**模块之间的依赖方向**（如 `engines/` 反向依赖 `apps.*`）；
   - 修改**钱与配额**相关口径（计费规则、token 统计口径、预算默认值）。

   「变更申请」至少写清四件事：**改什么、为什么必须改、影响面、怎么回退**。理由再充分也不能自己批——规则的意义就是在"看起来必须破例"时拦住 AI。

## GitHub 版本控制与提交

1. **单主干 `Kahoku`**：仓库只有这一个长期分支。
2. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`，type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`。一次提交只做一件事；**禁止 `git add -A`** —— 历史上有一次退役提交用它把未申报的目录改名一起带进去，导致已删除的包复活。
3. **PR 流程**：所有改动走 `feature 分支 → PR → 合并进 Kahoku`，禁止直推主干（`Kahoku` 分支保护强制，管理员同样生效）。外部协作者可 fork 后提 PR，无需授权；首次贡献者的 PR 需维护者在 Actions 页批准运行 CI。
4. **CI 是唯一的质量闸门**：PR 提交后必须确认 `ci-phase1.yml` 的 `python` 与 `frontend` 两个 job 全绿，作为合并前置条件
5. **禁止强推**：`Kahoku` 是唯一主干，禁止 `--force`。已推送的提交要改，用新提交修正，不改写历史。
6. **提交前先跑本地门禁**：`python run.py check`（与 CI 同一批检查，阻塞项失败即退出码 1）。不跑全量回归。
```bash
python run.py check                # 本地门禁
git add <具体文件>                  # 逐文件暂存，不用 -A
git commit -m "feat(scope): ..."
git push origin <feature分支>       # 推特性分支，不直推 Kahoku
gh pr create --base Kahoku         # 提 PR；python / frontend 两个 CI job 全绿后方可合并
```

## Python代码编写要求

### 代码编写要求

1. 模块与方法必须有注释，注释格式参考下文中的"注释格式模板"。

2. 相同业务功能封装在一个模块(`.py`)中, 例如 adb 设备工具放在`engines/ae_harness/tools/adb/`，串口日志放在`engines/uart_log/`

3. 参考`engines/ae_harness/agents/models.py`（按调用方传入的连接参数造模型）与`engines/ae_harness/agents/creator.py`（只造智能体、不定义角色）的写法，一个模块（类、函数、组件）只做一件事，内部元素紧密相关，职责清晰；

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
