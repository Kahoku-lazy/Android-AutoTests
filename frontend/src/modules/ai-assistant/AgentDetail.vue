<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/shared/api-client.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import { IconArrowLeft, IconSave, IconPlus, IconTrash } from '@/shared/icons/index.js'
import { fetchDefaultPrompt, fetchPlatformTools, fetchAvailableSkills, fetchKnowledgeDocuments, fetchAgentTools, saveMcp as saveMcpApi, testMcpConnection, uploadSkill as uploadSkillApi, toggleToolEnabled, deleteToolById } from './api.js'

const route = useRoute(); const router = useRouter()
const agentId = route.params.agentId; const isNew = agentId === 'new'
const agent = ref(null); const loading = ref(false); const uploading = ref(false)
const fileInput = ref(null); const step = ref(1)

const form = ref({
  name:'', avatar:'🤖', tags:'', description:'',
  model_provider:'dashscope', model_name:'qwen-max', api_key:'', base_url:'',
  system_prompt:'', temperature:0.7, max_tokens:4096, generate_kwargs:'{}',
  formatter:'dashscope', max_iters:10, parallel_tool_calls:true, print_hint_msg:false,
  memory_mode:'inmemory', long_term_memory_mode:'both', enable_meta_tool:false,
  enable_rewrite_query:true, enable_knowledge_base:true, tools:[],
  compression_enabled:false, compression_threshold:10000, compression_keep_recent:3,
  compression_prompt:'', compression_template:'', tts_enabled:false,
  skills_config: {},
  knowledge_sources: [],
})

onMounted(async () => {
  // Always load available platform tools list, skills, and knowledge docs
  await loadPlatformTools()
  await loadAvailableSkills()
  await loadKnowledgeDocs()
  await loadAgentTools()

  if (!isNew) { loading.value = true
    try {
      const { data } = await client.get(`/ai/agents/${agentId}`)
      if (data.ok) {
        // Restore selected platform tools from agent detail
        const allTools = data.agent.tools || []
        const platformNames = allTools
          .filter(t => t.tool_type === 'platform' && t.enabled)
          .map(t => t.name)
        selectedPlatformTools.value = new Set(platformNames)
        // Don't populate form.tools from API — MCP tools loaded via loadAgentTools()
        form.value = { ...form.value, ...data.agent, tools: [] }
        agent.value = data.agent
      }
    } catch(_){}
    loading.value = false }
  else {
    // New agent: pre-fill default system prompt template
    await loadDefaultPrompt()
  }
})

const providers = [
  { value:'dashscope', label:'阿里百炼 (DashScope)', formatter:'dashscope', models:['qwen-max','qwen-plus','qwen-turbo','qwen3-235b'] },
  { value:'openai', label:'OpenAI', formatter:'openai', models:['gpt-4o','gpt-4-turbo','gpt-3.5-turbo','o4-mini'] },
  { value:'anthropic', label:'Anthropic (Claude)', formatter:'anthropic', models:['claude-fable-5','claude-opus-4-8','claude-sonnet-4-6'] },
  { value:'deepseek', label:'DeepSeek', formatter:'openai', models:['deepseek-v4-flash','deepseek-v4-pro','deepseek-chat','deepseek-reasoner'] },
  { value:'custom', label:'自定义 (OpenAI 兼容)', formatter:'openai', models:[] },
]

const detectingModels = ref(false)
const detectedModels = ref([])

// Platform tool selection
const availablePlatformTools = ref([])       // [{name, description}]
const selectedPlatformTools = ref(new Set())  // Set of enabled tool names
const loadingPlatformTools = ref(false)

async function loadPlatformTools() {
  loadingPlatformTools.value = true
  try {
    const data = await fetchPlatformTools()
    if (data.ok) availablePlatformTools.value = data.tools || []
  } catch (_) {}
  loadingPlatformTools.value = false
}

function togglePlatformTool(name) {
  const s = new Set(selectedPlatformTools.value)
  if (s.has(name)) s.delete(name)
  else s.add(name)
  selectedPlatformTools.value = s
}

function isPlatformToolSelected(name) {
  return selectedPlatformTools.value.has(name)
}

// Workspace skill toggles
const availableSkills = ref([])       // [{name, description}]
const loadingSkills = ref(false)

async function loadAvailableSkills() {
  loadingSkills.value = true
  try {
    const data = await fetchAvailableSkills()
    if (data.ok) availableSkills.value = data.skills || []
  } catch (_) {}
  loadingSkills.value = false
}

function isSkillEnabled(name) {
  const cfg = form.value.skills_config || {}
  return cfg[name] !== false  // default: enabled
}

function toggleSkill(name) {
  const cfg = { ...(form.value.skills_config || {}) }
  cfg[name] = !isSkillEnabled(name)
  form.value.skills_config = cfg
}

// Knowledge base document selection
const knowledgeDocs = ref([])     // [{id, source, type, size}]
const loadingDocs = ref(false)

async function loadKnowledgeDocs() {
  loadingDocs.value = true
  try {
    const data = await fetchKnowledgeDocuments()
    if (data.ok) knowledgeDocs.value = data.data?.documents || []
  } catch (_) {}
  loadingDocs.value = false
}

function isDocEnabled(docId) {
  const sources = form.value.knowledge_sources || []
  if (!sources.length) return true  // empty = all enabled
  return sources.includes(docId)
}

