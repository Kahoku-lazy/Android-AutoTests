# AGENTS.md

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

2. 相同业务功能封装在一个模块(`.py`)中, 例如 设备控制工具全部放在`engines/agents/tools/test_device.py`中；串口日志相关的放在了`engines/agents/tools/test_serial.py`中

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
