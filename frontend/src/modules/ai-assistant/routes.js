export default [
  { path: '/ai-assistant', name: 'ai-assistant',
    component: () => import('@/modules/ai-assistant/index.vue') },
  { path: '/ai-assistant/agent/:agentId', name: 'ai-agent-detail',
    component: () => import('@/modules/ai-assistant/AgentDetail.vue') },
  { path: '/ai-assistant/chat/:agentId', name: 'ai-agent-chat',
    component: () => import('@/modules/ai-assistant/ChatView.vue') },
]