function toggleDoc(docId) {
  let sources = [...(form.value.knowledge_sources || [])]
  if (sources.length === 0) {
    // Currently "all enabled" — switch to explicit list with all docs minus this one
    sources = knowledgeDocs.value.map(d => d.id)
  }
  if (sources.includes(docId)) {
    sources = sources.filter(s => s !== docId)
  } else {
    sources.push(docId)
  }
  // If all docs are enabled, clear to "all" state
  const allIds = new Set(knowledgeDocs.value.map(d => d.id))
  const selectedIds = new Set(sources)
  if (allIds.size === selectedIds.size && [...allIds].every(id => selectedIds.has(id))) {
    form.value.knowledge_sources = []
  } else {
    form.value.knowledge_sources = sources
  }
}

// MCP management (edit mode uses API directly; create mode stashes in form.tools)
const mcpTools = ref([])
const mcpDialogVisible = ref(false)
const mcpDialogMode = ref('add')
const mcpEditingIndex = ref(-1)
const mcpForm = ref({ name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}' })
const mcpJsonError = ref('')
const mcpTestingId = ref(null)
const mcpTestResults = ref({})

// Skill management (only available in edit mode)
const skills = ref([])
const skillUploading = ref(false)
const skillFolderInput = ref(null)

// ── MCP functions ──
async function loadAgentTools() {
  if (isNew.value) return
  try {
    const data = await fetchAgentTools(agentId)
    if (data.ok) {
      mcpTools.value = data.data?.mcp || []
      skills.value = data.data?.skills || []
    }
  } catch (_) {}
}

function highlightJson(raw) {
  try {
    const obj = JSON.parse(raw)
    const formatted = JSON.stringify(obj, null, 2)
    return formatted
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/("(?:[^"\\]|\\.)*")\s*:/g, '<span style="color:#9cdcfe">$1</span>:')
      .replace(/:\s*("(?:[^"\\]|\\.)*")/g, ': <span style="color:#ce9178">$1</span>')
      .replace(/:\s*(\d+\.?\d*)/g, ': <span style="color:#b5cea8">$1</span>')
      .replace(/:\s*(true|false)/g, ': <span style="color:#569cd6">$1</span>')
      .replace(/:\s*(null)/g, ': <span style="color:#569cd6">$1</span>')
  } catch {
    return `<span style="color:#f44747">${raw.replace(/&/g, '&amp;').replace(/</g, '&lt;')}</span>`
  }
}

function openMcpDialog(mode = 'add', index = -1) {
  mcpDialogMode.value = mode
  mcpEditingIndex.value = index
  mcpJsonError.value = ''
  if (mode === 'edit' && index >= 0) {
    const list = isNew.value ? form.value.tools : mcpTools.value
    const t = list[index]
    const cfgStr = typeof t.config_json === 'string' ? t.config_json : JSON.stringify(t.config || t.config_json || {}, null, 2)
    mcpForm.value = { name: t.name || '', config_json: cfgStr }
  } else {
    mcpForm.value = { name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}' }
  }
  mcpDialogVisible.value = true
}

function normalizeMcpJson(raw) {
  let parsed
  try { parsed = JSON.parse(raw) } catch { return null }
  // Auto-detect mcpServers wrapper: {"mcpServers": {"name": {...}}}
  if (parsed.mcpServers && typeof parsed.mcpServers === 'object') {
    const servers = parsed.mcpServers
    const names = Object.keys(servers)
    if (names.length === 0) return null
    const name = names[0]
    const inner = servers[name]
    return { name, config: inner }
  }
  // Plain inner config — no wrapper
  return { name: null, config: parsed }
}

async function saveMcpTool() {
  const raw = mcpForm.value.config_json.trim()
  if (!raw) { mcpJsonError.value = 'JSON 配置不能为空'; return }

  const normalized = normalizeMcpJson(raw)
  if (!normalized) { mcpJsonError.value = 'JSON 格式无效，请检查语法'; return }

  // Use auto-detected name from mcpServers key, or fall back to form name
  const finalName = normalized.name || mcpForm.value.name.trim()
  if (!finalName) { ElMessage.warning('请输入 MCP 名称'); return }

  mcpJsonError.value = ''
  // Update the form config to use cleaned JSON (no mcpServers wrapper)
  mcpForm.value.config_json = cleanJson

  if (isNew.value) {
    if (mcpDialogMode.value === 'add') {
      form.value.tools.push({ name: finalName, tool_type: 'mcp', enabled: true, config_json: cleanJson })
    } else if (mcpEditingIndex.value >= 0) {
      form.value.tools[mcpEditingIndex.value] = { ...form.value.tools[mcpEditingIndex.value], name: finalName, config_json: cleanJson }
    }
  } else {
    const data = await saveMcpApi(agentId, finalName, cleanJson)
    if (data.ok) { await loadAgentTools() } else { ElMessage.error(data.error || '保存失败'); return }
  }
  mcpDialogVisible.value = false
}

function removeMcpLocal(index) { form.value.tools.splice(index, 1) }

async function removeMcpApi(index) {
  const tool = mcpTools.value[index]
  if (!tool) return
  try { await ElMessageBox.confirm(`确定删除 MCP「${tool.name}」？`, '确认删除', { type: 'warning' }) } catch { return }
  const data = await deleteToolById(agentId, tool.id)
  if (data.ok) { mcpTools.value.splice(index, 1) } else { ElMessage.error(data.error || '删除失败') }
}

