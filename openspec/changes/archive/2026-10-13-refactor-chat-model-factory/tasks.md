## 1. 降噪（`engines/agents/role/config.py`）

- [x] 1.1 新增两个私有 helper `_credential`（原样传 `base_url`）与 `_credential_default_endpoint`（`base_url` 为空时省略）；把 4 处内联凭证构造替换为调用，其中 DeepSeek 与 OpenAI 兼容档用前者、DashScope 用后者。验证：三个 provider 方法内不再内联 `OpenAICredential(` / `DeepSeekCredential(` / `DashScopeCredential(`；AST 断言两个 helper 的调用方正确。**验证结果**：通过 —— 检索 `credential=(OpenAICredential|DeepSeekCredential|DashScopeCredential)\(` 在方法体内 **0 命中**；AST ⑪ 证明 `_credential` 的调用方恰为 `deepseek_model` / `openai_model`，AST ⑫ 证明 `_credential_default_endpoint` 的调用方恰为 `dashscope_model`（`base_url` 的不对称被保留、只是显式化了）。**位置与形态在 5.x / 6.x 被两次修订**，本条记录的是当时的模块级函数形态。
- [x] 1.2 各方法内加 `config = self.config` 局部别名（含 `create()`），消除 provider 方法里逐处 `self.config.` 的重复（实测基线 18 次：`api_key` 5、`base_url` 5、`model_name` 4、`provider` 4）。验证：provider 方法与 `create()` 内不再直接读 `self.config`。**验证结果**：通过 —— 当时检索计数 0；6.x 修订后复检：`self.config.` 共 **6 次，全部落在两个 helper 内**（见 6.2 的 ①b），provider 方法与 `create()` 仍为 0 次。`__init__` 里的 `self.config = config`（赋值，无尾点）不受影响。
- [x] 1.3 `create()` 的 `if` 链改为局部表分派（表内放 bound method，用 `.get` + 判空，**不得**用 `try/except KeyError` 包住 builder 调用），未知 provider 仍抛 `ValueError` 且消息列出可选厂商。验证：报错行含「可选：」；`rg -n "except KeyError"` 无命中。**验证结果**：通过 —— 报错行为 `f"不支持的模型提供商: {config.provider}；可选：{', '.join(builders)}"`；`except KeyError` **0 命中**；AST ⑤/⑤b/⑥/⑦/⑧/⑨/⑩/⑯ 全部 PASS。

## 2. 修陈旧断言（`tests/graybox/unit/test_executor_tool_groups.py`）

- [x] 2.1 第 218 行 `role.executor_role.toolkit` → `role.role.toolkit`，不改任何断言意图。验证：该文件不再以 `.executor_role` 访问属性；写法与同文件第 203-204 行的 `role.role.toolkit` 一致。**验证结果**：通过 —— AST ⑬⑭ 双 PASS；更强证据见 4.1（该测试文件从 14 passed / 1 failed 变为 **15 passed**）。

## 3. 静态复核（会话内可做）

- [x] 3.1 新增 AST 静态校验脚本 `temps/verify_refactor.py`。验证：`python temps/verify_refactor.py` 退出码 0 且输出 `RESULT: PASS`。**验证结果**：通过（6.x 后为 **21 项**全 PASS）。**过程如实记录**：首次运行断言 ⑤ 报 FAIL（"create() 顶层无 if 链，实际 1 个"），是**脚本自身写错** —— design.md D3 刻意要求 `.get` + 判空，这必然产生一个 `if`。按 D3 的真实口径改为「不得与字符串常量比较」+「顶层恰好一次判空」后通过。**不是被实现代码的问题**。
- [x] 3.2 静态检查与格式归属核对。验证：`ruff check --no-cache` 退出码 0，或仅剩与本次改动无关的既有问题（逐条核对）。**验证结果**：**部分**符合预期，如实记录两点：
  - `ruff check --no-cache`：本单改动的行全部干净；`config.py` 剩 1 条 **`T201 print found`**，位于 `if __name__ == "__main__":` 调试块内的 `print(...)`。**归属：非本次改动** —— 该块是上一单归档之后由用户新加（上一单跑 ruff 时该文件 135 行、无此块，当时 `All checks passed!`），且 design.md D6 明确"不动 `__main__` 实验块"。按「只记录不扩散」处理，并已单独报给用户决定去留。
  - `ruff format --check --no-cache`：仍报 `would reformat`，4 个 hunk 里 3 个为既有问题（数据类 docstring 空行残留空格、`__init__` 空行残留空格、用户 `__main__` 的超长行与文件尾缺换行）；**1 处属本单** —— 我手工折行的 `raise ValueError(...)` 被格式化器要求收回单行（84 字符未超长），**已改**。**方法更正**：当时用"检索整份 diff 文本"判断归属，会把**上下文行**误当改动行（`@staticmethod` 就这么被误报过）；6.3 改为只过滤格式化器的 `+` 新增行。
