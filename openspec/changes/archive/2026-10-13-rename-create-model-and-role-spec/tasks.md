## 1. 改名（`engines/agents/role/base.py`）

- [x] 1.1 把 `class CreateModel:` 改名为 `class ChatModelFactory:`（第 93 行），并同步 `BaseRole.__init__` 里的构造调用（第 196 行 `ChatModelFactory(config, stream=role.stream, vision=role.vision).create()`）。验证：`ChatModelFactory` 在 `engines/agents/role/base.py` 覆盖类定义与构造调用，且 `CreateModel` 在 `engines/` 下 0 命中。**验证结果**：通过——第 93 行 `class ChatModelFactory:`、第 196 行构造调用均已改；`engines/` 全域搜 `CreateModel` 无命中。
- [x] 1.2 把 `class RoleSpec:` 改名为 `class RoleSpecConfig:`（第 68 行）。验证：`RoleSpecConfig` 命中 1 处，且**加词边界**的 `\bRoleSpec\b` 在 `engines/agents` 下 0 命中（不加词边界会把 `RoleSpecConfig` 自身算作命中，故必须加）。**验证结果**：通过——第 68 行 `class RoleSpecConfig:`；`\bRoleSpec\b` 在 `engines/` 下 13 处命中全部位于平台侧 `engines/ai/agents/**`，无 `engines/agents/` 路径。
- [x] 1.3 同步模块 docstring（第 3 行）里的 `CreateModel` 提法为新类名。验证：`ChatModelFactory` 覆盖 docstring、类定义、构造调用共 3 处。**验证结果**：通过——第 3 行现为 `` `ModelConfig` / `ChatModelFactory` 只负责建模型 ``，加第 93、196 行合计 3 处。

## 2. 复核与门禁

- [x] 2.1 全仓复核旧名残留并逐个定性归属：`CreateModel`（排除 `migrations/`）与 `\bRoleSpec\b`。验证：剩余命中只属于 Django `migrations.CreateModel(`、平台侧 `engines/ai/agents/**` 的 `RoleSpec`、`openspec/changes/archive/**` 历史文本；输出中不出现 `engines/agents/` 路径。**验证结果**：通过——`CreateModel` 在 `engines/`、`tests/` 均 0 命中；`\bRoleSpec\b` 在 `engines/` 13 处（全在 `engines/ai/agents/**`）、`tests/` 2 处（`test_agent_event_stream.py`，import 自 `engines.ai.agents`）；其余命中在 `openspec/changes/archive/**` 历史文本。
- [ ] 2.2 【未执行 · 已被后续变更取代，见文末收口记录】导入冒烟：`python -c "from engines.agents.role.base import ChatModelFactory, RoleSpecConfig"`。验证：退出码 0，无 ImportError。**未完成——本会话环境阻塞，非本次改动问题**：本会话沙箱读不到 `site-packages/idna/__init__.py`（`PermissionError`），`agentscope.agent → jsonschema → idna` 链路断裂，故该模块在本会话无法导入。已定位为环境问题：`python -c "import idna"` 单跑即失败，`python -c "import agentscope"` 单跑成功，且失败发生在第 18 行的 `agentscope` 导入处、与本改名无关。**替代证据**：已用 AST 静态校验（`temps/verify_rename.py`）确认模块可解析、类集合为 `ModelConfig / RoleSpecConfig / ChatModelFactory / RoleConfig / BaseRole`、无旧类名与旧标识符残留，`RESULT: PASS`。**真实导入冒烟待用户在本机终端执行**（沙箱外无此读限制）。
- [x] 2.3 对改动文件跑静态检查：`python -m ruff check --no-cache engines/agents/role/base.py`。验证：本次改名不引入**新增**问题；该文件既有问题按 design.md D5 不在本次范围，仅记录不修。**验证结果**：通过——改动后共 4 条，全部落在第 40 行那一行导入上（`I001` 导入块未排序 + `F401`×3：`FrozenInstanceError` / `fields` / `replace` 未使用）。这 4 条均指向 import 行，而本次改名未触碰任何 import，故非本次引入；改名前记录的既有问题码为 `E402`，实测 ruff 报的是 `I001`（已同步 design.md D5）。注：必须带 `--no-cache`，否则 ruff 写 `.ruff_cache` 会被本会话沙箱拒绝（`Failed to create temporary file`）。
- [x] 2.4 确认平台侧零改动：改动前后各跑一次 `git status --short -- engines/ai apps frontend` 并比对指纹。验证：两次输出无差异。**验证结果**：通过——改动前 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`，改动后 `lines=93 sha256=93B153A423291C9501F1437D766F425B5140F87556D233DA87BEB66AFC2CA10C`，逐字一致。

<!-- 编写约定：apply 阶段按 `- [ ]` 解析进度。
     按根 AGENTS.md「禁止主动跑全量回归」，本次只做上列定向验证，不跑全量回归。
     `ChatModelFactory` / `RoleSpecConfig` 目前均为声明后无引用点（`RoleSpecConfig` 全仓无实例化），
     故本次改名无运行期足迹，冒烟价值集中在「模块可导入」这一点上。

     【收口记录 2026-10-13】2.2 未执行即关单：它验证的导入路径 `engines.agents.role.base`
     随即被后续变更 `move-config-classes-to-role-config` 移走（这两个类搬去 `role/config.py`），
     该命令在移动后必然失败，故按「被取代」处理。改名本身已由 AST 静态校验、全仓检索复核、
     `ruff check --no-cache`、平台侧 git 指纹比对共四项证据验证通过。
     未执行根因：本会话沙箱拒绝读取 `site-packages/idna/__init__.py`，pytest 与任何 import
     冒烟在本会话均不可执行（`pytest --collect-only` 亦被拒）。 -->
