<script setup>

import AppTabs from "@/shared/components/AppTabs.vue";
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { selectPop, iconBounce } from '@/shared/animations.js'
import { animate } from 'animejs'
import { ElMessageBox, ElMessage } from 'element-plus'
import { listAgents, checkAgentsHealth, testAgent, deleteAgent as apiDeleteAgent, updateAgentModel, listTasks } from './api.js'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import WbLoader from './components/WbLoader.vue'
import AgentStickyNote from './components/AgentStickyNote.vue'
import TaskStickyNote from './components/TaskStickyNote.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import KnowledgeBase from './KnowledgeBase.vue'
import EvaluatorTab from './EvaluatorTab.vue'
import ToolboxPanel from './components/ToolboxPanel.vue'

const router = useRouter()
const viewMode = ref('agents')  // 'agents' | 'toolbox' | 'knowledge' | 'evaluator'
const agents = ref([])
const loading = ref(false)
const testingId = ref(null)
const confirmingId = ref(null)
const healthTimer = ref(null)
const taskTimer = ref(null)
const healthResults = ref({})
const pendingModels = ref({})
const tasks = ref([])
const tasksLoading = ref(false)

// 任务状态 Tabs（label 带数量）
const activeTaskFilter = ref('all')
const TASK_STATUS_MAP = {
  pending: ['PENDING'],
  running: ['RUNNING'],
  completed: ['COMPLETED', 'SUCCESS'],
  failed: ['FAILED', 'ERROR'],
}

function countTasksByFilter(key) {
  const list = tasks.value || []
  if (key === 'all') return list.length
  const allow = TASK_STATUS_MAP[key] || []
  return list.filter((t) => allow.includes(String(t.status || '').toUpperCase())).length
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
  return tasks.value.filter((t) => allow.includes(String(t.status || '').toUpperCase()))
})

const TAPE_HUES = ['mint', 'peach', 'sky', 'lilac', 'honey']
const NOTE_ROTATIONS = [-2.8, 1.6, -1.4, 2.2, -2.1, 1.2, -1.8, 2.5]

function noteRotation(agent) {
  let hash = 0
  for (const c of String(agent.id)) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return NOTE_ROTATIONS[hash % NOTE_ROTATIONS.length]
}
function tapeHue(agent) {
  let hash = 0
  for (const c of String(agent.name || agent.id)) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return TAPE_HUES[hash % TAPE_HUES.length]
}
function taskRotation(task) {
  let hash = 0
  for (const c of String(task.run_id || '')) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return NOTE_ROTATIONS[hash % NOTE_ROTATIONS.length]
}
function taskTapeHue(task) {
  let hash = 0
  for (const c of String(task.agent_name || task.run_id || '')) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return TAPE_HUES[hash % TAPE_HUES.length]
}

onMounted(() => {
  loadAgents()
  checkAllHealth()
  loadTasks()
  healthTimer.value = setInterval(checkAllHealth, 30 * 60 * 1000)
  taskTimer.value = setInterval(() => {
    const hasRunning = tasks.value.some((t) => String(t.status).toUpperCase() === 'RUNNING')
    if (hasRunning) loadTasks({ silent: true })
  }, 15000)
})
onUnmounted(() => {
  clearInterval(healthTimer.value)
  clearInterval(taskTimer.value)
})

async function loadAgents() {
  loading.value = true
  try {
    const data = await listAgents()
    if (data.ok) {
      agents.value = data.agents
      syncPendingModels()
    }
  } catch { ElMessage.error('加载智能体列表失败') }
  loading.value = false
  nextTick(() => animateStatusBubbles())
}

/** 接口为空时展示的预览便签（demo_ 前缀，不可进执行页） */
async function loadTasks({ silent = false } = {}) {
  if (!silent) tasksLoading.value = true
  try {
    const data = await listTasks({ status: 'all' })
    if (data.ok) tasks.value = data.tasks || []
  } catch {
    if (!silent) ElMessage.error('加载任务看板失败')
  } finally {
    tasksLoading.value = false
  }
}

function openTask(task) {
  if (!task?.run_id || task._demo || String(task.run_id).startsWith('demo-')) {
    ElMessage.info('这是预览便签，真实任务创建后可进入执行页')
    return
  }
  if (task.task_type === 'case_generation') {
    router.push('/cases')
  } else {
    router.push(`/runner?run=${encodeURIComponent(task.run_id)}`)
  }
}

