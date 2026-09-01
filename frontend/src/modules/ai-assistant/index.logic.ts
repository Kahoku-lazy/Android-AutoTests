/** AI 助手看板页 — 逻辑编排器（从 index.vue 提取） */
import { ref, onMounted, onActivated, onUnmounted, nextTick, type Ref } from 'vue'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { selectPop, iconBounce } from '@/shared/animations'
import {
  listAgents, checkAgentsHealth, testAgent,
} from './api/agents'
import type { AgentRecord, ViewMode } from '@/shared/types/ai'
import {
  agentDetailRoute,
  HEALTH_CHECK_INTERVAL_MS,
} from './constants'

// ── 页面配置 ──

export const PAGE_HEADER = {
  title: 'AI 助手',
  subtitle: '智能体看板贴便签，工具箱与评测一站管理',
  icon: 'bot' as const,
  iconGradient: 'linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover))',
}

// ── 展示辅助 ──

const TAPE_HUES = ['mint', 'peach', 'sky', 'lilac', 'honey']
const NOTE_ROTATIONS = [-2.8, 1.6, -1.4, 2.2, -2.1, 1.2, -1.8, 2.5]

// ── 返回类型 ──

export interface AgentBoardState {
  viewMode: Ref<ViewMode>
  agents: Ref<AgentRecord[]>
  loading: Ref<boolean>
  agentsError: Ref<string>
  testingId: Ref<number | null>
  healthResults: Ref<Record<number, { is_connected: boolean; last_checked?: string }>>
  // helpers
  PAGE_HEADER: typeof PAGE_HEADER
  noteRotation: (agent: AgentRecord) => number
  tapeHue: (agent: AgentRecord) => string
  agentStatusText: (agent: AgentRecord) => string
  agentStatusClass: (agent: AgentRecord) => string
  // actions
  loadAgents: () => Promise<void>
  testConnection: (agent: AgentRecord) => Promise<void>
  openAgent: (agent: AgentRecord) => void
  editAgent: (id: number, routeKey?: string) => void
  onAgentCardClick: (ev: Event) => void
}

// ── Composable ──

import { useRouter } from 'vue-router'

export function useAgentBoard(dutyRosterRef: Ref<HTMLElement | null>): AgentBoardState {
  const router = useRouter()

  // ── State ──
  const viewMode = ref<ViewMode>('agents')
  const agents = ref<AgentRecord[]>([])
  const loading = ref(false)
  const testingId = ref<number | null>(null)
  const healthTimer = ref<ReturnType<typeof setInterval> | null>(null)
  const healthResults = ref<Record<number, { is_connected: boolean; last_checked?: string }>>({})
  const agentsError = ref('')

  // ── Derived ──

  // ── Sticky note display ──

  function hashString(s: string, mod: number): number {
    let hash = 0
    for (const c of s) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
    return mod ? hash % mod : hash
  }

  function noteRotation(agent: AgentRecord) { return NOTE_ROTATIONS[hashString(String(agent.id), NOTE_ROTATIONS.length)] }
  function tapeHue(agent: AgentRecord) { return TAPE_HUES[hashString(agent.name || String(agent.id), TAPE_HUES.length)] }

  // ── Status helpers ──

  function agentStatusType(agent: AgentRecord): string {
    if (agent.status !== 'active') return agent.status === 'paused' ? 'warning' : 'danger'
    const h = healthResults.value[agent.id]
    if (h && !h.is_connected) return 'danger'
    return 'success'
  }
  function agentStatusText(agent: AgentRecord): string {
    if (agent.status !== 'active') return agent.status === 'paused' ? '已暂停' : '错误'
    const h = healthResults.value[agent.id]
    if (h && !h.is_connected) return '未连通'
    return '运行中'
  }
  function agentStatusClass(agent: AgentRecord): string { return `is-${agentStatusType(agent)}` }

  // ── Animations ──

  function animateStatusBubbles() {
    const container = dutyRosterRef.value
    if (!container) return
    const bubbles = container.querySelectorAll('.ac-status-bubble')
    bubbles.forEach((el, i) => {
      animate(el as HTMLElement, {
        opacity: [0, 1], scale: [0.4, 1.14, 1], translateY: [10, -3, 0], translateX: [4, 0],
        duration: 560, delay: 90 + i * 80, ease: 'outBack(1.8)',
      })
    })
  }

  function onAgentCardClick(ev: Event) {
    const card = (ev as unknown as { currentTarget?: HTMLElement }).currentTarget
    if (card) selectPop(card as HTMLElement)
    const container = dutyRosterRef.value
    if (container) {
      const mark = container.querySelector('.brand-mark')
      if (mark) iconBounce(mark as HTMLElement)
    }
  }

  // ── Data loading ──

  async function loadAgents() {
    loading.value = true
    agentsError.value = ''
    try {
      const data = await listAgents()
      if (data.status && data.data) { agents.value = data.data.agents }
      else { agentsError.value = data.message || '加载失败' }
    } catch { agentsError.value = '加载智能体列表失败，请检查网络连接' }
    loading.value = false
    nextTick(() => animateStatusBubbles())
  }

  async function checkAllHealth() {
    try {
      const data = await checkAgentsHealth()
      if (data.status && data.data?.agents) {
        for (const h of data.data.agents) healthResults.value[h.id] = { is_connected: h.is_connected, last_checked: h.last_checked }
        nextTick(() => animateStatusBubbles())
      }
    } catch { ElMessage.error('健康检查失败') }
  }

  async function testConnection(agent: AgentRecord) {
    testingId.value = agent.id
    try {
      const data = await testAgent(agent.id)
      const payload = data.data
      if (data.status && payload) {
        healthResults.value[agent.id] = { is_connected: payload.connected ?? false, last_checked: new Date().toISOString() }
        if (payload.connected) { ElMessage.success(`${agent.name} 连接成功`); loadAgents() }
        else ElMessage.warning(`${agent.name} 连接失败: ${payload.message || '未知错误'}`)
      }
    } catch { ElMessage.error(`${agent.name} 检测请求失败`) }
    testingId.value = null
  }

  function openAgent(_agent: AgentRecord) {
    router.push('/ai-assistant/tasks')
  }
  function editAgent(id: number, routeKey?: string) { router.push({ path: agentDetailRoute(id), query: routeKey ? { route: routeKey } : {} }) }

  // ── Lifecycle ──

  onMounted(async () => {
    await loadAgents()
    checkAllHealth()
    healthTimer.value = setInterval(checkAllHealth, HEALTH_CHECK_INTERVAL_MS)
  })
  onActivated(() => {
    loadAgents()
  })
  onUnmounted(() => {
    if (healthTimer.value) clearInterval(healthTimer.value)
  })

  return {
    viewMode, agents, loading, agentsError, testingId, healthResults,
    PAGE_HEADER,
    noteRotation, tapeHue,
    agentStatusText, agentStatusClass,
    loadAgents, testConnection,
    openAgent, editAgent, onAgentCardClick,
  }
}
