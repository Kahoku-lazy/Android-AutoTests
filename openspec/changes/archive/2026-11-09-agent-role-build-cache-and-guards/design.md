## 背景

角色装配链路的成本结构（本机实测，`temps/time_role_build.py`、`temps/profile_model_build.py`）：

| 环节 | 单次 | 说明 |
| --- | --- | --- |
| `load_role_spec` | 8.6 ms | 1 次整份 YAML 解析 + 1 份提示词 md + 1 份应用短卡 md |
| `get_chat_model` | 989.9 ms | `OpenAIChatModel` 构造 → `openai` 客户端 → `httpx` → 3 个 `SSLContext`，0.37 s/个 |
| `build_executor_toolkit` | 56.0 ms | 新 Toolkit + skill 目录加载器 |
| 中间件（无备用模型） | 0.0 ms | 未配置时全部跳过 |
| **一对角色** | **约 2.3 s** | 22 个角色 ≈ 25 s，且 3 对（未执行步骤）白建 |

结论：问题不在「每步新建角色」这一设计（跨步不继承上下文是有意为之），而在**每步都把模型客户端重建一遍**。

## 决策

### D1：实例复用落在 `engines.agents.models` 门面

模型实例的唯一构造点是门面（`models/AGENTS.md` 红线 3）。把缓存放到 `agent_builders` 或 workflow，等于在门面之外再开一个「实例从哪来」的入口，迟早出现第二份缓存。

- 新增 `get_or_create_chat_model(config)` 与 `clear_chat_model_cache()`：前者在 `models/chat_model.py`，后者在包入口，测试用来隔离环境变量。
- `get_chat_model(config_key)` 改为「装配置 → `get_or_create_chat_model`」。语义从「每次都新建」变为「同一配置同一循环内复用」，对外签名不变。

**替代方案（未采纳）**：process 级单例——平台每个任务在自己的 daemon 线程里 `asyncio.run`（`backend/apps/task_list/task_runner.py:429`），并发任务属于不同事件循环，共享异步客户端会触发跨循环复用风险。

### D2：缓存键 = 配置指纹 + 事件循环亲和

- **配置指纹**：`(provider, model_name, base_url, api_key, vision, stream)`。密钥是 `SecretStr` 时取明值再入键；环境变量改了（测试常 monkeypatch）自然得到新条目，不需要手动失效。
- **循环亲和**：条目额外保存事件循环的**弱引用**；取用时要求 `ref() is 当前循环`，否则重建并替换。不用 `id(loop)`——id 会在循环回收后被复用，导致「拿到已死循环的客户端」。
- 并发任务互相替换同一条目不会破坏正确性：A 已持有自己的实例引用，B 的替换只影响后续取用。

**实测副作用（可接受）**：`UI_EXECUTOR_ROLE_CONFIG` 与 `UI_VERIFIER_ROLE_CONFIG` 的连接参数完全相同（同 provider / 模型名 / 地址 / 密钥 / vision / stream），因此两者复用**同一个客户端**——22 次装配最终只建 1 个客户端，11 步用例的装配耗时从 25.2 s 降到 0.96 s（循环内实测）。角色差异在提示词、工具包与 ReAct 轮次上，不体现在客户端，故共享无副作用。

### D3：`bind_forced_handover` 幂等

当前实现直接改写 `model._call_api`。共享实例若被包装 22 次，会形成 22 层闭包（行为仍正确，但白耗调用栈，且日后排查 `_call_api` 时看不到真实入口）。加一个实例标记，已包装即原样返回。

### D4：未知分段键直接报错，不留 warning

`_merge_dataclass` 现在只遍历 dataclass 字段，多出来的键静默丢弃。选择报错而不是 warn：

- 现有 6 个角色节的 `ContextConfig` / `ReActConfig` 键集合与 dataclass 字段**完全一致**（已逐节核对），没有兼容成本；
- 「配置改了但不生效」是最贵的一类故障，warning 在日志洪流里等于没有。

报错文案同时列出未知键与合法键，避免使用者去翻 dataclass。

### D5：`__all__` 只删僵尸名，保留旧名别名

`build_executor` / `build_verifier` 是 `platform_run.py` 实际在用的别名，保留；`build_case_planner` / `build_case_writer_goal` / `build_case_verifier_goal` 三个函数已删除（`test_case_authoring_roles.py` 正在断言它们不存在），从 `__all__` 移除。

### D6：不做「按步惰性建角色」

缓存后单对成本约 0.2 s（YAML 两次 + 工具包 + 提示词），11 步全建约 2.2 s，其中未执行步骤最多浪费 0.6 s。为此引入惰性代理（`name` / `model` 需在建前可读、`IncompleteHandoverGuard` 包装顺序、重试复用同一实例）的风险大于收益，本期不做，登记在 proposal 的 Non-goals。

## 风险

| 风险 | 处置 |
| --- | --- |
| 共享实例被 `Agent` 意外改写 | 只读据：`agentscope` 的 `Agent.__init__` 仅 `self.model = model`，运行期只调用 `count_tokens` / `_call_api` / 读 `model` / `context_size`；`ChatModelBase` 构造后无惰性可变状态 |
| 跨循环共享异步客户端 | D2 的循环亲和 + 弱引用判等 |
| 测试互相污染（dummy 密钥模型残留） | 指纹含密钥；另提供 `clear_chat_model_cache()` 供测试显式清理 |
| 严格校验拦住历史 YAML | 已逐节核对当前 6 个角色节无未知键 |
