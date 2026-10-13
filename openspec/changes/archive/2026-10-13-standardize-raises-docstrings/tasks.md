## 1. `role/base.py` 的注释（5 处）

- [x] 1.1 类 docstring 写明两类既定异常。验证：AST 断言类 docstring 同时含 `ValueError` 与 `RuntimeError`。**验证结果**：通过 —— 脚本 ⑥ PASS。
- [x] 1.2 `__init__` docstring：保留用户已写的格式与真实条目（`ValueError: 不支持的模型提供商`），删除不存在的 `ValueError: API 密钥不是字符串或 SecretStr 类型`。验证：AST 断言 `__init__` 的 Raises 含 `ValueError`、docstring 内不含 `SecretStr`。**验证结果**：通过 —— 脚本 ④⑤ PASS。**说明**：该 docstring 是用户先写进文件的，本次只删那一条事实错误，格式与措辞（含空行结构）未动。
- [x] 1.3 `reply` / `reply_stream` 补成「功能 + Args + Returns + Raises」。验证：AST 断言两者 Raises 含 `RuntimeError`。**验证结果**：通过 —— 脚本 ③ 对两者各 PASS。
- [x] 1.4 `interrupt` 补 `Raises`。验证：同上。**验证结果**：通过 —— 脚本 ③ PASS。触发条件按代码写准：有运行中的回复时只 `call_soon_threadsafe(task.cancel)` 并返回，只有"没有运行中的任务"才走 `asyncio.run`。
- [x] 1.5 `_require_agent` 补「功能 + Returns + Raises（`RuntimeError`）」。验证：AST 断言"有显式 raise 的方法必有 Raises 段，且列出的类型覆盖真实 raise"。**验证结果**：通过 —— 脚本 ①② PASS；⑦ 断言其 `raise` 表达式逐字未变。

## 2. `AGNETS.md` 的规则

