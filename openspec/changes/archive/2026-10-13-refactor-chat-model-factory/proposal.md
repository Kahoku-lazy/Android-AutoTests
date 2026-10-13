## Why

`engines/agents/role/config.py` 的 `ChatModelFactory` 里有一批机器可查的重复：

- 工厂持有整个 `ModelConfig` 却只读 3 个字段，`self.config.` 在类内出现 **18 次**（实测 `engines/agents/role/config.py`：`api_key` 5、`base_url` 5、`model_name` 4、`provider` 4）。
- 同一套 `credential= / model= / stream=` 三件套重复 5 遍，其中 `credential` 的 `api_key` + `base_url` 拼装重复 4 遍。
- `create()` 用 3 段 `if` 做厂商分派，合法厂商集合隐含在分支里，报错也不告诉调用方有哪些可选。

另外 `tests/graybox/unit/test_executor_tool_groups.py:218` 有一行**既有陈旧断言**：`role.executor_role.toolkit` 引用的属性全仓不存在（`executor_role` 只是 `RoleConfig` 的 name 字符串），导致该测试文件永远是 14 passed / 1 failed。本单顺手修掉它，好让本单的 pytest 验收能闭合。

## What Changes

- `engines/agents/role/config.py`：在 `ChatModelFactory` 内新增两个私有 helper `_credential` 与 `_credential_default_endpoint`（**实例方法**，形参 `(self, credential_cls)`，读 `self.config`），把 4 处内联凭证构造收成 `self._credential(OpenAICredential)` 形式的调用（**保持现有不对称行为**）。
- `engines/agents/role/config.py`：各方法内加 `config = self.config` 局部别名，把 `self.config.` 归零。
- `engines/agents/role/config.py`：`create()` 的 `if` 链改为局部表分派，并在未知 provider 的报错里列出可选厂商（异常类型仍为 `ValueError`）。
- `tests/graybox/unit/test_executor_tool_groups.py:218`：`role.executor_role.toolkit` → `role.role.toolkit`（不改其它断言）。
- **Non-goals（A 档边界）**：不改 `ChatModelFactory(config, stream=…, vision=…)` 的构造签名与 [role/base.py](engines/agents/role/base.py) 的调用点；不删 `openai` 分支；不改未知 provider 的异常类型；不统一 `base_url` 空值语义；不动 `config.py` 末尾的 `__main__` 实验块。

## 关联文档

无关联需求编号。本单是纯重构 + 测试修补（行为不变），不改变平台对外能力，因此不进入 `dev_docs/ARCH_PRD` 的 PRD / ARCH 编号体系。按 schema 约定，纯重构在 `.openspec.yaml` 设 `skip_specs: true`。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

无。厂商分派集合（`deepseek` / `openai` / `dashscope`）与异常类型（`ValueError`）均不变；唯一的可见变化是报错消息补上合法集合，属诊断信息而非行为契约。故按 schema 约定以 `skip_specs: true` 显式退出 specs 阶段。

## Impact

- 代码：`engines/agents/role/config.py`（未跟踪的实验脚手架，不在平台 PRD 范围）。
- 测试：`tests/graybox/unit/test_executor_tool_groups.py`（同样未被 git 跟踪）—— 只改第 218 行一处属性访问，不改断言意图。
- 平台侧零改动：`engines/ai/**`、`apps/**`、`frontend/**` 不动；本次不触碰任何已跟踪文件。
- 调用点：`engines/agents/role/base.py` 的 `ChatModelFactory(config, stream=…, vision=…).create()` **不动**（A 档的定义）。
- 依赖：无新增。
- 验证能力：本会话沙箱拒绝读取 `site-packages`（`pytest` 与 import 冒烟在未提权时不可执行）；已验证「一次性提权后 pytest 可跑通」，故运行类验证按提权执行，提权被拒则转交用户本机终端。
