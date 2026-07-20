<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import client from '@/shared/api-client.js'
import { ElMessage } from 'element-plus'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import { IconArrowLeft, IconSave, IconPlus, IconTrash } from '@/shared/icons/index.js'

const route = useRoute(); const router = useRouter()
const agentId = route.params.agentId; const isNew = agentId === 'new'
const agent = ref(null); const loading = ref(false); const uploading = ref(false)
const fileInput = ref(null); const step = ref(1)

const form = ref({
  name:'', avatar:'🤖', tags:'', description:'',
  model_provider:'dashscope', model_name:'qwen-max', api_key:'', base_url:'',
  system_prompt:'', temperature:0.7, max_tokens:4096, generate_kwargs:'{}',
  formatter:'dashscope', max_iters:10, parallel_tool_calls:false, print_hint_msg:false,
  memory_mode:'inmemory', long_term_memory_mode:'both', enable_meta_tool:false,
  enable_rewrite_query:true, enable_knowledge_base:true, tools:[],
  compression_enabled:false, compression_threshold:10000, compression_keep_recent:3,
  compression_prompt:'', compression_template:'', tts_enabled:false,
})

onMounted(async () => {
  if (!isNew) { loading.value = true
    try {
      const { data } = await client.get(`/ai/agents/${agentId}`)
      if (data.ok) {
        // 将 API tools 的 config_json 解析为编辑表单字段
        const tools = (data.agent.tools || []).map(parseToolFromApi)
        form.value = { ...form.value, ...data.agent, tools }
        agent.value = data.agent
      }
    } catch(_){}
    loading.value = false }
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

/** 将 API 返回的 tool → 前端表单 tool（config_json JSON 解析为编辑字段） */
function parseToolFromApi(t) {
  let cfg = {}
  try { cfg = JSON.parse(t.config_json || '{}') } catch (_) {}
  return {
    name: t.name || '',
    tool_type: t.tool_type || 'mcp',
    enabled: t.enabled !== false,
    transport: cfg.transport || 'stdio',
    command: cfg.command || '',
    args: Array.isArray(cfg.args) ? cfg.args.join(' ') : (cfg.args || ''),
    cwd: cfg.cwd || '',
    url: cfg.url || '',
    client_type: cfg.client_type || 'stateful',
    env: cfg.env ? Object.entries(cfg.env).map(([k, v]) => ({ key: k, value: v })) : [],
    headers: cfg.headers ? Object.entries(cfg.headers).map(([k, v]) => ({ key: k, value: v })) : [],
    config_json: t.config_json || '{}',
  }
}

function addTool() {
  form.value.tools.push({
    name:'', tool_type:'mcp', enabled:true,
    transport:'stdio', command:'', args:'', cwd:'',
    url:'', env: [], headers: [],
    client_type:'stateful',
  })
}
function removeTool(i) { form.value.tools.splice(i,1) }
function addKV(list) { list.push({ key:'', value:'' }) }
function removeKV(list, i) { list.splice(i,1) }
function toConfigJSON(t) {
  const cfg = { transport: t.transport || 'stdio' }
  if (t.transport === 'stdio') {
    cfg.command = t.command || ''
    if (t.args) cfg.args = t.args.split(/\s+/).filter(Boolean)
    if (t.cwd) cfg.cwd = t.cwd
  } else {
    cfg.url = t.url || ''
    cfg.client_type = t.client_type || 'stateful'
  }
  const envList = t.env || []
  const env = {}
  envList.forEach(e => { if (e.key) env[e.key] = e.value })
  if (Object.keys(env).length) cfg.env = env
  const hdrList = t.headers || []
  const headers = {}
  hdrList.forEach(h => { if (h.key) headers[h.key] = h.value })
  if (Object.keys(headers).length) cfg.headers = headers
  return JSON.stringify(cfg, null, 2)
}
function syncToolConfig(t) { t.config_json = toConfigJSON(t) }

async function save() {
  form.value.tools.forEach(t => syncToolConfig(t))
  const url = isNew ? '/ai/agents/create' : `/ai/agents/${agentId}/update`
  try {
    const { data } = await client.post(url, form.value)
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
      :subtitle="isNew ? '配置一个全新的 AI 智能体，分 5 步完成设置' : (agent?.name ? `正在编辑「${agent.name}」的配置` : '修改智能体配置')"
      mark="⚙️"
    />

    <div class="doc-body agent-body">
      <!-- Back button -->
      <button class="back-btn" @click="router.push('/ai-assistant')">
        <IconArrowLeft :size="18" />
        <span>返回智能体列表</span>
      </button>

      <!-- Steps bar -->
      <div class="doc-section steps-section">
        <el-steps :active="step - 1" finish-status="success" align-center>
          <el-step v-for="(label, i) in stepLabels" :key="i" :title="label" />
        </el-steps>
      </div>

      <!-- Step 1: Basic Info -->
      <div v-if="step===1" class="doc-section step-panel">
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
      <div v-if="step===2" class="doc-section step-panel">
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
      <div v-if="step===3" class="doc-section step-panel">
        <div class="section-title">
          <span class="section-num">3</span>
          <span>提示词</span>
        </div>
        <el-form label-width="120px" class="agent-form">
          <el-form-item label="系统提示词">
            <el-input v-model="form.system_prompt" type="textarea" :rows="10" placeholder="你是一个专业的测试用例编写助手，擅长..." />
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
      <div v-if="step===4" class="doc-section step-panel">
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

        <el-divider>MCP 服务器 ({{ form.tools.length }})</el-divider>
        <button class="add-tool-btn" @click="addTool">
          <IconPlus :size="16" />
          <span>添加 MCP 服务器</span>
        </button>
        <div v-for="(t,i) in form.tools" :key="i" class="tool-card">
          <div class="tool-card-head">
            <el-input v-model="t.name" placeholder="名称 (如 github)" size="default" style="width:160px" />
            <el-select v-model="t.transport" size="default" style="width:140px">
              <el-option value="stdio" label="stdio 本地" />
              <el-option value="sse" label="SSE 远程" />
              <el-option value="streamable_http" label="HTTP 远程" />
            </el-select>
            <el-tag :type="t.enabled ? 'success' : 'info'" effect="light" size="small">
              {{ t.enabled ? '已启用' : '已禁用' }}
            </el-tag>
            <el-switch v-model="t.enabled" size="small" />
            <button class="tool-del-btn" @click="removeTool(i)" title="删除">
              <IconTrash :size="16" />
            </button>
          </div>

          <template v-if="t.transport==='stdio'">
            <el-input v-model="t.command" placeholder="命令 如: npx" size="default" />
            <el-input v-model="t.args" placeholder="参数 如: -y @mcp/server-github" size="default" />
            <el-input v-model="t.cwd" placeholder="工作目录 (可选)" size="default" />
          </template>
          <template v-else>
            <el-input v-model="t.url" placeholder="URL 如: https://mcp.example.com/sse" size="default" />
            <el-select v-model="t.client_type" size="default" style="width:180px">
              <el-option value="stateful" label="有状态 (Stateful)" />
              <el-option value="stateless" label="无状态 (Stateless)" />
            </el-select>
          </template>

          <div class="kv-section">
            <div class="kv-head">
              <span>{{ t.transport==='stdio' ? '环境变量' : '请求头' }}</span>
              <button class="kv-add-btn" @click="addKV(t.transport==='stdio'?t.env:t.headers)">
                <IconPlus :size="14" /> 添加
              </button>
            </div>
            <div v-for="(kv, ki) in (t.transport==='stdio'?t.env:t.headers)" :key="ki" class="kv-row">
              <el-input v-model="kv.key" placeholder="KEY" size="small" style="width:120px" />
              <el-input v-model="kv.value" placeholder="VALUE" size="small" style="flex:1" />
              <button class="kv-del-btn" @click="removeKV(t.transport==='stdio'?t.env:t.headers, ki)">
                <IconTrash :size="14" />
              </button>
            </div>
          </div>

          <details class="json-preview">
            <summary>预览 JSON 配置</summary>
            <pre>{{ toConfigJSON(t) }}</pre>
          </details>
        </div>
        <div v-if="!form.tools.length" class="tool-empty">
          暂未添加 MCP 服务器，点击上方按钮添加
        </div>
      </div>

      <!-- Step 5: Advanced -->
      <div v-if="step===5" class="doc-section step-panel">
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
      <div class="step-nav">
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
</style>
