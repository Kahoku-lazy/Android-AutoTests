## 1. 迁移到 `role/config.py`

- [x] 1.1 `engines/agents/role/config.py` 接收 `ChatModelFactory`（连同 `deepseek_model` / `openai_model` / `dashscope_model` / `create` 四个方法逐字搬入），并新增其依赖导入 `from agentscope.credential import DashScopeCredential, DeepSeekCredential, OpenAICredential` 与 `from agentscope.model import ChatModelBase, DashScopeChatModel, DeepSeekChatModel, OpenAIChatModel`；补模块 docstring；修正第 1 行 `from dataclasses import  dataclass` 的双空格。验证：`python -m ruff check --no-cache engines/agents/role/config.py` 退出码 0；且检索确认 `class ChatModelFactory` 在 `config.py`、`def create` 在其类体内。**验证结果**：通过 —— config.py 54 → 135 行，三个类分别落在第 22（`ModelConfig`）/ 47（`RoleSpecConfig`）/ 71（`ChatModelFactory`）行；`from .config import` 外部可导入名齐备；五个改动文件的 `ruff check --no-cache` 汇总为 `All checks passed!`。
- [x] 1.2 `engines/agents/role/base.py` 删除 `ModelConfig`、`RoleSpecConfig`、`ChatModelFactory` 三份定义（含 `__post_init__` 与四个工厂方法）。验证：检索 `class ModelConfig|class RoleSpecConfig|class ChatModelFactory` 在 `base.py` 0 命中；`base.py` 中不再出现 `SecretStr`、`DashScopeCredential`、`DeepSeekCredential`、`OpenAICredential`、`ChatModelBase`、`DashScopeChatModel`、`DeepSeekChatModel`、`OpenAIChatModel`。**验证结果**：通过 —— base.py 458 → 334 行；三类 0 命中；上述 8 个名字在 base.py 全无残留（AST 校验 `base.py 不再定义被搬移的类 -> ['BaseRole', 'RoleConfig']`）。
- [x] 1.3 `engines/agents/role/base.py` 改为 `from .config import ChatModelFactory, ModelConfig`，并按 ruff 判定清理失效导入；更新模块 docstring。验证：`python -m ruff check --no-cache engines/agents/role/base.py` 退出码 0 —— 该文件上一单遗留的 `I001` 与 `F401`×3 应随之清零；`F821` 0 命中。**验证结果**：通过 —— 新导入在第 26 行；第 40 行 `from dataclasses import ...` 整行删除、`pydantic.SecretStr` 与 `agentscope.credential`、四个 `ChatModel` 名一并移除；`ruff check --no-cache` 对该文件 `All checks passed!`，**上一单记录的 `I001` + `F401`×3 已清零**；无 `F821`。

## 2. 同步引用方

- [x] 2.1 `engines/agents/role/executor.py`：`ModelConfig` 改从 `.config` 导入（`from .base import BaseRole, RoleConfig` + `from .config import ModelConfig`）。验证：`python -m ruff check --no-cache engines/agents/role/executor.py` 退出码 0，且 `RoleConfig` / `BaseRole` 仍从 `.base` 取。**验证结果**：通过 —— 第 8、9 行分别为 `.base`（`BaseRole, RoleConfig`）与 `.config`（`ModelConfig`）；ruff 通过；AST 校验 `executor.py 从 .config 取 ModelConfig` / `executor.py 仍从 .base 取 RoleConfig` 双 PASS。
- [x] 2.2 `engines/agents/agents.py`：`ModelConfig` 改从 `.role.config` 导入（`from .role.base import BaseRole` + `from .role.config import ModelConfig`）。验证：`python -m ruff check --no-cache engines/agents/agents.py` 退出码 0。**验证结果**：通过 —— 第 18、19 行分别指向 `.role.base`（`BaseRole`）与 `.role.config`（`ModelConfig`）；ruff 通过；AST 校验双 PASS。
- [x] 2.3 `tests/graybox/unit/test_executor_tool_groups.py`：`ModelConfig` 改从 `engines.agents.role.config` 导入（`BaseRole` / `RoleConfig` 仍从 `engines.agents.role.base` 取），不改任何断言。验证：检索该文件的导入行指向 `engines.agents.role.config`；`python -m ruff check --no-cache tests/graybox/unit/test_executor_tool_groups.py` 退出码 0。**验证结果**：通过 —— 第 15、16 行为 `.role.base`（`BaseRole, RoleConfig`）与 `.role.config`（`ModelConfig`）；`import ModelConfig` 的断言用法（第 52 行 `ModelConfig(...)`）未改；ruff 通过；AST 校验双 PASS。

## 3. 静态等价复核（会话内可做）

