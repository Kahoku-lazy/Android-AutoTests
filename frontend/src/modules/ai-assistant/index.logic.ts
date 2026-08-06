/** AI 助手看板页 — 逻辑编排器（从 index.vue 提取） */
import { ref, computed, onMounted, onActivated, onUnmounted, nextTick, type Ref, type ComputedRef } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { selectPop, iconBounce } from '@/shared/animations'
import {
  listAgents, checkAgentsHealth, testAgent,
  deleteAgent as apiDeleteAgent, updateAgentModel, listTasks,
} from './api/agents'
import type { AgentRecord, TaskRecord, ViewMode, TaskFilterKey } from '@/shared/types/ai'
import { getModelOptions } from './helpers/model-config'
import {
  ROUTE_CASES,
  chatRoute,
  agentDetailRoute,
  runnerRoute,
  HEALTH_CHECK_INTERVAL_MS,
  TASK_REFRESH_INTERVAL_MS,
} from './constants'

// ── 页面配置 ──

export const PAGE_HEADER = {
  title: 'AI 助手',
  subtitle: '智能体看板贴便签，任务看板跟进度',
  icon: 'bot' as const,
  iconGradient: 'linear-gradient(135deg,#5EEAD4,#14b8a6)',
}

// ── 展示辅助 ──

const TAPE_HUES = ['mint', 'peach', 'sky', 'lilac', 'honey']
const NOTE_ROTATIONS = [-2.8, 1.6, -1.4, 2.2, -2.1, 1.2, -1.8, 2.5]

const TASK_STATUS_MAP: Record<string, string[]> = {
  pending: ['PENDING'],
  running: ['RUNNING'],
  completed: ['COMPLETED', 'SUCCESS'],
  failed: ['FAILED', 'ERROR'],
}

export const CARD_GROUPS = [
  { key: 'all' as const, label: '全部', icon: '📋' },
]

// ── 返回类型 ──

export interface AgentBoardState {
  viewMode: Ref<ViewMode>
  agents: Ref<AgentRecord[]>
  loading: Ref<boolean>
  testingId: Ref<number | null>
  confirmingId: Ref<number | null>
  healthResults: Ref<Record<number, { is_connected: boolean; last_checked?: string }>>
  pendingModels: Ref<Record<number, string>>
  tasks: Ref<TaskRecord[]>
  tasksLoading: Ref<boolean>
  activeTaskFilter: Ref<TaskFilterKey>
  taskFilterAppTabs: ComputedRef<{ key: string; label: string }[]>
  filteredTasks: ComputedRef<TaskRecord[]>
  // helpers
  PAGE_HEADER: typeof PAGE_HEADER
  TAPE_HUES: string[]
  NOTE_ROTATIONS: number[]
  noteRotation: (agent: AgentRecord) => number
  tapeHue: (agent: AgentRecord) => string
  taskRotation: (task: TaskRecord) => number
  taskTapeHue: (task: TaskRecord) => string
  agentStatusType: (agent: AgentRecord) => string
  agentStatusText: (agent: AgentRecord) => string
  agentStatusClass: (agent: AgentRecord) => string
  getModelOptions: (agent: AgentRecord) => { label: string; value: string }[]
  hasPendingModelChange: (agent: AgentRecord) => boolean
  countTasksByFilter: (key: string) => number
  // actions
  loadAgents: () => Promise<void>
  loadTasks: (opts?: { silent?: boolean }) => Promise<void>
  checkAllHealth: () => Promise<void>
  testConnection: (agent: AgentRecord) => Promise<void>
  confirmModel: (agent: AgentRecord) => Promise<void>
  deleteAgent: (agent: AgentRecord) => Promise<void>
  openAgent: (agent: AgentRecord) => void
  editAgent: (id: number) => void
  openTask: (task: TaskRecord) => void
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
  const taskTimer = ref<ReturnType<typeof setInterval> | null>(null)
  const healthResults = ref<Record<number, { is_connected: boolean; last_checked?: string }>>({})
  const pendingModels = ref<Record<number, string>>({})
  const tasks = ref<TaskRecord[]>([])
  const tasksLoading = ref(false)
  const activeTaskFilter = ref<TaskFilterKey>('all')

  // ── Derived ──

  function countTasksByFilter(key: string): number {
    const list = tasks.value
    if (key === 'all') return list.length
    const allow = TASK_STATUS_MAP[key] || []
    return list.filter(t => allow.includes(String(t.status || '').toUpperCase())).length
  }

  const taskFilterAppTabs = computed(() => [
    { key: 'all', label: `全部 (${countTasksByFilter('all')})` },
    { key: 'pending', label: `待执行 (${countTasksByFilter('pending')})` },
    { key: 'running', label: `执行中 (${countTasksByFilter('running')})` },
    { key: 'completed', label: `已完成 (${countTasksByFilter('completed')})` },
    { key: 'failed', label: `失败 (${countTasksByFilter('failed')})` },
  ])

  const filteredTasks = computed(() => {
    if (activeTaskFilter.value === 'all') return tasks.value
    const allow = TASK_STATUS_MAP[activeTaskFilter.value] || []
    return tasks.value.filter(t => allow.includes(String(t.status || '').toUpperCase()))
  })

