/*
 * 后端一次请求的流程（人工维护，非自动采集）
 *
 * 静态 AST 只能证明 import 存在，推不出"谁先谁后"；所以这里按 backend/apps/AGENTS
 * 与实际入口人工梳理，每一步带 source。改分层/路由/写库路径请同步这里。
 */
window.__FLOW_BACKEND__ = {
  updated: "2026-11-03",
  source: "人工维护（依据 backend/apps/AGENTS.md、backend/apps/task_list/AGENTS.md 与 gateway/routing）",
  caveat: "这是文档级流程，不是从运行日志采到的真实调用链；与代码不一致时以代码为准。",
  steps: [
    {
      key: "gateway",
      label: "① 进入网关",
      actor: "backend/gateway",
      detail: "中间件解析身份（request.user_id）、判定公开路径、统一错误码与响应信封。",
      source: "backend/gateway/middleware.py"
    },
    {
      key: "urls",
      label: "② 路由分发",
      actor: "apps/<app>/urls.py",
      detail: "按 `/api/...` 命中 App 的 urlpatterns，交给对应 View / ViewSet。",
      source: "backend/apps/*/urls.py"
    },
    {
      key: "view",
      label: "③ View 只分发",
      actor: "apps/<app>/views.py",
      detail: "View 负责鉴权姿态与入参校验、序列化，然后调用本 App 的 api 层；不直接写 ORM。",
      source: "backend/apps/AGENTS.md（View 只分发）"
    },
    {
      key: "serializer",
      label: "④ 序列化与校验",
      actor: "apps/<app>/serializers.py",
      detail: "请求体/查询参数走 Serializer 校验；响应统一序列化成 snake_case JSON。",
      source: "backend/apps/AGENTS.md（契约规则）"
    },
    {
      key: "api",
      label: "⑤ 写库走 api",
      actor: "apps/<app>/api.py",
      detail: "业务写操作集中在 api.py；跨 App 写必须走对方 api.py，跨 App 读只读 Model。",
      source: "backend/apps/AGENTS.md（写库路径）"
    },
    {
      key: "respond",
      label: "⑥ 落库与响应",
      actor: "ORM / 任务链",
      detail: "事务内落库；长任务交给 task_runner → engine_adapter 调引擎，结果与事件回写后再由前端读取。",
      source: "backend/apps/task_list/AGENTS.md（执行链）"
    }
  ]
};