- [x] 2.1 新增「异常与 Raises 规则」四条 + 注释格式模板：①显式 `raise` 必须有 `Raises:` 段并逐条对应；②只用内置或框架既有异常类型，禁止新增自定义异常类；③公开入口必须写明穿透异常；④工具 docstring 首行摘要是模型可见 description，`Raises:` 必须在 `Returns:` 之后。验证：检索该节含这些要点关键词。**验证结果**：通过 —— 脚本 ⑨ 对 5 个关键词全 PASS。
- [x] 2.2 （未做，按范围）`messaging:` 目录的空条目补说明 —— 本次用户只要求加规则节，未动目录说明。
- [x] 2.3 追加**模块 docstring** 格式模板（`python -m 调试路径: …` + 「本模块的业务功能如下：」+ 编号清单），与方法模板并列在同一小节；并注明"仓库现有文件在 `"""` 后带空格、`ruff format` 会判为尾随空白"。验证：检索 AGNETS.md 含该模板关键词。**验证结果**：通过 —— 脚本 ⑨ 新增关键词 `python -m 调试路径`、`本模块的业务功能如下：` 均 PASS。
- [x] 2.4 清理尾随空白：`role/base.py` 4 行、`role/config.py` 10 行（按精确扫描逐行核对）；`AGNETS.md` 的模块模板去掉 `"""` 后的空格，并把原"说明"改成**禁止规则**。验证：复查 `engines/agents` 下代码与规范文件无尾随空白；`ruff format --check` 对 `base.py` 通过。**验证结果**：通过 —— 清理 14 行与扫描结果一一对应（base.py 1/33/37/40、config.py 1/35/40/45/49/50/93/98/103/169）；`ruff format --diff base.py` 输出 **"1 file already formatted"**（该文件现已完全符合格式化器）；复查剩余的尾随空白**只**出现在 `tools/01/*.md` 两个**数据型 Markdown**（`H6810 基础测试用例.md` / `H6810自动化测试点.md`）——Markdown 行尾双空格是**硬换行语义**，明确不属清理范围，未动。

## 3. 静态复核

- [x] 3.1 新增 AST 校验脚本 `temps/verify_raises.py`。验证：`python temps/verify_raises.py` 退出码 0 且 `RESULT: PASS`。**验证结果**：通过 —— 15 项全 PASS。**过程如实记录**：⑦ 首跑 FAIL，是我**脚本里的引号比较写错**（`ast.unparse` 产出 `RuntimeError('请先调用 start()')`，我按双引号比较），改后 PASS；不是代码问题。
- [x] 3.2 `ruff check --no-cache` 与格式归属。验证：退出码 0；格式问题逐条核对归属。**验证结果**：`ruff check` → **All checks passed!**（无 `T201` / `F401` / `I001`）。`ruff format --diff` 对 `base.py` 报 **4 行**，逐条核对**均非本次新增文本**：① 模块 docstring 首行 `""" ` 的尾随空格（早前为"与 `config.py` 格式对齐"而复刻的，已在早前报告里登记为待决）；② 用户新写的 `__init__` docstring 内 3 个空行的残留空格。本次新增的类 docstring 与 4 个方法 docstring **一行都不在 diff 里**。
- [x] 3.3 平台侧零改动：指纹比对。**验证结果**：通过 —— 前后均 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`。
- [x] 3.4 登记 `config.py` 的格式化余量（当时**均非本次引入，未动**）：`ruff format` 仍会对它提三件事 —— `RoleSpecConfig` docstring 后补一个空行、`__main__` 块内删一个空行并把超长 `ModelConfig(...)` 折行、文件尾补换行；`ruff check` 仍有 1 条既有 `T201 print`。**该格式余量已由 3.5 处理完毕；`T201` 已由 3.6 删除。**
- [x] 3.5 用户要求：对 `role/config.py` 跑一次 `ruff format`。验证：`ruff format --check` 对该文件通过；两个 AST 校验脚本回归 PASS；pytest 全绿。**验证结果**：通过 —— `1 file reformatted`（140 → 145 行），formatter 实际只做三件事：① `RoleSpecConfig` docstring 收尾后补一个空行（现第 73 行）；② `__main__` 块内删一个空行、把超长 `ModelConfig(...)` 折成多行；③ 文件尾补换行。随后 `ruff format --check engines/agents/role/base.py engines/agents/role/config.py` → **"2 files already formatted"**（退出码 0）；`ruff check --no-cache` 当时仍只剩那 1 条既有 `T201 print`（**已由 3.6 删除**）；两个 AST 校验脚本（`temps/verify_raises.py`、`temps/verify_merge.py`）**均 PASS**；`pytest` **15 passed**；尾随空白复查为 **0**；平台侧指纹逐字未变。
- [x] 3.6 用户要求：删除 `role/config.py` 末尾的 `__main__` 调试块（该文件唯一的 `T201 print` 就在其中）。验证：`ruff check --no-cache` 对两个文件通过。**验证结果**：通过 —— 删掉 10 行（`if __name__ == "__main__":` 及其内的 `SecretStr` 测试与 `print`），`config.py` 177 → **135 行**；检索 `__main__` 与 `print` 均 **0 命中**；`ruff check --no-cache engines/agents/role/base.py engines/agents/role/config.py` → **`All checks passed!`**（该包 `.py` 现已零 lint 问题）；`ruff format --check` 仍为 **"2 files already formatted"**；文件尾以 `return builder()` 收尾、无多余空行；两个 AST 校验脚本（`verify_raises` / `verify_merge`）均 PASS；`pytest` **15 passed**；`engines/agents/**/*.py` 尾随空白 **0**；平台侧指纹逐字未变。

## 4. 运行验证

- [x] 4.1 `python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q`。验证：**15 passed**。**验证结果**：通过 —— `15 passed in 2.19s`（纯 docstring 改动未碰坏工具装配）。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：其余 8 处 Raises 缺口、role/config.py 的 2 处幽灵条目、
     不给不抛异常的函数加声明、不合并两处 _require_agent、不新增异常类。

     【范围记录】原始盘点覆盖全域 10 处缺口；用户指定本次只改 `role/base.py` 与 `AGNETS.md`，
     其余登记在 proposal 的 Non-goals，建议并入后续"脚手架收尾单"。 -->