  // ── Sticky note display ──

  function hashString(s: string, mod: number): number {
    let hash = 0
    for (const c of s) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
    return mod ? hash % mod : hash
  }

  function noteRotation(agent: AgentRecord) { return NOTE_ROTATIONS[hashString(String(agent.id), NOTE_ROTATIONS.length)] }
  function tapeHue(agent: AgentRecord) { return TAPE_HUES[hashString(agent.name || String(agent.id), TAPE_HUES.length)] }
  function taskRotation(task: TaskRecord) { return NOTE_ROTATIONS[hashString(task.run_id || '', NOTE_ROTATIONS.length)] }
  function taskTapeHue(task: TaskRecord) { return TAPE_HUES[hashString(task.agent_name || task.run_id || '', TAPE_HUES.length)] }

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
    const card = (ev as { currentTarget?: HTMLElement }).currentTarget
    if (card) selectPop(card)
    const container = dutyRosterRef.value
    if (container) {
      const mark = container.querySelector('.brand-mark')
      if (mark) iconBounce(mark)
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
    try {
      const data = await listAgents()
      if (data.status) { agents.value = data.agents; syncPendingModels() }
    } catch { ElMessage.error('加载智能体列表失败') }
    loading.value = false
    nextTick(() => animateStatusBubbles())
  }

  async function loadTasks({ silent = false }: { silent?: boolean } = {}) {
    if (!silent) tasksLoading.value = true
    try {
      const data = await listTasks({ status: 'all' })
      if (data.status) tasks.value = data.tasks || []
    } catch { if (!silent) ElMessage.error('加载任务看板失败') }
    finally { tasksLoading.value = false }
  }

  async function checkAllHealth() {
    try {
      const data = await checkAgentsHealth()
      if (data.status && data.agents) {
        for (const h of data.agents) healthResults.value[h.id] = { is_connected: h.is_connected, last_checked: h.last_checked }
        nextTick(() => animateStatusBubbles())
      }
    } catch (e) { console.error(e) }
  }

  async function testConnection(agent: AgentRecord) {
    testingId.value = agent.id
    try {
      const data = await testAgent(agent.id)
      if (data.status) {
        healthResults.value[agent.id] = { is_connected: data.connected, last_checked: new Date().toISOString() }
        if (data.connected) { ElMessage.success(`${agent.name} 连接成功`); loadAgents() }
        else ElMessage.warning(`${agent.name} 连接失败: ${(data as { error?: string }).message || '未知错误'}`)
      }
    } catch { ElMessage.error(`${agent.name} 检测请求失败`) }
    testingId.value = null
  }

  async function confirmModel(agent: AgentRecord) {
    const newModel = pendingModels.value[agent.id]
    if (!newModel || newModel === agent.model_name) return
    confirmingId.value = agent.id
    try {
      const data = await updateAgentModel(agent.id, newModel)
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
      else ElMessage.error((data as { error?: string }).message || '删除失败')
    } catch { ElMessage.error('删除请求失败，请检查网络') }
  }

  function openAgent(agent: AgentRecord) {
    if (hasPendingModelChange(agent)) { ElMessage.warning('请先点击「保存模型」确认模型'); return }
    router.push(chatRoute(agent.id))
  }
  function editAgent(id: number) { router.push(agentDetailRoute(id)) }

  function openTask(task: TaskRecord) {
    if (!task?.run_id || task._demo || String(task.run_id).startsWith('demo-')) {
      ElMessage.info('这是预览便签，真实任务创建后可进入执行页')
      return
    }
    if (task.task_type === 'case_generation') router.push(ROUTE_CASES)
    else router.push(runnerRoute(task.run_id))
  }

  // ── Lifecycle ──

  onMounted(() => {
    loadAgents(); checkAllHealth(); loadTasks()
    healthTimer.value = setInterval(checkAllHealth, HEALTH_CHECK_INTERVAL_MS)
    taskTimer.value = setInterval(() => {
      if (tasks.value.some(t => String(t.status).toUpperCase() === 'RUNNING')) loadTasks({ silent: true })
    }, TASK_REFRESH_INTERVAL_MS)
  })
  onActivated(() => {
    loadAgents(); loadTasks()
  })
  onUnmounted(() => {
    if (healthTimer.value) clearInterval(healthTimer.value)
    if (taskTimer.value) clearInterval(taskTimer.value)
  })

  return {
    viewMode, agents, loading, testingId, confirmingId, healthResults, pendingModels,
    tasks, tasksLoading, activeTaskFilter, taskFilterAppTabs, filteredTasks,
    PAGE_HEADER, TAPE_HUES, NOTE_ROTATIONS, CARD_GROUPS,
    noteRotation, tapeHue, taskRotation, taskTapeHue,
    agentStatusType, agentStatusText, agentStatusClass,
    getModelOptions, hasPendingModelChange, countTasksByFilter,
    loadAgents, loadTasks, checkAllHealth, testConnection, confirmModel, deleteAgent,
    openAgent, editAgent, openTask, onAgentCardClick,
  }
}
