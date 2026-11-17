# engines AGENTS.md

> 层级：根 `AGENTS.md` → **本文件** → `engines/**/AGENTS.md`。进入 engines 任务时**默认必读本文件**；子目录 AGENTS 写领域增量。**冲突时更具体子目录的领域规则优先**（本文件仍管跨包红线与阅读/检查流程）。  
> 完整代码风格正文在 [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md)；**何时读规范、何时用检查技能以下方「AI 阅读与检查流程」为准**——勿跳过本流程直接改代码或忽略 rules。

## 职责

- **平台总思路**（前端展示 / 后端通道与记账 / engines 能力核心；Agent = Model + Harness）见根 [AGENTS.md](../AGENTS.md)「平台架构定位」；本文只写 engines 落地与红线。
- `engines/`：可替换引擎层——设备控制、串口日志、视觉 OCR、智能体（SOP / 角色 / 工具）运行时等。导入边界：零 `apps.*`、零 `django.*`（业务工具经注入）。
- 一级子包（一句话）：
  - `ae_harness/`：**Agent 原语层**——`create_agent`、设备工具（adb）、事件记录与报告渲染、中间件、SOP 抽象、只读知识检索。其中 `assistant/` **只服务控制台调试**。
  - `backend_bridge/`：**平台侧智能体角色的唯一落点**（后端任务 / 前端卡片用），在 `ae_harness` 原语上装配，并承接**事件落库、运行取消、报告与用量**。详见 [backend_bridge/AGENTS.md](backend_bridge/AGENTS.md)。
  - `device/`：设备引擎；对外入口是 `action`。
  - `uart_log/`：串口日志采集与处理。
  - `vision/`：页面文本识别（OCR）；主要供引擎侧工具调用。
- **依赖方向只有一条**：`backend/` →（注入）→ `engines/backend_bridge/` → `engines/ae_harness/`。`device/`、`vision/`、`uart_log/` 是底座，**不得**反向依赖 `backend_bridge` 或 `ae_harness`；需要写过程日志时经 `utils.logs`。
- 领域架构与目录细则见 [`ae_harness/AGENTS.md`](ae_harness/AGENTS.md)、[`backend_bridge/AGENTS.md`](backend_bridge/AGENTS.md) 等子文档，本文不展开。
- `engines/agents/` 正在退役（见 `openspec/changes/retire-engines-agents`）：删除前对它的任何改动**只允许**修退役相关缺陷，不得新增能力。

## 红线（禁止）

- **禁止**跳过本文件与下方「AI 阅读与检查流程」直接改 `engines/**` 代码。
- **禁止**恢复 `engines/agents/` 为包：平台角色一律经 `backend_bridge` 装配，原语一律来自 `ae_harness`。
- **ae_harness 角色**：只经 `agents/creator.create_agent` 创建；**禁止**在别处直接构造 `Agent(...)`，禁止新增第二种创建入口。
- **ae_harness 工具**：实现放 `tools/<域>/`，由该域门面函数分配（设备域 `build_adb_tools()`、只读 `build_adb_readonly_tools()`）；**禁止**业务代码直接 `import` 工具实现绑到角色。
- **提示词**：平台角色的系统提示词由调用方传入正文，来源是运营配置库，不读本地 md。`ae_harness` 不得再维护角色提示词文件，也不得把整段提示词硬编码进装配代码。
- **禁止** `device/`、`vision/`、`uart_log/` 反向依赖 `backend_bridge` 或 `ae_harness`。
- **禁止**在 engines 内随意新增自定义异常类（确有需要须先在对应子 AGENTS 立项）。
- **禁止**无关业务塞进同一文件；避免强依赖扩散与循环导入（细则见规范原文 §3 / §4）。

## AI 阅读与检查流程（必读）

**写清楚，防止忽略 `.agents/rules/`：** AI 进入 engines 相关任务时**只有本 `engines/AGENTS.md` 是默认必读项**；规范全文在 rules 里，若不在本文件写明「何时读」，容易被跳过。

**两个技能各管一段，别跑错：**

| 场景 | 技能 | 命令（cd 到技能目录） |
| --- | --- | --- |
| **读代码前**先取注释看全貌 | [`engines-docstring-check`](../.agents/skills/engines-docstring-check/SKILL.md) | `python -m scripts.docstrings read --changed`（或 `--path engines/...`） |
| **改完代码**自检注释/docstring 合规 | 同上 | `python -m scripts.docstrings check`（默认只查 git 改动行） |
| 命名 / 禁 import / 门禁机械化项 | [`engines-agents-style-check`](../.agents/skills/engines-agents-style-check/SKILL.md) | `python -m scripts.check_engines_agents_style` |

技能是**辅助**：注释是否可信、设计是否合理仍要人判断，过检 ≠ 整份规范合规。

1. **任何时候进入 engines 任务**：先读本 `engines/AGENTS.md`（职责 + 红线 + 本流程）。
2. **即将编写或修改 `engines/**` 代码时**（含补 docstring、改工具、改 role、改设备/串口/视觉等）：  
   **必须先阅读** [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) 全文（或至少与本次改动相关的章节），**禁止**未读规范就写代码。
3. **只做只读分析 / 解释 / 排障且不改 `engines/**` 代码时**：可以不读 `.agents/rules/engines-code-style.md`；但**读代码前建议先用 `engines-docstring-check read`** 拿模块字段 + 签名 + 段清单，比逐行读实现省一个量级（也顺带看出注释是否可信）。
4. **需要检查代码是否符合可自动化的规范条目时**（用户要求检查、改完自检、准备宣称合规、门禁 `engines-agents-style` 告警）：  
   **必须使用项目技能**：注释/docstring 用 [`engines-docstring-check`](../.agents/skills/engines-docstring-check/SKILL.md)（按其 `SKILL.md` 运行 `python -m scripts.docstrings check`）；命名 / 禁 import / `tool_*.py` 段序另用 [`engines-agents-style-check`](../.agents/skills/engines-agents-style-check/SKILL.md)：
   ```text
   cd .agents/skills/engines-agents-style-check
   python -m scripts.check_engines_agents_style
   ```
   两个检查器都只覆盖机械化子集；**过检 ≠ 整份规范合规**。
5. **改 Agent 装配 / 目录职责时**：另读 [`engines/ae_harness/AGENTS.md`](ae_harness/AGENTS.md) 与 [`engines/backend_bridge/AGENTS.md`](backend_bridge/AGENTS.md)。涉及 device / uart_log / vision 时再读对应子目录 AGENTS（见速查）。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 平台总思路（Model + Harness） | [../AGENTS.md](../AGENTS.md)「平台架构定位」 |
| 规范原文（风格正文） | [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) |
| 注释 / docstring 读写技能 | [`.agents/skills/engines-docstring-check/`](../.agents/skills/engines-docstring-check/) |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../.agents/skills/engines-agents-style-check/) |
| Agent 原语层 | [`engines/ae_harness/AGENTS.md`](ae_harness/AGENTS.md) |
| 平台角色落点 | [`engines/backend_bridge/AGENTS.md`](backend_bridge/AGENTS.md) |
| 设备引擎 | [engines/device/AGENTS.md](device/AGENTS.md) |
| 串口采集 | [engines/uart_log/AGENTS.md](uart_log/AGENTS.md) |
| 视觉 OCR | [engines/vision/AGENTS.md](vision/AGENTS.md) |
| OpenSpec Harness | [openspec/specs/agent-harness/spec.md](../openspec/specs/agent-harness/spec.md) |
| 门禁（非阻塞告警） | `python -m utils.check_gates --only engines-agents-style` |