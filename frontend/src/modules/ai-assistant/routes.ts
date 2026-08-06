import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  { path: '/ai-assistant', name: 'ai-assistant',
    component: () => import('@/modules/ai-assistant/index.vue'),
    meta: { title: 'AI 助手' } },
  { path: '/ai-assistant/agent/:agentId', name: 'ai-agent-detail',
    component: () => import('@/modules/ai-assistant/AgentDetail.vue'),
    meta: { title: '智能体详情' } },
  { path: '/ai-assistant/chat/:agentId', name: 'ai-agent-chat',
    component: () => import('@/modules/ai-assistant/ChatView.vue'),
    meta: { title: 'AI 对话' } },
]

export default routes
