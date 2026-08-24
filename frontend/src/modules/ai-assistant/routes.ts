import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/ai-assistant', redirect: '/ai-assistant/agents' },
  { path: '/ai-assistant/agents', name: 'ai-assistant-agents',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: '智能体看板' } },
  { path: '/ai-assistant/toolbox', name: 'ai-assistant-toolbox',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: 'AI工具箱' } },
  { path: '/ai-assistant/knowledge', name: 'ai-assistant-knowledge',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: '知识库' } },
  { path: '/ai-assistant/evaluator', name: 'ai-assistant-evaluator',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: '评测中心' } },
  { path: '/ai-assistant/agent/:agentId', name: 'ai-agent-detail',
    component: () => import('@/modules/ai-assistant/AgentDetail.vue'),
    meta: { title: '智能体详情' } },
  { path: '/ai-assistant/chat/:agentId', name: 'ai-agent-chat',
    component: () => import('@/modules/ai-assistant/ChatView.vue'),
    meta: { title: 'AI 对话' } },
]

export default routes
