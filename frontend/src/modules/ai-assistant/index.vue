<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { animate, stagger } from 'animejs'
import { ElMessageBox, ElMessage } from 'element-plus'
import client from '@/shared/api-client.js'
import { Button as AnimalButton, Card as AnimalCard, Tabs } from 'animal-island-vue'
import PageHeader from '@/shared/components/PageHeader.vue'

const router = useRouter()
const agents = ref([])
const loading = ref(false)
const testingId = ref(null)
const confirmingId = ref(null)
const healthTimer = ref(null)
const healthResults = ref({})
const pendingModels = ref({})

// ── Tabs 筛选 ──
const activeFilter = ref('all')
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'running', label: '运行中' },
  { key: 'disconnected', label: '未连通' },
  { key: 'paused', label: '已暂停' },
]

const filteredAgents = computed(() => {
  if (activeFilter.value === 'all') return agents.value
  return agents.value.filter(a => {
    const h = healthResults.value[a.id]
    if (activeFilter.value === 'running') return a.status === 'active' && (!h || h.is_connected)
    if (activeFilter.value === 'disconnected') return a.status === 'active' && h && !h.is_connected
    if (activeFilter.value === 'paused') return a.status !== 'active'
    return true
  })
})

const CARD_COLORS = ['app-green', 'app-blue', 'app-yellow', 'app-pink', 'app-teal', 'purple', 'app-orange', 'brown']
const CARD_PATTERNS = ['app-green', 'app-blue', 'app-yellow', 'app-pink', 'app-teal', 'purple', 'app-orange', 'brown']

function cardColor(agent) {
  let hash = 0
  for (const c of String(agent.id)) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return CARD_COLORS[hash % CARD_COLORS.length]
}
function cardPattern(agent) {
  let hash = 0
  for (const c of String(agent.name || agent.id)) hash = (hash * 31 + c.charCodeAt(0)) >>> 0
  return CARD_PATTERNS[hash % CARD_PATTERNS.length]
}
function cardType(agent) {
  // 未连通的用 dashed 边框提示
  const h = healthResults.value[agent.id]
  if (h && !h.is_connected) return 'dashed'
  return 'default'
}

onMounted(() => {
  loadAgents()
  checkAllHealth()
  healthTimer.value = setInterval(checkAllHealth, 30 * 60 * 1000)
})
onUnmounted(() => { clearInterval(healthTimer.value) })

async function loadAgents() {
  loading.value = true
  try {
    const { data } = await client.get('/ai/agents')
    if (data.ok) {
      agents.value = data.agents
      syncPendingModels()
    }
  } catch { ElMessage.error('加载智能体列表失败') }
  loading.value = false
  nextTick(() => animateCards())
}

function syncPendingModels() {
  const next = {}
  for (const a of agents.value) next[a.id] = a.model_name
  pendingModels.value = next
}

function hasPendingModelChange(agent) {
  return pendingModels.value[agent.id] !== agent.model_name
}
function animateCards() {
  animate('.agent-card', {
    opacity: [0, 1], translateY: [24, 0], scale: [0.96, 1],
    delay: stagger(60), duration: 450, ease: 'outCubic',
  })
}

// ── Health ──
async function checkAllHealth() {
  try {
    const { data } = await client.get('/ai/agents/health')
    if (data.ok && data.agents) {
      for (const h of data.agents) {
        healthResults.value[h.id] = { is_connected: h.is_connected, last_checked: h.last_checked }
      }
    }
  } catch (_) {}
}