- [x] 3.3 平台侧零改动：改动前后比对 `git status --short -- engines/ai apps frontend` 指纹。验证：两次指纹逐字一致。**验证结果**：通过 —— 前后均 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`。

## 4. 运行验证（本会话提权后执行）

- [x] 4.1 `python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q`。**验证结果**：通过 —— `15 passed in 2.79s`（一次性提权下实跑），即本单同时闭合了前两单遗留的既有失败（14/15 → 15/15）。**注意**：该次实测发生在 5.x / 6.x 两次修订**之前**，故它证明的是 1.x / 2.x 的形态。
- [x] 4.2 导入冒烟：`python -c "from engines.agents.role.config import ChatModelFactory, ModelConfig, RoleSpecConfig; print('import ok')"`。**验证结果**：通过（同上，发生于两次修订之前）。

## 5. 复核后修订（第一次：helper 移入类内 + 去掉 `cls` 形参名）

- [x] 5.1 两个 helper 从模块级函数移入 `ChatModelFactory` 并改为 `@staticmethod`；调用点改为 `self._credential(...)`。验证：AST ② 断言类外无模块级函数、④b 断言两者已是类成员。**验证结果**：通过。**该形态已在 6.x 被再次修订**（`@staticmethod` → 实例方法），本条只作历史记录。
- [x] 5.2 helper 首个形参由 `cls` 改名 `credential_cls`（类体内 `cls` 是 classmethod 的保留约定）。验证：AST ④d 断言 helper 首个形参不叫 `cls`；调用点全部位置传参，故不应改动。**验证结果**：通过 —— ④d PASS，调用点零改动。
- [x] 5.3 静态复核复跑。**验证结果**：通过 —— AST 21 项全 PASS；`ruff check` 仍只剩既有 `T201`；格式化器"新增行"中无我方标识符。

> 本组原有一条 5.4（运行时复跑）**未执行**：为它申请的沙箱提权（danger-full-access）被用户拒绝，按要求不绕路重试。因形态在 6.x 又变（调用点去掉第二个实参），该条已**合并到 6.4 一次执行**，不在此单列。

## 6. 再修订（第二次：既然在同一个类，就不用 `cls` 写法，改用 `self`）

- [x] 6.1 两个 helper 由 `@staticmethod` 改为**实例方法**：`def _credential(self, credential_cls)` / `def _credential_default_endpoint(self, credential_cls)`，直接读 `self.config`；4 个调用点去掉第二个实参（`self._credential(OpenAICredential)` / `self._credential(DeepSeekCredential)` / `self._credential_default_endpoint(DashScopeCredential)`）。验证：AST ④c 断言两者是实例方法、无装饰器、形参为 `(self, credential_cls)`；⑰ 断言调用只传 1 个位置参数。**验证结果**：通过 —— ④c / ⑰ 均 PASS。
- [x] 6.2 指标与校验脚本同步改写：D6 由「全文件 `self.config.` 为 0」改为「**只允许出现在两个凭证 helper 内，其它方法 0 次**」；脚本新增 ①b 按方法统计分布。验证：`python temps/verify_refactor.py` 的 ①b 通过。**验证结果**：通过 —— `self.config.` 共 6 次，分布 `{_credential: 2, _credential_default_endpoint: 4}`，provider 方法与 `create()` **0 次**。代价已如实记入 design.md D2 修订。
- [x] 6.3 静态复核复跑。验证：AST 全 PASS；`ruff check --no-cache` 不因本次修订产生新问题；格式化器"新增行"中不含我方标识符。**验证结果**：通过 —— AST **21 项**全 PASS；`ruff check` 仍只剩那 1 条既有 `T201`；对 `ruff format --diff` 只取 `+` 新增行过滤后**无任何我方标识符**。
- [ ] 6.4 运行时复跑（本单唯一未执行项）：`python -m pytest tests/graybox/unit/test_executor_tool_groups.py -q` → **15 passed**，以及导入冒烟 → `import ok`。**未执行 —— 提权被用户拒绝**（5.4 阶段申请的 danger-full-access 被拒，按要求不绕路重试）。**当前状态缺少运行期实测**：静态证据已足够强（④b/④c 证明两个 helper 是实例方法且形参正确、⑪⑫ 证明调用方正确、⑮/⑯ 证明类内 `self.<name>(...)` 调用与分派表的值都能解析到本类已定义方法、⑰ 证明调用实参个数与签名匹配），但"运行期确实能构造出模型"只有**两次修订之前**的实测记录（4.1）。命令原样交用户在本机终端执行。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     本单有意**不**包含：删 openai 分支、改异常类型、统一 base_url 空值语义、下沉 stream/vision。
     以上都写进 design.md 的 Non-Goals 与 Open Questions，避免实施时顺手扩大。

     【口径更正记录】1.1 与 3.2 原写"ruff 退出码 0"作为验收。实测该判据在用户新加的
     `__main__` 调试块（含 `print`）存在时不可能成立，与本单改动无关（该块在本单之前就已在文件里）。
     故 3.2 的实际判据改为"退出码 0，或仅剩与本次改动无关的既有问题（逐条核对归属）"。
     这与"我方 `raise` 折行不合格式化器口径"是两件事：后者属我方代码，已修正，未借归属说明绕过。

     【范围外改动登记】本单实施期间，用户自行改写了 `engines/agents/role/config.py` 的模块 docstring
     （现第 1-7 行，列出本模块三个类的职责）。该改动不属本单任务，登记在此以免与本次 diff 混淆。

     【收口记录 2026-10-13】归档时 6.4 未打勾（15/16）：运行时复跑（pytest 期望 15 passed + 导入冒烟）
     未执行 —— 为其申请的沙箱提权（danger-full-access）被用户拒绝，按要求未绕路重试。
     本单的运行期实测只有 4.1 / 4.2 那一次（15 passed / import ok），发生在 5.x、6.x 两次形态修订之前；
     两次修订只改私有 helper 的位置与形态、以及调用点的实参个数，静态证据见 6.1-6.3
     （④b/④c/④d/⑪/⑫/⑮/⑯/⑰ 等 21 项断言全 PASS）。
     仍未处理、已单独报给用户的两项：① `config.py` 的既有 `T201 print`（在用户自加的 `__main__` 调试块内，
     非本单改动，且 design.md D6 明确不动该块）；② 该文件 3 处既有格式 hunk
     （数据类 docstring 与 `__init__` 的空行残留空格、`__main__` 超长行、文件尾缺换行）。 -->