function syncPendingModels() {
  const next = {}
  for (const a of agents.value) next[a.id] = a.model_name
  pendingModels.value = next
}

function hasPendingModelChange(agent) {
  return pendingModels.value[agent.id] !== agent.model_name
}

function animateStatusBubbles() {
  const bubbles = document.querySelectorAll('.duty-roster .ac-status-bubble')
  bubbles.forEach((el, i) => {
    animate(el, {
      opacity: [0, 1],
      scale: [0.4, 1.14, 1],
      translateY: [10, -3, 0],
      translateX: [4, 0],
      duration: 560,
      delay: 90 + i * 80,
      ease: 'outBack(1.8)',
    })
  })
}

// ── Health ──
async function checkAllHealth() {
  try {
    const data = await checkAgentsHealth()
    if (data.ok && data.agents) {
      for (const h of data.agents) {
        healthResults.value[h.id] = { is_connected: h.is_connected, last_checked: h.last_checked }
      }
      nextTick(() => animateStatusBubbles())
    }
  } catch (e) { console.error(e); }
}

async function testConnection(agent) {
  testingId.value = agent.id
  try {
    const data = await testAgent(agent.id)
    if (data.ok) {
      healthResults.value[agent.id] = { is_connected: data.connected, last_checked: new Date().toISOString() }
      if (data.connected) {
        ElMessage.success(`${agent.name} 连接成功，检测到 ${data.available_models.length} 个可用模型`)
        loadAgents()
      } else {
        ElMessage.warning(`${agent.name} 连接失败: ${data.error || '未知错误'}`)
      }
    }
  } catch (e) {
    ElMessage.error(`${agent.name} 检测请求失败`)
  }
  testingId.value = null
}