async function testConnection(agent) {
  testingId.value = agent.id
  try {
    const { data } = await client.post(`/ai/agents/${agent.id}/test`)
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
    const { data } = await client.post(`/ai/agents/${agent.id}/delete`)
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
function agentStatusEffect(agent) {
  if (agent.status !== 'active') return 'plain'
  const h = healthResults.value[agent.id]
  if (h && !h.is_connected) return 'dark'
  return 'dark'
}

// ── Tag type rotation ──
// Element Plus <el-tag type="..."> requires one of: primary | success | info | warning | danger
// Use `undefined` (omit) for the first slot to keep the default style.
const TAG_TYPES = [undefined, 'success', 'info', 'warning']
function tagType(index) {
  return TAG_TYPES[index % TAG_TYPES.length]
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
    const { data } = await client.post(`/ai/agents/${agent.id}/update`, { model_name: newModel })
    if (!data.ok) {
      pendingModels.value[agent.id] = agent.model_name
      ElMessage.error('模型切换失败')
    } else {
      agent.model_name = newModel
      ElMessage.success(`已确认使用 ${newModel}`)
    }
  } catch (_) {
    pendingModels.value[agent.id] = agent.model_name
    ElMessage.error('模型切换失败')
  }
  confirmingId.value = null
}

function openAgent(agent) {
  if (hasPendingModelChange(agent)) {
    ElMessage.warning('请先点击「确认」保存模型选择')
    return
  }
  router.push(`/ai-assistant/chat/${agent.id}`)
}
function editAgent(id) { router.push(`/ai-assistant/agent/${id}`) }

watch(activeFilter, () => nextTick(() => animateCards()))
</script>

<template>
  <div class="doc-page ai-animal-theme">
    <PageHeader
      title="AI 助手 AI Assistant"
      subtitle="管理 AI Agent 智能体，配置模型、工具与自动化工作流"
      color="app-yellow"
    />

    <div class="doc-body">
      <section class="doc-section agent-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            智能体列表
            <span class="doc-tag">Agents</span>
          </h3>
          <AnimalButton type="primary" @click="router.push('/ai-assistant/agent/new')">+ 新建智能体</AnimalButton>
        </div>

        <!-- Tabs 筛选 + 卡片内容 -->
        <div class="filter-bar">
          <Tabs
            class="agent-tabs"
            :items="filterTabs"
            v-model="activeFilter"
            :leaf-animation="true"
            :shadow="true"
          >
            <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
              <div class="agent-grid" v-loading="loading">
                <AnimalCard
                  v-for="a in filteredAgents"
                  :key="a.id"
                  :type="cardType(a)"
                  :color="cardColor(a)"
                  :pattern="cardPattern(a)"
                  class="agent-card"
                >
                  <!-- Avatar -->
                  <div class="ac-avatar"
                    :style="a.avatar?.startsWith('/api/ai/avatars/') ? { backgroundImage: `url(${a.avatar})` } : {}">
                    <span v-if="!a.avatar?.startsWith('/api/ai/avatars/')">{{ a.avatar || '🤖' }}</span>
                  </div>

                  <!-- Name + status tag -->
                  <div class="ac-header">
                    <span class="ac-name">{{ a.name }}</span>
                    <el-tag
                      :type="agentStatusType(a)"
                      :effect="agentStatusEffect(a)"
                      size="small"
                      round
                    >{{ agentStatusText(a) }}</el-tag>
                  </div>

                  <!-- Custom tags -->
                  <div class="ac-tags" v-if="a.tags">
                    <el-tag
                      v-for="(t, idx) in a.tags.split(',').filter(Boolean)"
                      :key="t"
                      :type="tagType(idx)"
                      effect="plain"
                      size="small"
                      round
                    >{{ t.trim() }}</el-tag>
                  </div>

                  <!-- Description -->
                  <div class="ac-desc" v-if="a.description">{{ a.description }}</div>

                  <!-- Model selector -->
                  <div class="ac-model-row">
                    <el-select
                      v-model="pendingModels[a.id]"
                      size="small"
                      class="ac-model-select"
                      @click.stop
                      filterable
                      placeholder="选择模型"
                    >
                      <el-option v-for="m in getModelOptions(a)" :key="m.value" :label="m.label" :value="m.value" />
                    </el-select>
                    <AnimalButton
                      v-if="hasPendingModelChange(a)"
                      size="small"
                      type="primary"
                      class="ac-model-confirm"
                      :loading="confirmingId === a.id"
                      @click.stop="confirmModel(a)"
                    >确认</AnimalButton>
                  </div>

                  <!-- Tool count + model provider -->
                  <div class="ac-meta">
                    <el-tag effect="plain" type="info" size="small" round>{{ a.tool_count || 0 }} 个工具</el-tag>
                    <span class="ac-provider">{{ a.model_provider }}</span>
                  </div>

                  <!-- Actions -->
                  <div class="ac-actions">
                    <AnimalButton size="small" type="primary" @click.stop="openAgent(a)">💬 对话</AnimalButton>
                    <AnimalButton size="small" @click.stop="editAgent(a.id)">⚙ 配置</AnimalButton>
                  </div>
                  <div class="ac-actions-secondary">
                    <AnimalButton size="small" :loading="testingId === a.id" @click.stop="testConnection(a)">🔌 测试</AnimalButton>
                    <AnimalButton size="small" type="danger" plain @click.stop="deleteAgent(a)">🗑 删除</AnimalButton>
                  </div>
                </AnimalCard>

                <div v-if="!filteredAgents.length && !loading" class="empty">
                  {{ activeFilter === 'all' ? '点击「+ 新建智能体」创建第一个智能体' : '当前筛选条件下没有智能体' }}
                </div>
              </div>
            </template>
          </Tabs>
          <span class="filter-count">{{ filteredAgents.length }} / {{ agents.length }} 个智能体</span>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.ai-animal-theme { min-height: 100%; }
.agent-section { padding: 20px 24px 24px; }

/* Filter bar */
.filter-bar {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 0 4px;
}
.agent-tabs {
  flex: 1;
  min-width: 0;
}
.agent-tabs :deep(.animal-tabs__content) {
  padding-top: 16px;
}
.filter-count {
  font-size: 13px;
  color: #9f927d;
  font-weight: 600;
  white-space: nowrap;
  flex-shrink: 0;
  padding-top: 10px;
}

/* Grid */
.agent-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-content: flex-start;
}
.agent-card {
  width: 260px;
  display: flex;
  flex-direction: column;
  gap: 0;
  transition: transform 0.25s ease;
}
.agent-card:hover {
  transform: translateY(-2px);
}
.agent-card :deep(.animal-card__content) {
  background: rgba(255, 248, 240, 0.85);
  border-radius: 16px;
  padding: 18px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}