async function testMcp(index) {
  const tool = isNew.value ? form.value.tools[index] : mcpTools.value[index]
  if (!tool) return
  let cfgStr = tool.config_json || '{}'
  if (isNew.value && typeof cfgStr !== 'string') cfgStr = JSON.stringify(cfgStr)
  let cfgObj; try { cfgObj = JSON.parse(cfgStr) } catch { cfgObj = {} }
  const name = tool.name || ''
  mcpTestingId.value = name
  try {
    const data = await testMcpConnection(agentId, cfgObj)
    mcpTestResults.value[name] = { connected: data.connected, detail: data.detail }
    if (data.connected) ElMessage.success(`MCP「${name}」连通成功`)
    else ElMessage.warning(`MCP「${name}」连通失败: ${data.detail}`)
  } catch { mcpTestResults.value[name] = { connected: false, detail: '请求失败' }; ElMessage.error('连通性测试请求失败') }
  mcpTestingId.value = null
}

async function toggleMcp(i) {
  if (isNew.value) { form.value.tools[i].enabled = !form.value.tools[i].enabled; return }
  const tool = mcpTools.value[i]
  const data = await toggleToolEnabled(agentId, tool.id, !tool.enabled)
  if (data.ok) mcpTools.value[i].enabled = data.enabled
}

// ── Skill functions ──
function triggerSkillUpload() { skillFolderInput.value?.click() }

async function handleSkillFolderChange(e) {
  const files = e.target.files
  if (!files || !files.length) return
  const firstPath = files[0].webkitRelativePath || files[0].name
  const folderName = firstPath.split('/')[0] || 'skill'
  skillUploading.value = true
  try {
    const data = await uploadSkillApi(agentId, [...files], folderName)
    if (data.ok) {
      skills.value.push(data.data)
      ElMessage.success(`Skill「${folderName}」上传成功 (${data.data.config?.file_count || 0} 个文件)`)
    } else { ElMessage.error(data.error || '上传失败') }
  } catch (err) { ElMessage.error('上传失败: ' + (err.message || '未知错误')) }
  skillUploading.value = false
  e.target.value = ''
}

async function removeSkill(index) {
  const skill = skills.value[index]
  if (!skill) return
  try { await ElMessageBox.confirm(`确定删除 Skill「${skill.name}」？相关文件将被清除。`, '确认删除', { type: 'warning' }) } catch { return }
  const data = await deleteToolById(agentId, skill.id)
  if (data.ok) { skills.value.splice(index, 1); ElMessage.success('Skill 已删除') } else { ElMessage.error(data.error || '删除失败') }
}

function formatSkillSize(bytes) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// Load default system prompt template
const loadingDefaultPrompt = ref(false)
async function loadDefaultPrompt() {
  loadingDefaultPrompt.value = true
  try {
    const data = await fetchDefaultPrompt()
    if (data.ok && data.template) form.value.system_prompt = data.template
  } catch (_) {}
  loadingDefaultPrompt.value = false
}

// 合并内置模型 + API 检测到的模型，去重
const availableModels = computed(() => {
  const builtin = providers.find(p => p.value === form.value.model_provider)?.models || []
  const all = [...new Set([...builtin, ...detectedModels.value])]
  // 如果当前选择的模型不在列表中，追加
  if (form.value.model_name && !all.includes(form.value.model_name)) {
    all.push(form.value.model_name)
  }
  return all
})

async function detectModels() {
  if (!form.value.api_key) {
    ElMessage.warning('请先填写 API Key')
    return
  }
  detectingModels.value = true
  try {
    const { data } = await client.post('/ai/models/detect', {
      model_provider: form.value.model_provider,
      api_key: form.value.api_key,
      base_url: form.value.base_url,
    })
    if (data.ok) {
      detectedModels.value = data.models || []
      if (data.models.length) {
        ElMessage.success(`检测到 ${data.models.length} 个可用模型`)
        // 如果当前模型不在列表中，自动选择第一个
        if (!data.models.includes(form.value.model_name) && data.models.length) {
          form.value.model_name = data.models[0]
        }
      } else {
        ElMessage.warning('未能检测到可用模型，请检查 API Key 和地址')
      }
    }
  } catch (e) {
    ElMessage.error('模型检测请求失败')
  }
  detectingModels.value = false
}

function onProviderChange(p) {
  const prov = providers.find(x => x.value === p)
  if (prov) { form.value.formatter = prov.formatter; form.value.model_name = prov.models[0] || '' }
  detectedModels.value = []
}

const memoryModes = [
  { value:'inmemory', label:'短期记忆 (InMemory)' },
  { value:'longterm', label:'长期记忆 (LongTerm)' },
]
const ltmModes = [
  { value:'agent_control', label:'智能体控制' },
  { value:'static_control', label:'静态控制' },
  { value:'both', label:'两者结合' },
]

const stepLabels = ['基本信息', '模型配置', '提示词', '记忆工具', '高级']

function triggerUpload() { fileInput.value?.click() }
async function handleAvatarUpload(e) {
  const file = e.target.files?.[0]; if (!file) return; uploading.value = true
  const reader = new FileReader()
  reader.onload = async () => {
    try { const { data } = await client.post('/ai/upload-avatar', { image: reader.result }); if (data.ok) form.value.avatar = data.url } catch(_) {}
    uploading.value = false }
  reader.readAsDataURL(file)
}