// ── Delete ──
async function deleteAgent(agent) {
  try {
    await ElMessageBox.confirm(
      `确定要删除智能体「${agent.name}」吗？此操作不可恢复。`,
      '确认删除',
      { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
    )
  } catch { return }  // 用户取消
  try {
    const data = await apiDeleteAgent(agent.id)
    if (data.ok) {
      agents.value = agents.value.filter(a => a.id !== agent.id)
      ElMessage.success(`已删除「${agent.name}」`)
    } else {
      ElMessage.error(data.error || '删除失败')
    }
  } catch { ElMessage.error('删除请求失败，请检查网络') }
}

// ── Status helpers ──
function agentStatusType(agent) {
  if (agent.status !== 'active') return agent.status === 'paused' ? 'warning' : 'danger'
  const h = healthResults.value[agent.id]
  if (h && !h.is_connected) return 'danger'
  return 'success'
}
function agentStatusText(agent) {
  if (agent.status !== 'active') return agent.status === 'paused' ? '已暂停' : '错误'
  const h = healthResults.value[agent.id]
  if (h && !h.is_connected) return '未连通'
  return '运行中'
}
function agentStatusClass(agent) {
  return `is-${agentStatusType(agent)}`
}

// ── Model selector ──
const builtinModels = {
  dashscope: ['qwen-max','qwen-plus','qwen-turbo','qwen3-235b'],
  openai: ['gpt-4o','gpt-4-turbo','gpt-3.5-turbo','o4-mini'],
  anthropic: ['claude-fable-5','claude-opus-4-8','claude-sonnet-4-6'],
  deepseek: ['deepseek-v4-flash','deepseek-v4-pro','deepseek-chat','deepseek-reasoner'],
  custom: [],
}
const customProviderModels = {
  deepseek: ['deepseek-v4-flash','deepseek-v4-pro','deepseek-chat','deepseek-reasoner'],
}

function getModelOptions(agent) {
  const builtin = builtinModels[agent.model_provider] || []
  const detected = (agent.available_models && Array.isArray(agent.available_models))
    ? agent.available_models : []
  let customModels = []
  const searchText = [(agent.model_provider || ''), (agent.name || ''), (agent.model_name || '')].join(' ').toLowerCase()
  for (const [key, models] of Object.entries(customProviderModels)) {
    if (searchText.includes(key)) { customModels = models; break }
  }
  const all = [...new Set([agent.model_name, pendingModels.value[agent.id], ...builtin, ...customModels, ...detected].filter(Boolean))]
  return all.map(m => ({ label: m, value: m }))
}

async function confirmModel(agent) {
  const newModel = pendingModels.value[agent.id]
  if (!newModel || newModel === agent.model_name) return
  confirmingId.value = agent.id
  try {
    const data = await updateAgentModel(agent.id, newModel)
    if (!data.ok) {
      pendingModels.value[agent.id] = agent.model_name
      ElMessage.error('模型切换失败')
    } else {
      agent.model_name = newModel
      ElMessage.success(`已确认使用 ${newModel}`)
    }
  } catch (e) {
    pendingModels.value[agent.id] = agent.model_name
    ElMessage.error('模型切换失败')
    console.error(e);
  }
  confirmingId.value = null
}

function openAgent(agent) {
  if (hasPendingModelChange(agent)) {
    ElMessage.warning('请先点击「保存模型」确认模型')
    return
  }
  router.push(`/ai-assistant/chat/${agent.id}`)
}
function onAgentCardClick(ev) {
  const card = ev?.currentTarget
  if (card) selectPop(card)
  const mark = document.querySelector('.ai-workbench .brand-mark')
  if (mark) iconBounce(mark)
}
function editAgent(id) { router.push(`/ai-assistant/agent/${id}`) }
</script>

<template>
  <div class="doc-page wb-shell ai-workbench">
    <WorkbenchHeader
      title="AI 助手"
      subtitle="智能体看板贴便签，任务看板跟进度"
      icon="bot"
      icon-gradient="linear-gradient(135deg,#5EEAD4,#14b8a6)"
    >
      <template #actions>
        <el-button class="wb-btn wb-btn--sky" type="primary" @click="router.push('/ai-assistant/agent/new')">+ 新建智能体</el-button>
      </template>
    </WorkbenchHeader>

    <div class="doc-body">
      <!-- 视图切换 Tab -->
      <div class="view-tabs">
        <button
          :class="['view-tab', { active: viewMode === 'agents' }]"
          @click="viewMode = 'agents'"
        >🤖 智能体看板</button>
        <button
          :class="['view-tab', { active: viewMode === 'toolbox' }]"
          @click="viewMode = 'toolbox'"
        >🧰 AI工具箱</button>
        <button
          :class="['view-tab', { active: viewMode === 'knowledge' }]"
          @click="viewMode = 'knowledge'"
        >📚 知识库</button>
        <button
          :class="['view-tab', { active: viewMode === 'evaluator' }]"
          @click="viewMode = 'evaluator'"
        >📊 评测中心</button>
      </div>

      <!-- 智能体看板视图 -->
      <template v-if="viewMode === 'agents'">
      <!-- 上方：智能体看板 -->
      <section class="doc-section duty-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            智能体看板
            <span class="doc-tag">Agents</span>
          </h3>
          <span class="filter-count">{{ agents.length }} 张便签</span>
        </div>
        <div class="dot-board duty-roster" v-loading="loading">
          <div v-if="loading && !agents.length" class="ai-loading-wrap">
            <WbLoader />
            <span>正在加载智能体…</span>
          </div>
          <AgentStickyNote
            v-for="a in agents"
            :key="a.id"
            :agent="a"
            :rotation="noteRotation(a)"
            :tape-hue="tapeHue(a)"
            :pending-model="pendingModels[a.id]"
            :confirming="confirmingId === a.id"
            :testing="testingId === a.id"
            :status-class="agentStatusClass(a)"
            :status-text="agentStatusText(a)"
            :model-options="getModelOptions(a)"
            @update:pending-model="pendingModels[a.id] = $event"
            @confirm-model="confirmModel(a)"
            @chat="openAgent(a)"
            @edit="editAgent(a.id)"
            @test="testConnection(a)"
            @delete="deleteAgent(a)"
            @select="onAgentCardClick"
          />
          <EmptyState v-if="!agents.length && !loading" icon="🤖" text="还没有智能体" hint="点击「+ 新建智能体」贴上第一张便签" />
        </div>
      </section>

      <!-- 下方：任务看板 -->
      <section class="doc-section task-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            任务看板
            <span class="doc-tag">Tasks</span>
          </h3>
          <span class="filter-count">{{ filteredTasks.length }} / {{ tasks.length }}</span>
        </div>
        <div class="filter-bar">
          <AppTabs
            class="task-tabs"
            :items="taskFilterAppTabs"
            v-model="activeTaskFilter"
            :leaf-animation="true"
            :shadow="true"
          >
            <template v-for="tab in taskFilterAppTabs" #[tab.key] :key="tab.key">
              <div class="dot-board task-board" v-loading="tasksLoading">
                <div v-if="tasksLoading && !filteredTasks.length" class="ai-loading-wrap">
                  <WbLoader />
                  <span>正在加载任务…</span>
                </div>
                <TaskStickyNote
                  v-for="t in filteredTasks"
                  :key="t.run_id"
                  :task="t"
                  :rotation="taskRotation(t)"
                  :tape-hue="taskTapeHue(t)"
                  @open="openTask"
                />
                <EmptyState v-if="!filteredTasks.length && !tasksLoading" icon="📋"
                  :text="activeTaskFilter === 'all' ? '还没有 AI 任务' : '当前状态下没有任务便签'"
                  :hint="activeTaskFilter === 'all' ? '在对话里让智能体帮你创建任务' : '尝试切换筛选条件'" />
              </div>
            </template>
          </AppTabs>
        </div>
      </section>
      </template>

      <!-- AI工具箱视图 -->
      <ToolboxPanel v-if="viewMode === 'toolbox'" class="tb-host" />
      <!-- 知识库视图：占满 doc-body 剩余区域 -->
      <KnowledgeBase v-if="viewMode === 'knowledge'" class="kb-host" />
      <!-- 评测中心视图 -->
      <EvaluatorTab v-if="viewMode === 'evaluator'" class="eval-host" />
    </div>
  </div>
</template>

<style scoped>
.ai-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.doc-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
  padding-bottom: 12px;
}
.kb-host {
  flex: 1;
  min-height: 0;
  min-width: 0;
  width: 100%;
}