/* Avatar */
.ac-avatar {
  width: 56px; height: 56px; border-radius: 18px; margin: 0 auto;
  background-size: cover; background-position: center; background-repeat: no-repeat;
  background-color: rgba(139,115,85,0.06); display: flex; align-items: center;
  justify-content: center; font-size: 28px;
  box-shadow: 0 2px 8px rgba(61, 52, 40, 0.1);
}

/* Header — name + status */
.ac-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.ac-name {
  font-size: 15px; font-weight: 700; color: #4A3A28;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* Tags */
.ac-tags {
  display: flex; gap: 4px; flex-wrap: wrap; justify-content: center;
}

/* Description */
.ac-desc {
  font-size: 12px; color: #988B7A; text-align: center;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}

/* Model row */
.ac-model-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0 -4px;
}
.ac-model-select { flex: 1; min-width: 0; }
.ac-model-confirm { flex-shrink: 0; }
.ac-model-select :deep(.el-input__wrapper) {
  padding: 0 10px; font-size: 12px; border-radius: 8px;
}
.ac-model-select :deep(.el-input__inner) { font-size: 12px; }

/* Meta */
.ac-meta {
  display: flex; justify-content: space-between; align-items: center;
}
.ac-provider {
  font-size: 11px; color: #a0936e; font-weight: 600; text-transform: uppercase;
}

/* Actions */
.ac-actions { display: flex; gap: 6px; justify-content: center; }
.ac-actions-secondary { display: flex; gap: 6px; justify-content: center; }

/* Empty */
.empty { color: #988B7A; padding: 60px 0; text-align: center; font-size: 15px; width: 100%; }
</style>
