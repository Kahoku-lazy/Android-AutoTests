/** AI 助手看板页 — 逻辑编排器（从 index.vue 提取） */
import { ref, onMounted, onActivated, onUnmounted, nextTick, type Ref } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { selectPop, iconBounce } from '@/shared/animations'
import {
  listAgents, checkAgentsHealth, testAgent,
  deleteAgent as apiDeleteAgent, updateAgentModel,
} from './api/agents'
import type { AgentRecord, ViewMode } from '@/shared/types/ai'
import { getModelOptions } from './helpers/model-config'
import {
  chatRoute,
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
  confirmingId: Ref<number | null>
  healthResults: Ref<Record<number, { is_connected: boolean; last_checked?: string }>>
  pendingModels: Ref<Record<number, string>>
  // helpers
  PAGE_HEADER: typeof PAGE_HEADER
  noteRotation: (agent: AgentRecord) => number
  tapeHue: (agent: AgentRecord) => string
  agentStatusText: (agent: AgentRecord) => string
  agentStatusClass: (agent: AgentRecord) => string
  getModelOptions: (agent: AgentRecord, pendingModel?: string) => { label: string; value: string }[]
  // actions
  loadAgents: () => Promise<void>
  testConnection: (agent: AgentRecord) => Promise<void>
  confirmModel: (agent: AgentRecord) => Promise<void>
  deleteAgent: (agent: AgentRecord) => Promise<void>
  openAgent: (agent: AgentRecord) => void
  editAgent: (id: number) => void
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
  const confirmingId = ref<number | null>(null)
  const healthTimer = ref<ReturnType<typeof setInterval> | null>(null)
  const healthResults = ref<Record<number, { is_connected: boolean; last_checked?: string }>>({})
  const pendingModels = ref<Record<number, string>>({})
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
  function hasPendingModelChange(agent: AgentRecord): boolean {
    return pendingModels.value[agent.id] !== agent.model_name
  }

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

  function syncPendingModels() {
    const next: Record<number, string> = {}
    for (const a of agents.value) next[a.id] = a.model_name || ''
    pendingModels.value = next
  }

  async function loadAgents() {
    loading.value = true
    agentsError.value = ''
    try {
      const data = await listAgents()
      if (data.status) { agents.value = data.agents; syncPendingModels() }
      else { agentsError.value = data.message || '加载失败' }
    } catch { agentsError.value = '加载智能体列表失败，请检查网络连接' }
    loading.value = false
    nextTick(() => animateStatusBubbles())
  }

  async function checkAllHealth() {
    try {
      const data = await checkAgentsHealth()
      if (data.status && data.agents) {
        for (const h of data.agents) healthResults.value[h.id] = { is_connected: h.is_connected, last_checked: h.last_checked }
        nextTick(() => animateStatusBubbles())
      }
    } catch { ElMessage.error('健康检查失败') }
  }

  async function testConnection(agent: AgentRecord) {
    testingId.value = agent.id
    try {
      const data = await testAgent(agent.id)
      if (data.status) {
        healthResults.value[agent.id] = { is_connected: data.connected, last_checked: new Date().toISOString() }
        if (data.connected) { ElMessage.success(`${agent.name} 连接成功`); loadAgents() }
        else ElMessage.warning(`${agent.name} 连接失败: ${(data as { message?: string }).message || '未知错误'}`)
      }
    } catch { ElMessage.error(`${agent.name} 检测请求失败`) }
    testingId.value = null
  }

  async function confirmModel(agent: AgentRecord) {
    const newModel = pendingModels.value[agent.id]
    if (!newModel || newModel === agent.model_name) return
    confirmingId.value = agent.id
    try {
      const data = await updateAgentModel(agent.id, newModel, agent.name)
      if (!data.status) { pendingModels.value[agent.id] = agent.model_name || ''; ElMessage.error('模型切换失败') }
      else { agent.model_name = newModel; ElMessage.success(`已确认使用 ${newModel}`) }
    } catch { pendingModels.value[agent.id] = agent.model_name || ''; ElMessage.error('模型切换失败') }
    confirmingId.value = null
  }

  async function deleteAgent(agent: AgentRecord) {
    try { await ElMessageBox.confirm(`确定要删除智能体「${agent.name}」吗？`, '确认删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }) }
    catch { return }
    try {
      const data = await apiDeleteAgent(agent.id)
      if (data.status) { agents.value = agents.value.filter(a => a.id !== agent.id); ElMessage.success(`已删除「${agent.name}」`) }
      else ElMessage.error(data.message || '删除失败')
    } catch { ElMessage.error('删除请求失败，请检查网络') }
  }

  function openAgent(agent: AgentRecord) {
    if (hasPendingModelChange(agent)) { ElMessage.warning('请先点击「保存模型」确认模型'); return }
    router.push(chatRoute(agent.id))
  }
  function editAgent(id: number) { router.push(agentDetailRoute(id)) }

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
    viewMode, agents, loading, agentsError, testingId, confirmingId, healthResults, pendingModels,
    PAGE_HEADER,
    noteRotation, tapeHue,
    agentStatusText, agentStatusClass,
    getModelOptions,
    loadAgents, testConnection, confirmModel, deleteAgent,
    openAgent, editAgent, onAgentCardClick,
  }
}
