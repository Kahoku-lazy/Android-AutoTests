import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  { path: "/ai-assistant", redirect: "/ai-assistant/agents" },
  {
    path: "/ai-assistant/agents",
    name: "ai-assistant-agents",
    component: () => import("@/modules/ai-assistant/index.vue"),
    meta: { title: "平台小助手" },
  },
  {
    path: "/ai-assistant/agent/:agentId",
    name: "ai-agent-detail",
    component: () => import("@/modules/ai-assistant/AgentDetail.vue"),
    meta: { title: "智能体详情" },
  },
  {
    path: "/ai-assistant/tasks/:taskId",
    name: "ai-task-detail",
    component: () => import("@/modules/ai-assistant/TaskDetailPage.vue"),
    meta: { title: "任务详情" },
  },
]

export default routes
