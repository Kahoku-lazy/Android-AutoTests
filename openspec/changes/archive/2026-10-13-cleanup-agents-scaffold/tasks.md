## 1. 补齐 9 处 `Raises:` 段

- [x] 1.1 `tools_config.py` 三处：`select_tools`（`ValueError`：名字表里有未登记工具，报错列出可选名）、`_assigned_tools`（`ValueError`：同一工具同时列入 basic 与某组）、`_skill_sources`（`TypeError`：来源既不是目录路径，也不是 `Skill` / `SkillLoaderBase`）。验证：AST 脚本判定"有 raise 且有 Raises"。**验证结果**：通过 —— 脚本 ①②③ 全 PASS（缺口 0）。
- [x] 1.2 `tools/tool_serial.py` 三处：`_parse_log_at`（`ValueError`：时间点不匹配四种支持格式）、`read_device_log` 与 `check_device_log`（`ValueError`：无可用日志来源或日志为空）。验证：同上。**验证结果**：通过。**说明**：这两个是**工具函数**，docstring 首行摘要是模型可见 description，故 `Raises:` 一律追加在 `Args:` 段**之后**（遵守 `AGNETS.md` 第 4 条的位置要求）；并额外写明它们会穿透 `_parse_log_at` 的 `ValueError`（`at` 无法解析）。
- [x] 1.3 `tools/tool_wrapper.py` 的 `call`（`DeveloperOrientedException`：工具返回 `LOG_EMPTY` 时转成开发者可见异常）；`agents.py` 的 `main`（`SystemExit`：未设置 `DEEPSEEK_API_KEY`）。验证：同上。**验证结果**：通过 —— `call` 此前**连 docstring 都没有**，本次补了完整 docstring（功能 + Args + Returns + Raises）。
- [x] 1.4 `role/config.py` 的 `create`（`ValueError`：provider 不在支持集合内，报错列出可选厂商）—— 由 2.2 一并完成。验证：AST 脚本判定 `create` 有 `Raises:`。**验证结果**：通过 —— 脚本 ⑥ PASS。
- [x] 1.5 **（脚本逮到的额外一处，已顺手修）** `tools_config.py` 的 `_tool_group` 原有 `Raises:` 只列 `ValueError`，把 `RuntimeError` 混写在 `ValueError:` 那行文字里（"basic 缺失时改为 RuntimeError"）—— 不满足规范第 1 条的"逐条写明异常类型"。已拆成 `RuntimeError: 工具包缺少 basic 组。` 与 `ValueError: 工具包中没有该组。` 两条。验证：脚本 ③ 从 FAIL 转 PASS。

## 2. 清理 `role/config.py` 的幽灵 `Raises`

- [x] 2.1 `ModelConfig` 的 docstring：删除 `ValueError: API 密钥不是字符串或 SecretStr 类型。`，保留 `FrozenInstanceError: 模型配置不可变。`。验证：脚本 ④。**验证结果**：通过 —— `ModelConfig` 的 `Raises:` 段现只剩 `FrozenInstanceError`。（`Attributes:` 里那句 `api_key: 字符串或 SecretStr 类型` 是**字段类型说明**，不是异常条目，保留不动。）
- [x] 2.2 `ChatModelFactory.__init__` 的 docstring：删两条 `ValueError`，把"不支持的模型提供商"移到 `create()`。验证：脚本 ⑤⑥。**验证结果**：通过 —— `__init__` 现无 `Raises:` 段；`create()` 有且含 `ValueError`。**说明**：两个 docstring 是用户手写的，本次只改事实错误与归属，结构与措辞风格未动。

## 3. 删除 `prompt_config.py` 的两个孤儿类

