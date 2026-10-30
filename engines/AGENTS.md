# engines AGENTS.md

> 层级：根 `AGENTS.md` → **本文件** → `engines/**/AGENTS.md`。进入 engines 任务时**默认必读本文件**；子目录 AGENTS 写领域增量。**冲突时更具体子目录的领域规则优先**（本文件仍管跨包红线与阅读/检查流程）。  
> 完整代码风格正文在 [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md)；**何时读规范、何时用检查技能以下方「AI 阅读与检查流程」为准**——勿跳过本流程直接改代码或忽略 rules。

## 职责

- **平台总思路**（前端展示 / 后端通道与记账 / engines 能力核心；Agent = Model + Harness）见根 [AGENTS.md](../AGENTS.md)「平台架构定位」；本文只写 engines 落地与红线。
- `engines/`：可替换引擎层——设备控制、串口日志、视觉 OCR、智能体（SOP / 角色 / 工具）运行时等。导入边界：零 `apps.*`、零 `django.*`（业务工具经注入）。
- 一级子包（一句话）：
  - `agents/`：控制设备任务的 SOP / 智能体角色、提示词、工具与工作流。
  - `device/`：设备引擎；对外入口是 `action`。
  - `uart_log/`：串口日志采集与处理。
  - `vision/`：页面文本识别（OCR）；主要供引擎侧工具调用。
- 领域架构与目录细则见 [`engines/agents/AGENTS.md`](agents/AGENTS.md) 等子文档，本文不展开。

## 红线（禁止）

- **禁止**跳过本文件与下方「AI 阅读与检查流程」直接改 `engines/**` 代码。
- **agents 工具**：必须 `tools/tool_*.py` 命名，且经 `tools_config.py` 分配；**禁止**业务代码直接 `import` 绑工具。
- **agents 提示词**：角色提示词**必须**经 `role_sys_prompts.py` 配置，禁止旁路硬编码绕过配置入口。
- **禁止**在 engines 内随意新增自定义异常类（确有需要须先在对应子 AGENTS 立项）。
- **禁止**无关业务塞进同一文件；避免强依赖扩散与循环导入（细则见规范原文 §3 / §4）。
- **禁止**再使用已废弃工具示例名 `test_device.py` / `test_serial.py`（应为 `tool_device.py` / `tool_serial.py`）。
- agents 角色经 `AgentRoleFactory` / `agent_builders.build_*`（语音经 `realtime_vocie_agent`）装配；改 agents 架构时仍须遵守 [`engines/agents/AGENTS.md`](agents/AGENTS.md)「创建 Agent 统一流程」。

## AI 阅读与检查流程（必读）

**写清楚，防止忽略 `.agents/rules/`：** AI 进入 engines 相关任务时**只有本 `engines/AGENTS.md` 是默认必读项**；规范全文在 rules 里，若不在本文件写明「何时读」，容易被跳过。

1. **任何时候进入 engines 任务**：先读本 `engines/AGENTS.md`（职责 + 红线 + 本流程）。
2. **即将编写或修改 `engines/**` 代码时**（含补 docstring、改工具、改 role、改设备/串口/视觉等）：  
   **必须先阅读** [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) 全文（或至少与本次改动相关的章节），**禁止**未读规范就写代码。
3. **只做只读分析 / 解释 / 排障且不改 `engines/**` 代码时**：可以不读 `.agents/rules/engines-code-style.md`。
4. **需要检查代码是否符合可自动化的规范条目时**（用户要求检查、改完自检、准备宣称合规、门禁 `engines-agents-style` 告警）：  
   **必须使用项目技能** [`.agents/skills/engines-agents-style-check/`](../.agents/skills/engines-agents-style-check/)（按其 `SKILL.md` 运行）：
   ```text
   cd .agents/skills/engines-agents-style-check
   python -m scripts.check_engines_agents_style
   ```
   检查器只覆盖机械化子集（模块 docstring、`Raises:` 与 显式 `raise`、`tool_*.py` 命名与工具 docstring 段序等）；**过检 ≠ 整份规范合规**。
5. **改 agents 架构 / 目录职责时**：另读 [`engines/agents/AGENTS.md`](agents/AGENTS.md)。涉及 RAG / 语音 / device / uart_log / vision 时再读对应子目录 AGENTS（见速查）。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 平台总思路（Model + Harness） | [../AGENTS.md](../AGENTS.md)「平台架构定位」 |
| 规范原文（风格正文） | [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../.agents/skills/engines-agents-style-check/) |
| agents 架构 | [`engines/agents/AGENTS.md`](agents/AGENTS.md) |
| RAG 子约束 | [`engines/agents/rag/AGENTS.md`](agents/rag/AGENTS.md) |
| 语音子约束 | [`engines/agents/realtime_vocie/AGENTS.md`](agents/realtime_vocie/AGENTS.md) |
| 设备引擎 | [engines/device/AGENTS.md](device/AGENTS.md) |
| 串口采集 | [engines/uart_log/AGENTS.md](uart_log/AGENTS.md) |
| 视觉 OCR | [engines/vision/AGENTS.md](vision/AGENTS.md) |
| OpenSpec Harness | [openspec/specs/agent-harness/spec.md](../openspec/specs/agent-harness/spec.md) |
| 门禁（非阻塞告警） | `python -m utils.check_gates --only engines-agents-style` |