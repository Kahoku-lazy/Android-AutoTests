/*
 * 智能体一次运行的流程 / 时序（人工维护，非自动采集）
 *
 * 为什么是人工的：时序讲的是"谁在什么时候调谁"，静态 AST 只能证明 import 存在，
 * 推不出调用顺序；强行从代码猜会得出看起来很像但可能错的时序图。
 * 所以这里按仓库现有文档 + 代码入口人工梳理，每一步都带 source（改代码请同步这里）。
 */
window.__FLOW__ = {
  updated: "2026-11-03",
  source: "人工维护（依据 engines/AGENTS.md、engines/agents/AGENTS.md、backend/apps/task_list/AGENTS.md 与各步骤对应代码）",
  caveat: "这是文档级时序，不是从运行日志采到的真实调用链；与代码不一致时以代码为准。",
  steps: [
    {
      key: "submit",
      label: "① 任务下发",
      actor: "前端 / 接口层",
      detail: "用户提交任务 → 接口写入任务与附件 → 后端 task_runner 经 engine_adapter 调引擎。",
      source: "backend/apps/task_list/AGENTS.md"
    },
    {
      key: "assemble",
      label: "② 角色装配",
      actor: "engines/agents · models + agent_builders",
      detail:
        "从 agent_config.yaml 装载 ModelConfig 与四分段（Role/Tools/Context/ReAct）→ models 门面按 provider 造 ChatModelBase → AgentRoleFactory 把模型与四分段装成 agentscope.Agent。Agent 只持有模型实例，不持有 ModelConfig。",
      source: "engines/agents/AGENTS.md（N1/N2/N3）"
    },
    {
      key: "orchestrate",
      label: "③ 编排进入步骤",
      actor: "engines/agents · workflow",
      detail:
        "SOP / GoalPipeline 按步骤调用 build_* 取得角色实例，把本步骤输入（需求片段、模块 KEY、历史反馈）喂给执行者；workflow 自己不创建角色、不配提示词。",
      source: "engines/agents/workflow/platform_run.py、case_goal_workflow.py"
    },
    {
      key: "run",
      label: "④ Agent 运行",
      actor: "engines/agents · Agent + tools + middleware",
      detail:
        "Agent 按 ReAct 循环推理与调用工具（工具由 tools_config 分配）；middleware 在生命周期点拦截（重试、预算、RAG 注入、Tracing、TTS）。",
      source: "engines/agents/middleware/、tools_config.py"
    },
    {
      key: "events",
      label: "⑤ 过程事件",
      actor: "engines/agents · messaging",
      detail:
        "每步事件经 event_sink 交给接收方：messages 写上屏日志、fold 折叠成轮次、record 产出结构化记录与 Token 费用。引擎不写业务库。",
      source: "engines/agents/messaging/、event_sink.py"
    },
    {
      key: "result",
      label: "⑥ 结果回写与展示",
      actor: "后端 / 前端",
      detail:
        "任务结果、事件、用量与费用由后端落库；前端任务详情页按事件流与报告展示（角色、模型、状态、次数、费用）。",
      source: "backend/apps/task_list/AGENTS.md、engines/AGENTS.md（花费与任务闭环）"
    }
  ]
};