- [x] 3.1 删除 `ModelConfig`（原 :14）与 `DeviceExecutionConfig`（原 :24），同步 `__all__`，并清理因删类失效的 `dataclasses` 导入与模块 docstring 里过时的"模型连接配置"表述。验证：脚本 ⑧⑨⑪ + ruff。**验证结果**：通过 —— 该文件现已**无任何类定义**；`__all__` 为 `['CHINESE_DEMAND', 'DEEPSEEK_MODELS', 'EXECUTOR_PROMPT', 'PLANNER_PROMPT', 'VERIFIER_PROMPT', 'model_supports_image']`；`dataclass` 导入已清。另：删类后留下 2 个空行，`ruff check` 报 `I001`，已按 formatter 口径改成 1 个空行 → `All checks passed!`。
- [x] 3.2 复核提示词取用不受影响。验证：`python -c` 导入四个提示词与 `DEEPSEEK_MODELS` / `model_supports_image`。**验证结果**：通过 —— 导入冒烟 `import ok`，`prompt_config` 导出集合如上（四个提示词均在）。

## 4. `AGNETS.md` 的目录说明

- [x] 4.1 第 12 行 `messaging` 条目补说明。验证：脚本 ⑫。**验证结果**：通过 —— 现为"**存放**对话稿与消息处理：对话落库（`dialogue.py`）、工具输出与用量费用解析、上屏渲染（`messages.py`）。"
- [x] 4.2 第 19 行 `,。` 标点瑕疵顺手修正。验证：脚本 ⑬。**验证结果**：通过 —— 全文件已无 `,。`。

## 5. 静态复核

- [x] 5.1 AST 校验脚本 `temps/verify_scaffold_cleanup.py`（13 项 + 1 项报告）。验证：退出码 0 且 `RESULT: PASS`。**验证结果**：通过 —— ①15 处 `raise` 的异常类型与位置**逐字未变**（证明本单只改注释与删零引用类）②缺口 **0** ③`Raises` 覆盖 `raise` 类型 ④⑤⑥⑦ 幽灵条目清除 ⑧⑨⑩⑪ 孤儿类与导出 ⑫⑬ 规范同步。**过程如实记录**：首跑 ③⑦ 两项 FAIL —— ③ 是**真实瑕疵**（`_tool_group` 混写，见 1.5，已修）；⑦ 是**我脚本的断言过宽**（把 `Attributes:` 里的字段类型说明也算成异常条目），改成精确匹配那条幽灵文案后 PASS。
- [x] 5.2 `ruff check --no-cache --force-exclude` 与 `ruff format --check`（6 个文件）。验证：`All checks passed!` + `6 files already formatted`。**验证结果**：通过（先修了 `prompt_config.py` 的 `I001`）。
- [x] 5.3 平台侧零改动。验证：比对 `git status --short -- engines/ai apps frontend` 指纹。**验证结果**：通过 —— 本单前后该范围状态**均为空**，即 SHA256 为空串的 `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`（上一批改动已随 `ded6e62e` 提交，故基线从 93 行状态更新为空）。

## 6. 运行验证

- [x] 6.1 定向测试：`pytest tests/graybox/unit/test_executor_tool_groups.py tests/graybox/unit/test_ai_role_tool_subsets.py -q`。验证：全部通过。**验证结果**：通过 —— **19 passed**（15 + 4）。
- [x] 6.2 导入冒烟。验证：退出码 0。**验证结果**：通过 —— `import ok`（提示词、`role.config` 三个类、`tools_config` 的 `select_tools` / `register_skills` / `build_executor_toolkit`、`engines.agents.agents` 全部可导入）。
- [x] 6.3 删类影响面复核：`git grep -n "prompt_config" -- '*.py'`。验证：命中集合与改动前一致。**验证结果**：通过 —— 仍是同样 3 处：`prompts/__init__.py:1`（注释）、`role/executor.py:5`、`tests/graybox/unit/test_executor_tool_groups.py:14`，**全部只取提示词**。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：改异常类型、改运行时行为、动平台侧 engines/ai、合并两处 _require_agent、
     给不抛异常的函数加声明、动 AGNETS.md 其它条目。

     【新发现·未纳入本单，仅记录】校验脚本顺带报告：`engines/agents` 下有 **22 个模块**没有套用
     `AGNETS.md` 的模块 docstring 模板（无 `python -m 调试路径` 段），当前只有 `role/base.py`、
     `role/config.py` 等少数几个符合。这属于"规范已生效、代码未跟进"的同类问题，
     建议另立一单统一处理，不作为本单验收项。 -->