## Why

同一个包里有**两个都在描述"角色配置"的类**，读者无法从代码判断该用哪个：

- `engines/agents/role/base.py` 的 `RoleConfig`：12 个字段，手写可变类，**唯一在用**（`BaseRole` 的装配参数）。
- `engines/agents/role/config.py` 的 `RoleSpecConfig`：6 个字段，`@dataclass(frozen=True)`，**全仓零实例化** —— 它是从平台侧 `engines/ai/agents/base.py` 的 `RoleSpec` 复制过来的同名异义类。

两者的字段语义还互相冲突：`toolkit`（已装配的实例）vs `tool_names`（待解析的名字）、ReAct/上下文摊平成字段 vs 收进两个 dict、`vision` 默认 `True` vs `False`。留两个只会让下一个改动者选错。

## What Changes

- `role/config.py` 的 `RoleSpecConfig` 改为承载 `RoleConfig` 的**全部 12 个字段**，保持 `@dataclass(frozen=True)`：`name` / `system_prompt` / `toolkit` / `vision=True` / `stream=True` / `max_iters=30` / `structured_output_grace_iters=3` / `stop_on_reject=True` / `trigger_ratio=0.7` / `reserve_ratio=0.2` / `tool_result_limit=400000` / `max_image_num=5`。默认值逐项照抄，不改任何数值。
- **BREAKING**（仅限该脚手架包内部）：`RoleSpecConfig` 不再提供 `role` / `prompt` / `tool_names` / `context_config` / `react_config` 五个字段（全仓零引用，且与上面 12 个字段构成两套并存）。
- `role/base.py`：删除 `RoleConfig` 类定义；导入改为 `from .config import ChatModelFactory, ModelConfig, RoleSpecConfig`；`BaseRole.__init__` 的类型注解改为 `RoleSpecConfig`；连带移除因此失效的 `Toolkit` 导入。
- 调用方改为从 `role/config.py` 取：`role/executor.py`（2 处构造）、`tests/graybox/unit/test_executor_tool_groups.py`（1 处构造）。
- 同步两处 docstring：`config.py` 模块 docstring 第 2 条（现描述的是旧字段集）、`base.py` 模块 docstring 第 4 行。
- **Non-goals**：不改字段名（`name` 保留，不换成 `role`）；不改任何默认值；不引入平台侧那层"`tool_names` → 工具包"的解析；不动 `prompt_config.py` 里重复的 `ModelConfig` / `DeviceExecutionConfig`；不动 `config.py` 末尾的 `__main__` 调试块。

## 关联文档

无关联需求编号。本次是纯重构（行为不变）：装配参数、默认值、Agent 名与提示词的来源都不变，只是把"角色配置"收敛成一个类、宿主改到 `role/config.py`。按 schema 约定在 `.openspec.yaml` 设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。类的名字与宿主文件不是可观察行为；12 个字段的语义与默认值一字未改，spec 不应变。故以 `skip_specs: true` 显式退出 specs 阶段。

## Impact

- 代码（均未被 git 跟踪，属独立实验脚手架）：`engines/agents/role/config.py`、`engines/agents/role/base.py`、`engines/agents/role/executor.py`。
- 测试（同样未被 git 跟踪）：`tests/graybox/unit/test_executor_tool_groups.py` 的导入行（第 15 行）与构造点（第 59 行）。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动。
- 依赖：`config.py` 新增 `from agentscope.tool import Toolkit`（同包已有依赖，无新依赖）；`base.py` 删除同一个导入。
- 运行验证受限：本会话沙箱拒绝读取 `site-packages`，`pytest` 与 import 冒烟在未提权时不可执行；上一单为同类验证申请的提权曾被用户拒绝。本单把"由用户在本机终端执行"写成并列路径。
