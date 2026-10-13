## Context

见 `proposal.md` - Why。

现状（实测）：`engines/agents/role/config.py` 目前 156 行，含两个配置数据类、`ChatModelFactory` 五个方法，以及末尾一个 `if __name__ == "__main__":` 调试块（第 151-156 行）。`self.config.` 在类内出现 **18 次**（`api_key` 5、`base_url` 5、`model_name` 4、`provider` 4；另有 0 次在这两个数据类里）；凭证构造内联 4 处，且 DeepSeek / OpenAI **无条件传** `base_url`、只有 DashScope 判断空值。

平台侧同功能实现是函数 `create_model(config, stream=True, vision=False)`（`engines/ai/agents/base.py:84`），与本脚手架的类形态不同；平台侧也保留了同样的 `base_url` 不对称写法。

测试侧：`tests/graybox/unit/test_executor_tool_groups.py:218` 访问 `role.executor_role.toolkit`，该属性全仓不存在；同文件 203-204 行用的是正确的 `role.role.toolkit`。

## Goals / Non-Goals

- Goals：把类内的"结构性重复"降下来（`self.config.` 归零、凭证拼装收成 helper、分派换成表），且**行为一字不变**（除报错消息）；顺手让那个测试文件可以跑绿。
- Non-Goals（A 档边界）：
  - 不改接口：构造签名 `(config, stream, vision)` 与 `.create()` 保持不变，调用点不动。
  - 不做 B 档：不改模块级函数 `build_chat_model(...)`，不把 `stream` / `vision` 下沉为调用参数。
  - 不删 `openai_model()` 与 `openai` 分支，不收敛 provider 集合。
  - 不改异常类型（仍 `ValueError`），不引入 `engines.ai.registry.ConfigurationError`。
  - 不统一 `base_url` 空值语义。
  - 不动末尾 `__main__` 调试块。

## Decisions

**D1：采用 A 档（保留类与构造签名），不采用 B 档（函数形态）。**
理由：用户已选 A。B 档会推翻上一单刚定下的 `ChatModelFactory` 类名、并改调用点，收益（与平台侧形态一致）与本次目标（参数更好管理）不匹配 —— 参数管理问题在 A 档里已经解决。备选 B 档留在 Open Questions。

**D2：用两个具名 helper 把 `base_url` 的不对称"显式化"，而不是统一。**
`_credential(cls, config)` 原样传 `base_url`（DeepSeek 与 OpenAI 兼容档的现有口径）；`_credential_default_endpoint(cls, config)` 在 `base_url` 为空时省略（DashScope 的现有口径）。
理由：统一成"空则省略"会改变 DeepSeek / OpenAI 的构造行为，而平台侧 `create_model` 是**一样的不对称写法** —— 说明要么有意为之、要么从未遇到空值。在不确认 `OpenAICredential(api_key="k", base_url="")` 与省略是否等价之前，统一就是盲改。显式命名的不对称比内联的不对称更容易被下一个改动者发现。
备选：一个 helper 加 `keep_empty_base_url: bool` 开关 —— 否决，布尔开关参数是典型坏味道。

**D2 修订（apply 后按用户要求，共两次）**：两个 helper 从模块级函数移入 `ChatModelFactory`。
- 第一次落成 `@staticmethod def _credential(credential_cls, config)`（`config` 由调用处显式传入）。
- 第二次按用户「既然都在同一个类就不需要 `cls` 写法」改为**实例方法**：`def _credential(self, credential_cls)` / `def _credential_default_endpoint(self, credential_cls)`，直接读 `self.config`；4 个调用点随之去掉第二个实参（`self._credential(OpenAICredential)`）。
- **采纳实例方法付出的代价（如实记录）**：`self.config.` 从 0 回升到 **6 次**（`_credential` 2、`_credential_default_endpoint` 4），全部落在两个 helper 内，其它方法 0 次。**D6 的指标随之改写**（见 D6 修订）。
- 被否决的备选：`@staticmethod` 形态（`self.config.` 可保持 0、`config` 由调用处显式传入）—— 用户口径优先：同一个类里就用 `self`，不必再显式传参。
- `cls` 命名：无论哪种形态，都不再用 `cls` 作"凭证类"的形参名 —— 类体内 `cls` 是 classmethod 的保留约定，用它承载"凭证类"会误导读者。