async function save() {
  // In create mode, include MCP tools in payload. In edit mode, tools are managed via API.
  let allTools = []
  if (isNew.value) {
    const platformToolRecords = [...selectedPlatformTools.value].map(name => ({
      name, tool_type: 'platform', enabled: true, config_json: '{}',
    }))
    allTools = [...form.value.tools.map(t => ({
      name: t.name || '',
      tool_type: t.tool_type || 'mcp',
      enabled: t.enabled !== false,
      config_json: typeof t.config_json === 'string' ? t.config_json : JSON.stringify(t.config_json || {}),
    })), ...platformToolRecords]
  }
  const payload = { ...form.value, tools: allTools }
  const url = isNew ? '/ai/agents/create' : `/ai/agents/${agentId}/update`
  try {
    const { data } = await client.post(url, payload)
    if (data.ok) {
      router.push('/ai-assistant')
    } else {
      ElMessage.error(data.error || '保存失败')
    }
  } catch (err) {
    ElMessage.error('保存失败: ' + (err.response?.data?.error || err.message))
  }
}
</script>

<template>
  <div class="doc-page wb-shell ai-workbench" v-loading="loading">
    <WorkbenchHeader
      :title="isNew ? '新建智能体' : '编辑智能体'"
      :subtitle="isNew ? '配置一个全新的 AI 智能体，分 5 步完成设置' : (agent?.name ? `编辑「${agent.name}」— 所有配置项已展开，修改后直接保存` : '所有配置项已展开，修改后直接保存')"
      mark="⚙️"
    />

    <div class="doc-body agent-body">
      <!-- Back button -->
      <button class="back-btn" @click="router.push('/ai-assistant')">
        <IconArrowLeft :size="18" />
        <span>返回智能体列表</span>
      </button>

      <!-- Steps bar — only in wizard mode (new agent) -->
      <div v-if="isNew" class="doc-section steps-section">
        <el-steps :active="step - 1" finish-status="success" align-center>
          <el-step v-for="(label, i) in stepLabels" :key="i" :title="label" />
        </el-steps>
      </div>

      <!-- Step 1: Basic Info -->
      <div v-if="!isNew || step===1" class="doc-section step-panel">
        <div class="section-title">
          <span class="section-num">1</span>
          <span>基本信息</span>
        </div>
        <el-form label-width="100px" class="agent-form">
          <el-form-item label="名称" required>
            <el-input v-model="form.name" placeholder="测试用例编写助手" />
          </el-form-item>
          <el-form-item label="头像">
            <div class="avatar-row">
              <div class="avatar-preview" :style="form.avatar?.startsWith('/api/ai/avatars/')?{backgroundImage:`url(${form.avatar})`}:{}">
                <span v-if="!form.avatar?.startsWith('/api/ai/avatars/')">{{ form.avatar || '🤖' }}</span>
              </div>
              <input ref="fileInput" type="file" accept="image/*" @change="handleAvatarUpload" style="display:none" />
              <el-button :loading="uploading" size="default" @click="triggerUpload">
                {{ uploading ? '上传中...' : '上传图片' }}
              </el-button>
              <span class="avatar-hint">或直接输入 Emoji 作为头像</span>
            </div>
          </el-form-item>
          <el-form-item label="标签">
            <el-input v-model="form.tags" placeholder="测试,用例,自动化" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="3" placeholder="智能体职责描述" />
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 2: Model Config -->
      <div v-if="!isNew || step===2" class="doc-section step-panel">
        <div class="section-title">
          <span class="section-num">2</span>
          <span>模型配置</span>
        </div>
        <el-form label-width="110px" class="agent-form">
          <el-form-item label="模型服务">
            <el-select v-model="form.model_provider" @change="onProviderChange" style="width:100%">
              <el-option v-for="p in providers" :key="p.value" :label="p.label" :value="p.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="模型名称">
            <el-select v-if="form.model_provider!=='custom'" v-model="form.model_name" style="width:100%" allow-create filterable>
              <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
            </el-select>
            <el-input v-else v-model="form.model_name" placeholder="输入模型名称" />
            <div v-if="detectedModels.length" class="form-hint" style="margin-top:4px">
              已检测模型: {{ detectedModels.length }} 个
            </div>
          </el-form-item>
          <el-form-item label="API Key">
            <el-input v-model="form.api_key" type="password" show-password placeholder="sk-..." />
            <el-button :loading="detectingModels" @click="detectModels" style="margin-left:8px" size="default">
              {{ detectingModels ? '检测中...' : '🔍 检测模型' }}
            </el-button>
          </el-form-item>
          <el-form-item v-if="form.model_provider==='custom'" label="API 地址">
            <el-input v-model="form.base_url" placeholder="https://api.example.com/v1" />
          </el-form-item>
          <el-form-item label="温度">
            <el-slider v-model="form.temperature" :min="0" :max="2" :step="0.1" show-input />
          </el-form-item>
          <el-form-item label="最大Token">
            <el-input-number v-model="form.max_tokens" :min="256" :max="128000" :step="256" />
          </el-form-item>
          <el-form-item label="Formatter">
            <el-select v-model="form.formatter" style="width:100%">
              <el-option value="dashscope" label="DashScope (Qwen)" />
              <el-option value="openai" label="OpenAI (GPT)" />
              <el-option value="anthropic" label="Anthropic (Claude)" />
            </el-select>
          </el-form-item>
          <el-form-item label="生成参数">
            <el-input v-model="form.generate_kwargs" type="textarea" :rows="2" placeholder='{"parallel_tool_calls":true}' />
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 3: Prompt -->
      <div v-if="!isNew || step===3" class="doc-section step-panel">
        <div class="section-title">
          <span class="section-num">3</span>
          <span>提示词</span>
        </div>
        <el-form label-width="120px" class="agent-form">
          <el-form-item label="系统提示词">
            <div style="display:flex;flex-direction:column;gap:8px;width:100%">
              <el-button :loading="loadingDefaultPrompt" size="small" @click="loadDefaultPrompt" style="align-self:flex-start">
                📋 加载默认模板
              </el-button>
              <el-input v-model="form.system_prompt" type="textarea" :rows="10" placeholder="你是一个专业的测试用例编写助手，擅长..." />
            </div>
          </el-form-item>
          <el-form-item label="最大迭代次数">
            <el-input-number v-model="form.max_iters" :min="1" :max="100" />
          </el-form-item>
          <el-form-item label="并行工具调用">
            <el-switch v-model="form.parallel_tool_calls" />
            <span class="form-hint">允许智能体同时调用多个工具</span>
          </el-form-item>
          <el-form-item label="打印提示消息">
            <el-switch v-model="form.print_hint_msg" />
            <span class="form-hint">在控制台输出运行时提示</span>
          </el-form-item>
        </el-form>
      </div>

      <!-- Step 4: Memory & Tools -->
      <div v-if="!isNew || step===4" class="doc-section step-panel">
        <div class="section-title">
          <span class="section-num">4</span>
          <span>记忆与工具</span>
        </div>
        <el-form label-width="120px" class="agent-form">
          <el-form-item label="记忆模式">
            <el-select v-model="form.memory_mode" style="width:100%">
              <el-option v-for="m in memoryModes" :key="m.value" :label="m.label" :value="m.value" />
            </el-select>
          </el-form-item>
          <template v-if="form.memory_mode==='longterm'">
            <el-form-item label="长期记忆模式">
              <el-select v-model="form.long_term_memory_mode" style="width:100%">
                <el-option v-for="m in ltmModes" :key="m.value" :label="m.label" :value="m.value" />
              </el-select>
            </el-form-item>
          </template>
          <el-form-item label="元工具">
            <el-switch v-model="form.enable_meta_tool" />
            <span class="form-hint">允许智能体动态管理自己的工具集</span>
          </el-form-item>
          <el-form-item label="重写查询">
            <el-switch v-model="form.enable_rewrite_query" />
            <span class="form-hint">LLM 检索前重写用户查询</span>
          </el-form-item>
          <el-form-item label="知识库检索">
            <el-switch v-model="form.enable_knowledge_base" />
            <span class="form-hint">开启后对话将自动搜索项目文档（ChromaDB RAG）作为上下文</span>
          </el-form-item>
        </el-form>

        <el-divider>平台业务工具</el-divider>
        <div v-if="loadingPlatformTools" style="padding:12px;color:#a0936e;text-align:center">加载工具列表中...</div>
        <div v-else-if="!availablePlatformTools.length" style="padding:12px;color:#a0936e;text-align:center">暂无可用工具</div>
        <div v-else class="platform-tools-grid">
          <div v-for="tool in availablePlatformTools" :key="tool.name" class="platform-tool-item"
               :class="{ selected: isPlatformToolSelected(tool.name) }"
               @click="togglePlatformTool(tool.name)">
            <el-checkbox :model-value="isPlatformToolSelected(tool.name)" />
            <div class="platform-tool-info">
              <span class="platform-tool-name">{{ tool.name }}</span>
              <span class="platform-tool-desc">{{ tool.description?.slice(0, 80) }}{{ (tool.description?.length || 0) > 80 ? '...' : '' }}</span>
            </div>
          </div>
        </div>

        <el-divider>工作区 Skills</el-divider>
        <div v-if="loadingSkills" style="padding:12px;color:#a0936e;text-align:center">加载 Skills 列表中...</div>
        <div v-else-if="!availableSkills.length" style="padding:12px;color:#a0936e;text-align:center">暂无可用 Skills</div>
        <div v-else class="platform-tools-grid">
          <div v-for="skill in availableSkills" :key="skill.name" class="platform-tool-item"
               :class="{ selected: isSkillEnabled(skill.name) }"
               @click="toggleSkill(skill.name)">
            <el-checkbox :model-value="isSkillEnabled(skill.name)" />
            <div class="platform-tool-info">
              <span class="platform-tool-name">{{ skill.name }}</span>
              <span class="platform-tool-desc">{{ skill.description?.slice(0, 80) }}{{ (skill.description?.length || 0) > 80 ? '...' : '' }}</span>
            </div>
          </div>
        </div>
        <div style="font-size:12px;color:#a0936e;margin-top:4px">
          工作区 Skills（Bash/Read/Write 等）默认全部启用。关闭的 Skill 将不会出现在工具列表中。
        </div>

        <el-divider>知识库文档范围</el-divider>
        <div v-if="loadingDocs" style="padding:12px;color:#a0936e;text-align:center">加载文档列表中...</div>
        <div v-else-if="!knowledgeDocs.length" style="padding:12px;color:#a0936e;text-align:center">知识库暂无文档</div>
        <div v-else>
          <div style="font-size:12px;color:#a0936e;margin-bottom:8px">
            AI 调用 <code>search_knowledge_base</code> 时只检索勾选的文档。不勾选任何文档 = 检索全部。
          </div>
          <div class="platform-tools-grid">
            <div v-for="doc in knowledgeDocs" :key="doc.id" class="platform-tool-item"
                 :class="{ selected: isDocEnabled(doc.id) }"
                 @click="toggleDoc(doc.id)">
              <el-checkbox :model-value="isDocEnabled(doc.id)" />
              <div class="platform-tool-info">
                <span class="platform-tool-name">{{ doc.source }}</span>
                <span class="platform-tool-desc">{{ doc.type }} · {{ (doc.size / 1024).toFixed(1) }} KB</span>
              </div>
            </div>
          </div>
        </div>

        <el-divider>MCP 服务器 ({{ isNew ? form.tools.length : mcpTools.length }})</el-divider>
        <button class="add-tool-btn" @click="openMcpDialog('add')">
          <IconPlus :size="16" />
          <span>添加 MCP 服务器</span>
        </button>

        <!-- Edit mode: MCP cards loaded from API -->
        <template v-if="!isNew">
          <div v-for="(t, i) in mcpTools" :key="t.id" class="mcp-card">
            <div class="mcp-card-head">
              <span class="mcp-card-name">{{ t.name }}</span>
              <span class="mcp-card-transport">{{ t.config?.transport || 'stdio' }}</span>
              <span v-if="mcpTestResults[t.name]" class="mcp-card-status"
                    :class="mcpTestResults[t.name].connected ? 'connected' : 'failed'">
                {{ mcpTestResults[t.name].connected ? '已连通' : '未连通' }}
              </span>
              <el-switch v-model="t.enabled" size="small" @change="toggleMcp(i)" />
            </div>
            <div class="mcp-card-body">
              <code>{{ t.config?.command || t.config?.url || '(未配置)' }}</code>
            </div>
            <div class="mcp-card-actions">
              <el-button size="small" :loading="mcpTestingId === t.name"
                         @click="testMcp(i)">测试连通</el-button>
              <el-button size="small" @click="openMcpDialog('edit', i)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeMcpApi(i)">删除</el-button>
            </div>
          </div>
        </template>

        <!-- Create mode: MCP cards stashed in form.tools -->
        <template v-if="isNew">
          <div v-for="(t, i) in form.tools" :key="i" class="mcp-card">
            <div class="mcp-card-head">
              <span class="mcp-card-name">{{ t.name || '(未命名)' }}</span>
              <span v-if="mcpTestResults[t.name]" class="mcp-card-status"
                    :class="mcpTestResults[t.name].connected ? 'connected' : 'failed'">
                {{ mcpTestResults[t.name].connected ? '已连通' : '未连通' }}
              </span>
              <el-switch v-model="t.enabled" size="small" />
            </div>
            <div class="mcp-card-body">
              <code>{{ (typeof t.config_json === 'string' ? JSON.parse(t.config_json) : t.config_json)?.command || '(未配置)' }}</code>
            </div>
            <div class="mcp-card-actions">
              <el-button size="small" :loading="mcpTestingId === t.name"
                         @click="testMcp(i)">测试连通</el-button>
              <el-button size="small" @click="openMcpDialog('edit', i)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="removeMcpLocal(i)">删除</el-button>
            </div>
          </div>
        </template>

        <div v-if="(isNew ? form.tools.length : mcpTools.length) === 0" class="tool-empty">
          暂未添加 MCP 服务器，点击上方按钮添加
        </div>

        <!-- MCP JSON editor dialog -->
        <el-dialog v-model="mcpDialogVisible"
                   :title="mcpDialogMode === 'add' ? '添加 MCP 服务器' : '编辑 MCP 服务器'"
                   width="560px" destroy-on-close append-to-body>
          <el-form label-width="80px">
            <el-form-item label="名称" required>
              <el-input v-model="mcpForm.name" placeholder="如: github" />
            </el-form-item>
            <el-form-item label="JSON 配置" required>
              <div style="width:100%">
                <el-input v-model="mcpForm.config_json" type="textarea" :rows="10"
                          placeholder='支持两种格式：&#10;1. 直接粘贴 MCP 配置：{"transport":"stdio","command":"npx",...}&#10;2. 粘贴完整 mcpServers 配置（自动提取）'
                          style="font-family: var(--font-mono, monospace); font-size: 13px;" />
                <div v-if="mcpJsonError" style="color:#e85f5f;font-size:12px;margin-top:4px">{{ mcpJsonError }}</div>
                <div v-if="mcpForm.config_json.trim()" class="json-preview-live" style="margin-top:8px;max-height:200px;overflow:auto;background:#1e1e1e;border-radius:8px;padding:10px;font-size:12px;font-family:Consolas,Monaco,'Courier New',monospace;line-height:1.5">
                  <pre v-html="highlightJson(mcpForm.config_json)" style="margin:0;white-space:pre-wrap;word-break:break-all"></pre>
                </div>
              </div>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="mcpDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveMcpTool">保存</el-button>
          </template>
        </el-dialog>

        <el-divider>Skills ({{ skills.length }})</el-divider>

        <template v-if="!isNew">
          <button class="add-tool-btn add-skill-btn" @click="triggerSkillUpload" :disabled="skillUploading">
            <IconPlus :size="16" />
            <span>{{ skillUploading ? '上传中...' : '上传 Skill 文件夹' }}</span>
          </button>
          <input ref="skillFolderInput" type="file" webkitdirectory multiple
                 style="display:none" @change="handleSkillFolderChange" />

          <div v-if="skillUploading" style="padding:12px 0">
            <el-progress :percentage="100" :indeterminate="true" :duration="2" />
          </div>

          <div v-for="(s, i) in skills" :key="s.id" class="skill-card">
            <div class="skill-card-head">
              <span class="skill-card-name">{{ s.name }}</span>
              <span class="skill-card-count">{{ s.config?.file_count || 0 }} 个文件</span>
            </div>
            <div class="skill-card-body">
              <div class="skill-card-features">{{ s.config?.features || '无功能描述' }}</div>
              <div class="skill-card-meta">
                <span>{{ formatSkillSize(s.config?.size_bytes) }}</span>
                <span>·</span>
                <span>{{ s.config?.uploaded_at || s.created_at }}</span>
              </div>
            </div>
            <div class="skill-card-actions">
              <el-button size="small" type="danger" plain @click="removeSkill(i)">删除</el-button>
            </div>
          </div>

          <div v-if="!skills.length && !skillUploading" class="tool-empty">
            暂未上传 Skill，点击上方按钮选择文件夹上传
          </div>
        </template>

        <div v-else class="tool-empty">
          Skills 管理在创建智能体后可用。请先保存智能体，再进入编辑模式上传 Skill。
        </div>
      </div>

      <!-- Step 5: Advanced -->
      <div v-if="!isNew || step===5" class="doc-section step-panel">
        <div class="section-title">
          <span class="section-num">5</span>
          <span>高级设置</span>
        </div>
        <el-form label-width="120px" class="agent-form">
          <el-form-item label="TTS 语音">
            <el-switch v-model="form.tts_enabled" />
            <span class="form-hint">启用文本转语音输出</span>
          </el-form-item>
        </el-form>

        <el-divider>内存压缩 (CompressionConfig)</el-divider>
        <el-form label-width="120px" class="agent-form">
          <el-form-item label="启用压缩">
            <el-switch v-model="form.compression_enabled" />
            <span class="form-hint">对话过长时自动压缩历史</span>
          </el-form-item>
          <template v-if="form.compression_enabled">
            <el-form-item label="触发阈值">
              <el-input-number v-model="form.compression_threshold" :min="1000" :max="100000" :step="1000" />
              <span class="form-hint">tokens</span>
            </el-form-item>
            <el-form-item label="保留最近">
              <el-input-number v-model="form.compression_keep_recent" :min="1" :max="50" />
              <span class="form-hint">条消息</span>
            </el-form-item>
            <el-form-item label="压缩提示词">
              <el-input v-model="form.compression_prompt" type="textarea" :rows="2" placeholder="Summarize the conversation..." />
            </el-form-item>
            <el-form-item label="摘要模板">
              <el-input v-model="form.compression_template" type="textarea" :rows="2" placeholder="Previous summary: {summary}" />
            </el-form-item>
          </template>
        </el-form>
      </div>

      <!-- Navigation -->
      <!-- Wizard mode (new agent): step-by-step with prev/next -->
      <div v-if="isNew" class="step-nav">
        <button v-if="step>1" class="nav-btn nav-prev" @click="step--">
          <IconArrowLeft :size="18" />
          <span>上一步</span>
        </button>
        <button v-if="step<5" class="nav-btn nav-next" @click="step++">
          <span>下一步</span>
          <IconArrowLeft :size="18" style="transform: rotate(180deg)" />
        </button>
        <button v-if="step===5" class="nav-btn nav-save" @click="save">
          <IconSave :size="18" />
          <span>保存智能体</span>
        </button>
      </div>

      <!-- Edit mode (existing agent): all sections expanded, single save button -->
      <div v-else class="step-nav">
        <button class="nav-btn nav-save" @click="save">
          <IconSave :size="18" />
          <span>保存修改</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.ai-animal-theme {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.agent-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding-bottom: 40px;
  overflow-x: hidden;
  overflow-y: auto;
}