.duty-section,
.task-section {
  display: flex;
  flex-direction: column;
  padding: 12px 24px 8px;
  flex-shrink: 0;
}
.duty-section {
  min-height: 0;
}
.task-section {
  flex: 1;
  min-height: 480px;
}

.doc-section__header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  flex-shrink: 0;
  margin-bottom: 8px;
}

.filter-bar {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.task-tabs {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.task-tabs :deep(.el-tabs) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.task-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  display: block;
  padding-top: 12px;
}
.task-tabs :deep(.el-tabs__inner) {
  min-height: min-content;
}

.filter-count {
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary, #999);
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
}

.dot-board {
  display: flex;
  flex-wrap: wrap;
  gap: 28px 32px;
  align-content: flex-start;
  align-items: flex-start;
  padding: 28px 22px 24px;
  border-radius: 18px;
  background-color: #fff);
  background-image: radial-gradient(rgba(137,207,240,0.12) 1.1px, transparent 1.1px);
  background-size: 18px 18px;
  border: 1.5px solid var(--ink));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55);
}
.duty-roster {
  min-height: 200px;
  max-height: 340px;
  overflow-x: auto;
  overflow-y: auto;
}
.task-board {
  min-height: 380px;
}

.empty {
  color: var(--app-text-secondary, #999);
  padding: 48px 0;
  text-align: center;
  font-size: var(--app-size-md);
  width: 100%;
  font-weight: 700;
}
.ai-loading-wrap {
  width: 100%;
  min-height: 140px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: var(--app-text-secondary, #999);
  font-size: var(--app-size-sm);
  font-weight: 700;
}

/* View tabs — prominent pill-style switcher */
.view-tabs {
  display: flex;
  gap: 4px;
  padding: 6px;
  margin: 0 24px;
  background: rgba(137,207,240,0.06);
  border-radius: 14px;
  flex-shrink: 0;
}
.view-tab {
  flex: 1;
  padding: 10px 20px;
  border: none;
  border-radius: 10px;
  background: transparent;
  font-size: var(--app-size-md);
  font-weight: 700;
  color: #999;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}
.view-tab:hover {
  background: rgba(255, 255, 255, 0.6);
  color: var(--app-text, var(--ink));
}
.view-tab.active {
  background: #fff;
  color: var(--app-text, var(--ink));
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}
</style>