**D3：`create()` 用局部表 + `.get` + 判空，不用 `try/except KeyError` 包住调用。**
表内直接放 bound method（`self.deepseek_model`），不用 `getattr(self, f"{provider}_model")` 字符串反射 —— 后者改名时 IDE 与 ruff 都抓不到。
必须避免写成 `try: return builders[provider]()`：那会把 builder **内部**抛出的 `KeyError` 误判成"未知 provider"而吞掉。

**D4：异常类型保持 `ValueError`，只把消息补成"含可选厂商"。**
这是本单唯一有意的可见变化。理由：脚手架不依赖平台的错误体系（`ConfigurationError` 来自 `engines.ai.registry`），为一个诊断信息引入跨包依赖不值；但"列出合法集合"是平台既有 fail-fast 口径，值得对齐。

**D5：顺手修测试第 218 行（用户已批）。**
`role.executor_role.toolkit` → `role.role.toolkit`。依据：`executor_role` 作为属性全仓不存在（`engines/agents/role/executor.py:20` 里它只是 `RoleConfig` 的 name 字符串）；同文件 203-204 行用的是 `role.role.toolkit`。定位为 rider：它是本单 pytest 验收能闭合的前提，不改任何断言意图。

**D6：`self.config.` 归零，含 `create()`。**
`create()` 里也加 `config = self.config`，这样全文件 `self.config.` 出现 0 次 —— 一个可被检索断言的硬指标，避免以后又慢慢长回来。

**D6 修订（同 D2 第二次修订）**：指标由「全文件 0 次」改为「**只允许出现在两个凭证 helper 内，其它方法 0 次**」（当前实测分布：`_credential` 2 次、`_credential_default_endpoint` 4 次，其它方法 0 次）。理由：实例 helper 读 `self.config` 是用户选定的形态，与「归零」互斥；指标本身仍保留，因为它依然可被机器断言（`temps/verify_refactor.py` 的 ①b），只是允许范围从"全文件"收窄到"两个方法内"。

**D7：以 `skip_specs: true` 退出 specs 阶段。**
厂商集合与异常类型不变即行为契约不变；报错消息属诊断信息。仓库既有的纯重构变更（`2026-10-08-split-agent-roles`、本会话前两单）采用同一处理。

## Risks / Trade-offs

- [重构中误改厂商分派集合] → AST 断言分派表的键集合恰为 `{deepseek, openai, dashscope}`，且仍为 `raise ValueError`。
- [把 builder 内部异常吞掉] → D3 明确用 `.get` + 判空；任务里把"不得用 try/except 包调用"写成可检索的检查点。
- [第 218 行的修法猜错] → 依据同文件既有正确写法；修完必须实跑 pytest 确认 **15 passed**（本会话需一次性提权）。
- [本会话无法执行运行验证] → 沙箱拒绝读 `site-packages/idna`；本次已验证提权后 pytest 可跑通。若提权被拒，则把 4.1 / 4.2 转为用户在本机终端执行，未执行不打勾。
- [helper 命名不合口味] → 命名是本单唯一主观项；不满意只改名字，不动结构。
- [重复又长回来] → 把 `self.config.` == 0 写进验收断言，属机器可查指标。

## Migration Plan

无部署动作：`role/config.py` 不在平台运行链路的 import 图上（`apps/` 只引同包 `tools/tool_serial.py`）。
回退策略：恢复 `create()` 的 `if` 链与 4 处内联凭证构造、删掉两个 helper 与局部别名，并把测试第 218 行改回 `role.executor_role`（不建议 —— 那会让测试重新变红）。

## Open Questions

- 是否升级到 B 档（模块级 `build_chat_model(config, *, stream, vision)`，删掉类，与平台侧 `create_model` 形态对齐）—— 不在本单，需要时另立。
- `openai` 分支的去留、以及未知 provider 是否改用 `ConfigurationError` —— 属 provider 集合收敛，另立一单（参考归档单 `2026-10-08-converge-model-providers`；注意其 D2 警告：`deepseek + vision` 走 OpenAI 兼容客户端与 `provider == "openai"` 分支是两回事，不能一起删）。
- `OpenAICredential(api_key="k", base_url="")` 与省略 `base_url` 是否等价 —— 统一语义前必须先验证。