/* Back button */
.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: 2px solid #19c8b9;
  border-radius: 12px;
  background: #e6f9f6;
  color: #158a80;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  align-self: flex-start;
}
.back-btn:hover {
  background: #19c8b9;
  color: #fff;
  box-shadow: 0 4px 14px rgba(25, 200, 185, 0.35);
  transform: translateY(-1px);
}

/* Steps section */
.steps-section {
  padding: 24px 32px;
  flex-shrink: 0;
}

/* Step panel */
.step-panel {
  padding: 28px 32px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 18px;
  font-weight: 700;
  color: #4A3A28;
  margin-bottom: 24px;
  padding-bottom: 14px;
  border-bottom: 2px solid #f0ebe0;
}

.section-num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #19c8b9 0%, #15a89c 100%);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  box-shadow: 0 3px 8px rgba(25, 200, 185, 0.3);
}

.agent-form :deep(.el-form-item__label) {
  font-size: 15px;
  font-weight: 600;
  color: #5c4b38;
}

.agent-form :deep(.el-input__wrapper),
.agent-form :deep(.el-textarea__inner) {
  border-radius: 10px;
  font-size: 15px;
}

.form-hint {
  font-size: 13px;
  color: #a0936e;
  margin-left: 10px;
}

/* Avatar row */
.avatar-row {
  display: flex;
  align-items: center;
  gap: 14px;
  flex-wrap: wrap;
}

