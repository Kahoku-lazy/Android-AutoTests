# engines AGENTS.md
> **层级**：根 [AGENTS.md](../AGENTS.md) → 上级约束 `.agents/rules/engines-code-style.md`（风格正文）→ **本文件（索引）** → `.agents/docs/engines/**`（模块文档）
> 本文件**不承载模块级细则**，只做导航；平台级红线与「AI 阅读与检查流程」仍在本文件上述两节，不外置到子模块。
> **进入 engines 任务时默认必读本文件**；进某个模块改代码前，先读下表列出的文档——文档里的红线、契约、依赖方向效力等同模块级约束（更具体的模块文档优先，本文件仍管跨包红线与阅读/检查流程）。
> 完整代码风格正文在 [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md)；**何时读规范、何时用检查技能以下方「AI 阅读与检查流程」为准**——勿跳过本流程直接改代码或忽略 rules。

## 怎么用

1. 先读本文件的「[职责](#职责)」「[红线（禁止）](#红线禁止)」「[AI 阅读与检查流程（必读）](#ai-阅读与检查流程必读)」——平台级约束不随模块外置。
2. 定位要改的模块 → 读下表对应文档（一个模块一篇，按功能域分开）。
3. 跨模块改动 → 两个模块的文档都要读；依赖方向以本文件「职责」与各模块文档为准。
4. 规范原文与检查技能 → [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) 与两个技能（见文末「相关路径速查」）。

## 职责

- **平台总思路**（前端展示 / 后端通道与记账 / engines 能力核心；Agent = Model + Harness）见根 [AGENTS.md](../AGENTS.md)「平台架构定位」；本文只写 engines 落地与红线。
- `engines/`：可替换引擎层——设备控制、串口日志、视觉 OCR、智能体（SOP / 角色 / 工具）运行时等。导入边界：零 `apps.*`、零 `django.*`（业务工具经注入）。
- 一级子包（一句话）：
  - `ae_harness/`：**Agent 原语层**——`create_agent`、工具、事件记录与报告渲染、中间件、SOP 抽象、只读知识检索。不定义角色、不保存提示词、不保存流程；控制台入口已删除。
  - `eval/`：**评测原语层**——封装 deepeval：裁判模型、评测方法目录、`evaluate()` 与官方看板。不认平台角色、不落库；全仓只有这一层 import deepeval。与 `ae_harness` 同级且互不 import。
  - `backend_bridge/`：**平台侧智能体角色的唯一落点**（后端任务 / 前端卡片用），在 `ae_harness` 原语上装配，并承接**事件落库、运行取消、报告与用量**。详见 [`backend_bridge_role_assembly.md`](../.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md)。
  - `device/`：设备引擎；对外入口是 `action`。
  - `uart_log/`：串口日志采集与处理。
  - `vision/`：页面文本识别（OCR）；主要供引擎侧工具调用。
- **依赖方向只有一条**：`backend/` →（注入）→ `engines/backend_bridge/` → `engines/ae_harness/`。`device/`、`vision/`、`uart_log/` 是底座，**不得**反向依赖 `backend_bridge` 或 `ae_harness`；需要写过程日志时经 `utils.logs`。
- 领域架构与目录细则见 [`ae_harness_overview.md`](../.agents/docs/engines/ae_harness/ae_harness_overview.md)、[`backend_bridge_role_assembly.md`](../.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md) 等子文档，本文不展开。
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
| **读代码前**取签名与结构 | [`engines-docstring-check`](../.agents/skills/engines-docstring-check/SKILL.md) | `python -m scripts.docstrings read --changed`（或 `--path engines/...`） |
| **改完代码**自检工具函数 docstring | 同上 | `python -m scripts.docstrings check`（默认只查 git 改动行） |
| 命名 / 禁 import / 门禁机械化项 | [`engines-agents-style-check`](../.agents/skills/engines-agents-style-check/SKILL.md) | `python -m scripts.check_engines_agents_style` |

技能是**辅助**：设计是否合理仍要人判断，过检 ≠ 整份规范合规。

**注释规则位置（2026-11-24 变更）**：全仓代码不写注释，正文在
[`.agents/rules/python-docstring-style.md`](../.agents/rules/python-docstring-style.md)；engines 只在
[`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) §6 保留「`engines/ae_harness/tools/**` 工具函数必须写首行摘要 + `Args:`」这条追加条款
（那是交给模型的工具说明，不得删减）。检查命令不变，见上表。

1. **任何时候进入 engines 任务**：先读本 `engines/AGENTS.md`（职责 + 红线 + 本流程）。
2. **即将编写或修改 `engines/**` 代码时**（含补工具函数 docstring、改工具、改 role、改设备/串口/视觉等）：  
   **必须先阅读** [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) 全文（或至少与本次改动相关的章节），**禁止**未读规范就写代码。
3. **只做只读分析 / 解释 / 排障且不改 `engines/**` 代码时**：可以不读 `.agents/rules/engines-code-style.md`；但**读代码前建议先用 `engines-docstring-check read`** 拿签名与结构清单（代码里已无注释可读），比逐行读实现省一个量级。
4. **需要检查代码是否符合可自动化的规范条目时**（用户要求检查、改完自检、准备宣称合规、门禁 `engines-agents-style` 告警）：  
   **必须使用项目技能**：注释/docstring 用 [`engines-docstring-check`](../.agents/skills/engines-docstring-check/SKILL.md)（按其 `SKILL.md` 运行 `python -m scripts.docstrings check`）；命名 / 禁 import / `tool_*.py` 段序另用 [`engines-agents-style-check`](../.agents/skills/engines-agents-style-check/SKILL.md)：
   ```text
   cd .agents/skills/engines-agents-style-check
   python -m scripts.check_engines_agents_style
   ```
   两个检查器都只覆盖机械化子集；**过检 ≠ 整份规范合规**。
5. **改 Agent 装配 / 目录职责时**：另读 [`ae_harness_overview.md`](../.agents/docs/engines/ae_harness/ae_harness_overview.md) 与 [`backend_bridge_role_assembly.md`](../.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md)。涉及 device / uart_log / vision 时再读对应模块文档（见速查）。

## 模块 → 文档

| 模块 | 文档 | 讲什么 |
|------|------|--------|
| backend_bridge | [backend_bridge_role_assembly.md](../.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md) | 平台角色唯一落点、SOP 与单角色分工、11 条红线、与后端分工、已定事项 |
| ae_harness | [ae_harness_overview.md](../.agents/docs/engines/ae_harness/ae_harness_overview.md) | 原语层定位、AgentScope 2.0.12、禁止 import 外部功能模块 |
| eval | [eval_deepeval_wrapper.md](../.agents/docs/engines/eval/eval_deepeval_wrapper.md) | deepeval 封装、官方裁判与看板、延迟导入、不依赖 ae_harness |
| ae_harness/agents | [ae_harness_agents_agent_creation.md](../.agents/docs/engines/ae_harness_agents/ae_harness_agents_agent_creation.md) | `create_agent` 唯一出口、`AgentBundle`、角色只有三样、观测中间件准入清单 |
| ae_harness/assistant | [ae_harness_assistant_console_retired.md](../.agents/docs/engines/ae_harness_assistant/ae_harness_assistant_console_retired.md) | 控制台入口已删、6 条红线、相关路径 |
| ae_harness/event | [ae_harness_event_observation_and_report.md](../.agents/docs/engines/ae_harness_event/ae_harness_event_observation_and_report.md) | 事件记录与 HTML 报告、用量采集口径、全量模式、扩展点 |
| ae_harness/knowledge | [ae_harness_knowledge_kb_retrieval.md](../.agents/docs/engines/ae_harness_knowledge/ae_harness_knowledge_kb_retrieval.md) | 只读检索、依赖边界的代价、未挂角色、接回 Agent 步骤、快速验证 |
| ae_harness/middleware | [ae_harness_middleware_admission.md](../.agents/docs/engines/ae_harness_middleware/ae_harness_middleware_admission.md) | 三类中间件准入、硬性边界、两个异常口径、测试命令 |
| ae_harness/tools | [ae_harness_tools_domain_tools.md](../.agents/docs/engines/ae_harness_tools/ae_harness_tools_domain_tools.md) | 按域分工具、目录准入门禁、返回契约、视觉定位精度 |
| ae_harness/workflow | [ae_harness_workflow_sop_abstraction.md](../.agents/docs/engines/ae_harness_workflow/ae_harness_workflow_sop_abstraction.md) | SOP / goal / team 抽象、步骤 YAML 字段、6 条红线、已知限制 |
| device | [device_control_engine.md](../.agents/docs/engines/device/device_control_engine.md) | `action` 对外入口、6 条红线、AI 阅读与检查流程 |
| uart_log | [uart_log_serial_capture.md](../.agents/docs/engines/uart_log/uart_log_serial_capture.md) | 端口检测 / 接收 / 落盘 / 开关、`MAX_PORTS`、6 条红线 |
| vision | [vision_ocr_engine.md](../.agents/docs/engines/vision/vision_ocr_engine.md) | cnocr 懒加载、坐标口径、调用面、5 条红线 |

## 暂无模块文档的目录

| 目录 | 现状 |
|------|------|
| `engines/utils` | 无模块文档（`io_files.py` 为通用文件 IO 辅助） |

该目录下的改动，按本文件「职责」「红线」「AI 阅读与检查流程」执行；需沉淀模块口径时新增
`.agents/docs/engines/{module}/{module}_{feature}.md` 并回到本表登记。

## 相关路径速查

| 用途 | 路径 |
|------|------|
| 平台总思路（Model + Harness） | [../AGENTS.md](../AGENTS.md)「平台架构定位」 |
| 规范原文（风格正文） | [`.agents/rules/engines-code-style.md`](../.agents/rules/engines-code-style.md) |
| 注释 / docstring 读写技能 | [`.agents/skills/engines-docstring-check/`](../.agents/skills/engines-docstring-check/) |
| 风格检查技能 | [`.agents/skills/engines-agents-style-check/`](../.agents/skills/engines-agents-style-check/) |
| Agent 原语层 | [`ae_harness_overview.md`](../.agents/docs/engines/ae_harness/ae_harness_overview.md) |
| 平台角色落点 | [`backend_bridge_role_assembly.md`](../.agents/docs/engines/backend_bridge/backend_bridge_role_assembly.md) |
| 设备引擎 | [device_control_engine.md](../.agents/docs/engines/device/device_control_engine.md) |
| 串口采集 | [uart_log_serial_capture.md](../.agents/docs/engines/uart_log/uart_log_serial_capture.md) |
| 视觉 OCR | [vision_ocr_engine.md](../.agents/docs/engines/vision/vision_ocr_engine.md) |
| OpenSpec Harness | [openspec/specs/agent-harness/spec.md](../openspec/specs/agent-harness/spec.md) |
| 门禁（非阻塞告警） | `python -m utils.check_gates --only engines-agents-style` |
