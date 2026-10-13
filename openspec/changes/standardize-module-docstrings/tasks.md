## 1. 套用模板（22 个模块，按目录分 5 组）

- [ ] 1.1 根目录 4 个：`agents.py`（含 `__main__`，调试路径即它）、`billing.py`、`prompt_config.py`、`tools_config.py`（顺带把"改下面的名字表即可"改成正式表述）。验证：脚本（5.1）判定这 4 个含模板；`ruff check`/`format` 通过。
- [ ] 1.2 `role/` 与 `messaging/` 4 个：`role/executor.py`、`messaging/__init__.py`（包职责 + 导出面，顺带补上 `messages.py` 的解析/用量费用/上屏三类功能）、`messaging/dialogue.py`、`messaging/messages.py`。验证：同上。
- [ ] 1.3 `prompts/` 5 个：`__init__.py`、`common_prompt.py`、`executor_prompt.py`、`planner_prompt.py`、`verifier_prompt.py`。验证：同上，**另加**"这些文件里所有字符串常量取值逐字未变"（脚本 5.1 的第 ③ 项）。
- [ ] 1.4 `tools/` 4 个：`tools/__init__.py`、`tools/tool_device.py`、`tools/tool_serial.py`、`tools/tool_wrapper.py`。**`mcp_config/mcp_config.py` 排除在外**（不可编译 + 零引用 + 归档单已定"保持现状"，详见 design D5）。验证：同上。
- [ ] 1.5 `workflow/` 4 个：`__init__.py`、`context_trim.py`、`runner.py`、`steps.py`。验证：同上。

## 2. 内容一致性

- [ ] 2.1 逐模块核对"业务功能如下"清单与实际导出/职责相符：`__init__.py` 写包职责与导出面；有 `__all__` 的模块（`prompt_config.py`、`tools/__init__.py` 等）清单需与 `__all__` 一致。验证：脚本断言有 `__all__` 的模块，其 docstring 清单条目名**全部**出现在 `__all__` 中（允许清单用中文描述而非符号名，此时跳过该断言并人工核对）。
- [ ] 2.2 核查是否存在"读取模块 docstring 当数据用"的消费点。验证：`rg -n "\.__doc__|getdoc|inspect\.getdoc" engines apps tests` 无命中（或命中处与本单涉及的 22 个模块无关）。

## 3. 静态复核

- [ ] 3.1 新增 AST 校验脚本 `temps/verify_module_docstrings.py`，断言：①21 个模块全部含 `python -m 调试路径:` 与「本模块的业务功能如下：」，即**全包 23/24 合规**（唯一例外 `mcp_config/mcp_config.py`）；②每个模块的调试路径字符串与该文件真实相对路径**一致**（防止复制串行）；③**剥离 docstring 后的 AST 与 `git show HEAD:<path>` 版本逐字相等**（零代码改动）；④`prompts/*.py` 的所有字符串常量取值逐字未变；⑤**守卫例外**：`mcp_config/mcp_config.py` 仍是不可编译状态（`py_compile` 失败）且内容未被改动 —— 一旦有人顺手改好或删掉，脚本报出提醒同步文档。验证：脚本退出码 0 且 `RESULT: PASS`。
- [ ] 3.2 `ruff check --no-cache --force-exclude` 与 `ruff format --check`（22 个文件）。验证：`All checks passed!` + `N files already formatted`；若 formatter 有要求则按其输出修好再验。
- [ ] 3.3 平台侧零改动：比对 `git status --short -- engines/ai apps frontend` 指纹。验证：改动前后逐字一致（当前基线为空状态）。

## 4. 运行验证

- [ ] 4.1 导入冒烟：`python -c` 依次导入**除 `mcp_config/mcp_config.py` 外的 21 个模块**。验证：退出码 0；并单独确认 `engines.agents.mcp_config.mcp_config` 仍是已知的不可导入状态（`SyntaxError: 'await' outside function`），证明本单确实没碰它。
- [ ] 4.2 定向测试：`python -m pytest tests/graybox/unit/test_executor_tool_groups.py tests/graybox/unit/test_ai_role_tool_subsets.py -q`。验证：全部通过（当前基线 19 passed）。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：改代码、改提示词正文、改方法 docstring、动平台侧与 AGNETS.md 本体、
     给 skills/ 供应商脚手架套模板、动 mcp_config/mcp_config.py（不可编译的示例残留，
     用户已决定保持现状）。 -->