.avatar-preview {
  width: 64px;
  height: 64px;
  border-radius: 14px;
  background-size: cover;
  background-position: center;
  background-color: #faf9f4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  border: 2px solid #e8e2d6;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(61, 52, 40, 0.08);
}

.avatar-hint {
  font-size: 13px;
  color: #a0936e;
}

/* Add tool button */
.add-tool-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border: 2px dashed #c4b89e;
  border-radius: 10px;
  background: #faf9f4;
  color: #8a7b66;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-bottom: 14px;
}
.add-tool-btn:hover {
  border-color: #19c8b9;
  background: #e6f9f6;
  color: #158a80;
}

/* Tool card */
.tool-card {
  background: #faf9f4;
  border: 1.5px solid #e8e2d6;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: border-color 0.2s ease;
}
.tool-card:hover { border-color: #d0c8b8; }

.tool-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.tool-del-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 8px;
  background: rgba(232, 95, 95, 0.1);
  color: #e85f5f;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-left: auto;
}
.tool-del-btn:hover {
  background: #e85f5f;
  color: #fff;
}

/* KV section */
.kv-section {
  margin-top: 6px;
  padding: 12px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #f0ebe0;
}

.kv-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  font-weight: 600;
  color: #8a7b66;
  margin-bottom: 8px;
}

