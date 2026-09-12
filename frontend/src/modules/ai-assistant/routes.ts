import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/ai-assistant', redirect: '/ai-assistant/agents' },
  { path: '/ai-assistant/agents', name: 'ai-assistant-agents',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: '平台小助手' } },
  { path: '/ai-assistant/toolbox', name: 'ai-assistant-toolbox',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: 'AI工具箱' } },
  { path: '/ai-assistant/knowledge', name: 'ai-assistant-knowledge',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: '知识库' } },
  { path: '/ai-assistant/evaluator', name: 'ai-assistant-evaluator',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: '评测中心' } },
  { path: '/ai-assistant/toolbox/skills/:skillName', name: 'ai-skill-viewer',
    component: () => import('@/modules/ai-assistant/SkillViewerPage.vue'),
    meta: { title: 'Skill 内容' } },
  { path: '/ai-assistant/agent/:agentId', name: 'ai-agent-detail',
    component: () => import('@/modules/ai-assistant/AgentDetail.vue'),
    meta: { title: '智能体详情' } },
  { path: '/ai-assistant/tasks/:taskId', name: 'ai-task-detail',
    component: () => import('@/modules/ai-assistant/TaskDetailPage.vue'),
    meta: { title: '任务详情' } },
]

export default routes
