## 1. 合并到 `role/config.py`

- [x] 1.1 `RoleSpecConfig` 改为承载 `RoleConfig` 的 12 个字段，形态保持 `@dataclass(frozen=True)`，顺序与默认值逐项照抄；删掉原 `role` / `prompt` / `tool_names` / `context_config` / `react_config`；新增 `from agentscope.tool import Toolkit`；docstring 改为逐字段 Attributes；同步模块 docstring 第 2 条。验证：AST 断言字段名序列与默认值；`ruff check --no-cache` 不新增问题。**验证结果**：通过 —— AST ② 实测字段列表 `[('name', None), ('system_prompt', None), ('toolkit', None), ('vision', True), ('stream', True), ('max_iters', 30), ('structured_output_grace_iters', 3), ('stop_on_reject', True), ('trigger_ratio', 0.7), ('reserve_ratio', 0.2), ('tool_result_limit', 400000), ('max_image_num', 5)]`；③④ 装饰器与 `frozen=True` 仍在；⑤⑥⑦⑧ 五个旧字段确认移除；⑨ `Toolkit` 已导入。**运行期证据**见 4.2（默认值与原值逐项一致、字段顺序正确、frozen 生效）。
- [x] 1.2 `role/base.py` 删除 `RoleConfig` 类定义；导入改为 `from .config import ChatModelFactory, ModelConfig, RoleSpecConfig`；删除失效的 `from agentscope.tool import Toolkit`；`BaseRole.__init__` 注解改为 `RoleSpecConfig`；模块 docstring 第 4 行改为"本模块只放 `BaseRole`（角色基类）"。验证：AST 断言 `base.py` 类集合为 `{BaseRole}`；`class RoleConfig` 0 命中；`Toolkit` 仅剩 docstring 文字。**验证结果**：通过 —— AST ⑩ `base.py 只定义 BaseRole -> ['BaseRole']`；⑪ 不再导入 `Toolkit`（删除后它只剩一处 docstring 文字，故必须删导入，否则 ruff `F401`）；⑫ 从 `.config` 取三个类；⑬ `BaseRole.__init__` 的 `role` 注解已是 `RoleSpecConfig`。

## 2. 同步调用方

- [x] 2.1 `role/executor.py`：导入拆为 `from .base import BaseRole` + `from .config import ModelConfig, RoleSpecConfig`；2 处构造改名，kwargs 一字不动。验证：AST 断言两处构造名与 kwargs 集合；ruff 通过。**验证结果**：通过 —— AST ⑭⑮ 导入绑定正确；⑯ 恰 2 处 `RoleSpecConfig` 构造；⑰ 两处 kwargs 都是 `['name', 'system_prompt', 'toolkit', 'vision']`（与改前一致）；⑱ 两处仍是关键字传参、未退化成位置传参。
- [x] 2.2 `tests/graybox/unit/test_executor_tool_groups.py`：第 15 行导入改从 `engines.agents.role.config` 取，第 59 行构造改名，不改任何断言。验证：该文件 `RoleConfig` 0 命中；ruff 通过。**验证结果**：通过 —— AST ⑲⑳ 导入绑定正确；**该测试文件实跑 15 passed**（见 4.1）。

## 3. 静态复核（会话内可做）

- [x] 3.1 新增 AST 校验脚本 `temps/verify_merge.py`（21 项断言）。验证：`python temps/verify_merge.py` 退出码 0 且 `RESULT: PASS`。**验证结果**：通过 —— 21 项全 PASS。**过程如实记录**：首次运行 ㉑（全仓 `RoleConfig` 残留扫描）报 FAIL，命中全部落在 `temps/` 下（我自己的两个校验脚本 + 你早先的 `_role_log_check.py` / `_sop_run_check.py`），是**脚本把临时目录当成了源码**，不是代码残留。改为排除 `temps/` 后重跑 PASS，并把被排除的命中**显式打印**出来（不静默跳过）。
- [x] 3.2 静态检查与格式归属：`ruff check --no-cache` 覆盖本次触及的四个文件；`ruff format --diff` 只取 `+` 新增行判断归属。验证：不因本次改动产生新问题；格式化器"新增行"中不含我方标识符。**验证结果**：通过 —— `ruff check --no-cache` 四个文件合计只剩 1 条既有 `T201 print`（`config.py` 的 `__main__` 调试块，非本次改动，已单独报给用户）；无 `F401` / `F821` / `I001`；对 `ruff format --diff` 只取 `+` 新增行过滤后**无任何我方标识符**（`RoleSpecConfig` / `Toolkit` / `system_prompt` / `max_image_num` / `toolkit:` / `name: str` 均 0 命中）。
- [x] 3.3 平台侧零改动：改动前后比对 `git status --short -- engines/ai apps frontend` 指纹。验证：两次指纹逐字一致。**验证结果**：通过 —— 前后均 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`。

## 4. 运行验证

- [x] 4.1 `python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q`。验证：**15 passed**。**验证结果**：通过 —— `15 passed in 3.65s`，退出码 0。这是本次合并唯一会真正触达装配路径的运行验证（`BaseRole` + `RoleSpecConfig` + `Toolkit` 全链路）。
- [x] 4.2 默认值与 frozen 冒烟（脚本 `temps/check_merge_runtime.py`）+ 导入冒烟。验证：输出 9 个默认值等于 `RoleConfig` 原值；`frozen` 生效。**验证结果**：通过 ——
  ```
  字段顺序 = ['name', 'system_prompt', 'toolkit', 'vision', 'stream', 'max_iters',
             'structured_output_grace_iters', 'stop_on_reject', 'trigger_ratio',
             'reserve_ratio', 'tool_result_limit', 'max_image_num']
  默认值 = (True, True, 30, 3, True, 0.7, 0.2, 400000, 5)
  默认值与 RoleConfig 原值逐项一致: True
  frozen 生效: 赋值被拒（FrozenInstanceError）
  toolkit.tool_groups 内部可变（frozen 只拦重新绑定）: True
  ```
  导入冒烟 `from engines.agents.role.config import RoleSpecConfig; from engines.agents.role.base import BaseRole` → `import ok`。
  **过程如实记录**：首跑报 `ModuleNotFoundError: No module named 'engines'` —— 是**我跑脚本的方式错了**（按路径执行时 `sys.path[0]` 是 `temps/` 而非仓库根），加 `PYTHONPATH=<仓库根>` 后通过，与被测代码无关。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：改字段名（保留 name）、改默认值、引入 tool_names 解析层、
     动 prompt_config 的重复 ModelConfig / DeviceExecutionConfig、动 config.py 的 __main__ 块。

     【环境记录】本次 apply 期间会话的运行策略发生变更（文件策略 → danger-full-access、
     审批提示关闭），因此 4.1 / 4.2 直接执行，未再申请沙箱提权。 -->