.kv-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 1px solid #e8e2d6;
  border-radius: 8px;
  background: #faf9f4;
  color: #8a7b66;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}
.kv-add-btn:hover {
  border-color: #19c8b9;
  color: #158a80;
}

.kv-row {
  display: flex;
  gap: 6px;
  align-items: center;
  margin-top: 6px;
}

.kv-del-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: rgba(232, 95, 95, 0.08);
  color: #e85f5f;
  cursor: pointer;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.kv-del-btn:hover {
  background: #e85f5f;
  color: #fff;
}

.json-preview {
  margin-top: 4px;
}
.json-preview summary {
  font-size: 13px;
  color: #a0936e;
  cursor: pointer;
  font-weight: 600;
}
.json-preview pre {
  font-size: 12px;
  font-family: var(--font-mono, monospace);
  background: #fff;
  padding: 10px;
  border-radius: 8px;
  margin: 6px 0 0;
  overflow: auto;
  border: 1px solid #f0ebe0;
  color: #5c4b38;
  line-height: 1.5;
}

.tool-empty {
  padding: 32px;
  text-align: center;
  color: #a0936e;
  font-size: 14px;
  background: #faf9f4;
  border-radius: 12px;
  border: 1.5px dashed #e8e2d6;
}

/* Navigation */
.step-nav {
  display: flex;
  gap: 14px;
  justify-content: center;
  padding: 8px 0 16px;
  flex-shrink: 0;
}

.nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 28px;
  border: none;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.nav-prev {
  background: #f5f3ed;
  color: #5c4b38;
  border: 1.5px solid #e8e2d6;
}
.nav-prev:hover {
  background: #ede8dc;
  border-color: #d0c8b8;
}

.nav-next {
  background: linear-gradient(135deg, #19c8b9 0%, #15a89c 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(25, 200, 185, 0.3);
}
.nav-next:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(25, 200, 185, 0.45);
}

.nav-save {
  background: linear-gradient(135deg, #6fba2c 0%, #5a9e22 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(111, 186, 44, 0.35);
}
.nav-save:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(111, 186, 44, 0.5);
}

/* Platform tools grid */
.platform-tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 8px;
  margin-bottom: 8px;
}

.platform-tool-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 12px;
  border: 1.5px solid #e8e2d6;
  border-radius: 10px;
  background: #faf9f4;
  cursor: pointer;
  transition: all 0.2s ease;
}

.platform-tool-item:hover {
  border-color: #19c8b9;
  background: #e6f9f6;
}

.platform-tool-item.selected {
  border-color: #19c8b9;
  background: #e6f9f6;
  box-shadow: 0 2px 8px rgba(25, 200, 185, 0.15);
}

.platform-tool-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.platform-tool-name {
  font-size: 13px;
  font-weight: 700;
  color: #4a3a28;
}

.platform-tool-desc {
  font-size: 11px;
  color: #a0936e;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ── MCP card ── */
.mcp-card {
  background: #faf9f4;
  border: 1.5px solid #e8e2d6;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  transition: border-color 0.2s ease;
}
.mcp-card:hover { border-color: #19c8b9; }

.mcp-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.mcp-card-name {
  font-size: 15px;
  font-weight: 700;
  color: #4a3a28;
}

.mcp-card-transport {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #e6f9f6;
  color: #158a80;
  font-weight: 600;
}

.mcp-card-status {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  font-weight: 600;
}
.mcp-card-status.connected { background: #e8f5e0; color: #4a8233; }
.mcp-card-status.failed { background: #fde8e8; color: #c0392b; }

.mcp-card-body code {
  display: block;
  font-size: 13px;
  color: #6b5c44;
  background: #fff;
  padding: 6px 10px;
  border-radius: 6px;
  border: 1px solid #f0ebe0;
  margin-bottom: 10px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mcp-card-actions {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

/* ── Skill card ── */
.add-skill-btn {
  border-color: #b39ef3;
  color: #7c6ab2;
}
.add-skill-btn:hover {
  border-color: #b39ef3;
  background: #f5f2ff;
  color: #5c4a9e;
}

.skill-card {
  background: #faf9fb;
  border: 1.5px solid #e6e0f0;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  transition: border-color 0.2s ease;
}
.skill-card:hover { border-color: #b39ef3; }

.skill-card-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.skill-card-name {
  font-size: 15px;
  font-weight: 700;
  color: #4a3a28;
}

.skill-card-count {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 6px;
  background: #f5f2ff;
  color: #5c4a9e;
  font-weight: 600;
}

.skill-card-body { margin-bottom: 10px; }

.skill-card-features {
  font-size: 13px;
  color: #6b5c44;
  line-height: 1.5;
}

.skill-card-meta {
  display: flex;
  gap: 6px;
  font-size: 11px;
  color: #a0936e;
  margin-top: 4px;
  align-items: center;
}

.skill-card-actions {
  display: flex;
  gap: 6px;
}
</style>
