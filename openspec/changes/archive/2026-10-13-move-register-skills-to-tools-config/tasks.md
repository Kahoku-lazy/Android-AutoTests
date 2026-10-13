## 1. `tools_config.py` 接收技能注册

- [x] 1.1 新增 `register_skills(toolkit, skills, *, scan_subdir=True, group_name=None)` 与四个私有辅助；新增 `_SkillSource`、`import os`、`Sequence`、`Skill`、`SkillLoaderBase`。验证：AST 断言五个函数存在且签名正确；ruff 无新增问题。**验证结果**：通过 —— AST ⑥（五个模块函数齐全）PASS；`ruff check --no-cache` 四个文件 **`All checks passed!`**。
- [x] 1.2 `_skill_sources` 复用既有 `resolve_skill_dirs`，不复制 `_resolve_skill_dir`。验证：AST 断言不存在 `_resolve_skill_dir`；运行期等价断言。**验证结果**：通过 —— AST ⑦（未复制）⑧（体内确有 `resolve_skill_dirs([directory])[0]`）PASS；5.2 实测解析结果为 `D:\Github\Android-AutoTests\engines\agents\skills\executor`，即 `tools_config` 的 `_REPO_ROOT`（`parents[2]`）口径正确，**没有抄成 `base.py` 那套 `parents[3]`**。

## 2. `role/base.py` 移除

- [x] 2.1 删除六个成员与 `_REPO_ROOT`、`_SkillSource`，按 ruff 清理失效导入。验证：AST 断言成员集合恰为 13 个；六个名字与两个常量 0 命中；ruff 通过。**验证结果**：通过 —— AST ①（`BaseRole` 成员**恰为** 13 个，无多无少）、②（六个名字逐个 0 命中）、③（`_REPO_ROOT` / `_SkillSource` 0 命中）、④（不再 import `os` / `pathlib` / `collections.abc` / `agentscope.skill`）、⑤（仍 import `asyncio`）全 PASS；ruff `All checks passed!`（无 `F401` / `F841`）。

## 3. 同步调用方

- [x] 3.1 `executor.py` 导入 `register_skills` 并改调模块函数。验证：AST 断言导入与调用形态；全仓 `.register_skills(` 0 命中。**验证结果**：通过 —— AST ⑨（已导入）⑩（不再出现 `self.register_skills`）⑫（`engines/` 与 `tests/` 全域 `.register_skills(` 0 命中）PASS；导入行因超长改为括号多行（含 `register_skills` 后单行会超 100 列）。
- [x] 3.2 测试两条用例改为对 `toolkit` 调模块函数，**断言语义一条不改**。验证：AST 断言导入来源；ruff 不报 `F841`。**验证结果**：通过 —— AST ⑪（从 `tools_config` 取到 `register_skills`）PASS；两条用例的断言逐字保留（含 `pytest.raises(ValueError, match="missing-group")`）；`_role(...)` 局部变量已按 D6 去掉，ruff 无 `F841`；5.1 实跑 15 passed。

## 4. 静态复核（会话内可做）

- [x] 4.1 新增 AST 校验脚本 `temps/verify_skills.py`。验证：`python temps/verify_skills.py` 退出码 0 且 `RESULT: PASS`。**验证结果**：通过 —— **25 项全 PASS**（本轮脚本一次通过，无需返工）。
- [x] 4.2 静态检查与格式归属。**验证结果**：通过 —— 四个文件 `All checks passed!`（无 `F401` / `F821` / `F841` / `I001` / `T201`）；`ruff format --diff` 只取 `+` 新增行过滤后无任何我方标识符。
- [x] 4.3 平台侧零改动：指纹比对。**验证结果**：通过 —— 前后均 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`。

## 5. 运行验证

- [x] 5.1 `python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q`。验证：**15 passed**。**验证结果**：通过 —— `15 passed in 4.26s`（含被改写的两条 `register_skills` 用例与 `ExecutorRole` 装配用例）。
- [x] 5.2 路径解析等价 + 技能确实挂上（`temps/check_skills_runtime.py`）。验证：脚本退出码 0。**验证结果**：通过 ——
  ```
  tools_config 推出的仓库根: D:\Github\Android-AutoTests
  期望的技能目录:            D:\Github\Android-AutoTests\engines\agents\skills\executor
  basic 组加载器数: 1
  解析出的目录:              D:\Github\Android-AutoTests\engines\agents\skills\executor   ← 与期望逐字相等
  未知组 -> ValueError: 工具包中不存在工具组: missing-group
  缺 basic 组 -> RuntimeError: 工具包缺少 basic 组
  非法类型 -> TypeError: skill 来源必须是目录路径、Skill 或 SkillLoader，收到 int
  ```
  另覆盖：重复注册同一目录不增加加载器数（幂等）、绝对路径原样保留、指定组挂载、空串/空白跳过（0 个加载器）。
  **过程如实记录**：首跑在"缺 basic 组应抛 `RuntimeError`"这条上失败 —— 是**我脚本的假设错了**（`Toolkit()` 自带 `basic` 组，实测 `['basic']`），不是代码问题。改用只提供 `.tool_groups = []` 的替身后通过。**顺带得到一个事实**：`agentscope.tool.Toolkit()` 默认就带 `basic` 组，所以那条 `RuntimeError("工具包缺少 basic 组")` 属防御性分支，正常构造路径触发不到。
- [x] 5.3 成员与导入冒烟。验证：退出码 0。**验证结果**：通过 —— `BaseRole` 公开成员为
  `['_context_config', '_interrupt_paused', '_react_config', '_reply', '_reply_stream', '_require_agent', '_running', '_user_msg', 'interrupt', 'reply', 'reply_stream', 'start']`（连同 `__init__` 共 13 个），**不含** `register_skills`；`register_skills` 已可从 `engines.agents.tools_config` 导入。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：折进 build_executor_toolkit、改技能目录内容、改异常语义。

     【环境记录】本次 apply 期间会话为完全访问、审批提示关闭，运行验证直接执行，未申请沙箱提权。 -->