- [x] 3.1 新增 AST 静态校验脚本 `temps/verify_move.py`：断言定义位置与各模块导入绑定。验证：`python temps/verify_move.py` 退出码 0 且输出 `RESULT: PASS`。**验证结果**：通过 —— 14 项检查全 PASS。**过程如实记录**：首次运行时 5 项 FAIL，原因是脚本自身 bug（`ast.ImportFrom.module` 对相对导入不含前导点，脚本用 `.config` 当键值），**不是被测代码的问题**（同一次检索已确认 `base.py:26` / `executor.py:9` / `agents.py:19` 的导入行正确）；把键值改为 `"." * level + module` 后重跑全 PASS。
- [x] 3.2 全仓检索旧导入路径无残留。验证：命中数为 0；`base.py` 自身也不再定义这三个类。**验证结果**：通过 —— 全仓检索 `role\.base import|role\.config import|from \.role import`，剩余命中全部是本次已改对的导入行（`agents.py:18-19`、`executor.py:8-9`、测试 `:15-16`）与变更单文档；**没有**任何位置再从 `role.base` 取 `ModelConfig` / `RoleSpecConfig` / `ChatModelFactory`。附带发现 `engines/agents/workflow/steps.py:16` 的 `from ..role.base import BaseRole` 只取 `BaseRole`（仍在 base.py），**无需改动**。
- [x] 3.3 平台侧零改动：记录基线指纹并逐字比对。验证：两次指纹一致。**验证结果**：通过 —— 改动前记录的基线为 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`，改动后逐字一致（`engines/ai`、`apps`、`frontend` 零变化）。

## 4. 需用户在本机终端执行的验证（本会话沙箱不可执行）

> 本会话沙箱拒绝读取 `site-packages/idna/__init__.py`，`pytest` 与任何 import 冒烟均失败（`pytest --collect-only` 亦然）。以下两条**必须**由用户在本机终端执行，未经执行不得打勾。

- [ ] 4.1 运行唯一覆盖这三个类的测试：`python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q`。验证：全部通过。理由：该测试用 `BaseRole` + `ModelConfig` + `RoleConfig` 装配角色，是本次搬移唯一会真正触达导入路径的运行验证。**验证结果（提权后实跑）**：14 passed / 1 failed。唯一失败是 `test_scratch_executor_basic_has_no_skills`（第 218 行 `role.executor_role.toolkit` 抛 `AttributeError: 'ExecutorRole' object has no attribute 'executor_role'`）。**判定为既有失败、与本次搬移无关**，依据三条：① 本次对该文件只改了第 15 行（`ModelConfig` 的来源模块，见 2.3 的改动记录），第 218 行未被触碰（该文件未被 git 跟踪，无 diff 可比）；② `executor_role` 作为**属性**全仓不存在（`engines/agents/role/executor.py:20` 里它只是 `RoleConfig` 的 name 字符串）；③ 同一文件第 203-204 行用的是正确的 `role.role.toolkit`。故本条**不打勾**，待用户决定是否把这一行陈旧断言一并修掉（属独立意图，需授权扩大范围）。
- [x] 4.2 导入冒烟：`python -c "from engines.agents.role.config import ChatModelFactory, ModelConfig, RoleSpecConfig; from engines.agents.role.base import BaseRole, RoleConfig; print('import ok')"`。验证：退出码 0，输出 `import ok`。**验证结果**：通过 —— 一次性提权（danger-full-access）后执行，退出码 0，输出 `import ok`。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     已知事实：`RoleSpecConfig` 全仓零引用，因此任何测试都不会覆盖它的实例化路径；
     本次能保证的只有「定义存在 + 模块可解析 + 绑定正确」。

     【格式检查如实记录】五个文件的 `ruff format --check --no-cache`：4 个"already formatted"，
     `config.py` 报 "would reformat"。用 `ruff format --diff` 逐条核对，全部落在**用户搬过来的那份代码**上，
     与本次插入的代码无关：① 空行里残留的空格（ModelConfig / RoleSpecConfig 的 docstring 内与
     `__post_init__` 后的两行）；② `def __post_init__` 前缺一个空行；③ 文件尾多出 2 个空行。
     本次任务清单的验证口径是 `ruff check`（lint，已全绿），格式问题按 design.md D6 的口径未纳入，
     已单独报给用户决定是否清理。

     【收口记录 2026-10-13】归档时 4.1 仍未打勾（10/11）。实跑
     `python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q` 得 14 passed / 1 failed，
     唯一失败是**既有陈旧断言**：第 218 行 `role.executor_role.toolkit`（该属性全仓不存在，
     同文件第 203-204 行用的是正确的 `role.role.toolkit`），与本次搬移无关。
     另 `config.py` 的 3 类既有格式问题（空行残留空格 / `def __post_init__` 前缺空行 / 文件尾多 2 空行）
     也未清理，同样与本次插入的代码无关。以上两者均为已报给用户的独立事项，不改变本次搬移的验收结论：
     定义位置、导入绑定、lint、导入冒烟、平台侧零改动五项证据全部通过。 -->