import { ref, computed } from 'vue'
import {
  fetchPlatformTools, fetchAvailableSkills, fetchKnowledgeDocuments,
  fetchAgentTools, saveMcp as saveMcpApi, testMcpConnection,
  uploadSkill as uploadSkillApi, toggleToolEnabled, deleteToolById,
} from '../api.js'

/**
 * Composable for the Agent Detail Step 4 (Memory & Tools) state management.
 * Extracted from AgentDetail.vue to keep the parent component under the 500-line limit.
 */
export function useAgentTools(form, isNew, agentId) {
  // ── Platform Tools ──
  const availablePlatformTools = ref([])
  const selectedPlatformTools = ref(new Set())
  const loadingPlatformTools = ref(false)

  async function loadPlatformTools() {
    loadingPlatformTools.value = true
    try {
      const data = await fetchPlatformTools()
      if (data.ok) availablePlatformTools.value = data.tools || []
    } catch (err) { /* silent */ }
    loadingPlatformTools.value = false
  }

  function togglePlatformTool(name) {
    const s = new Set(selectedPlatformTools.value)
    s.has(name) ? s.delete(name) : s.add(name)
    selectedPlatformTools.value = s
  }

  function isPlatformToolSelected(name) { return selectedPlatformTools.value.has(name) }

  // ── Workspace Skills ──
  const availableSkills = ref([])
  const loadingSkills = ref(false)
  const enabledSkills = ref(new Set())

  async function loadAvailableSkills() {
    loadingSkills.value = true
    try {
      const data = await fetchAvailableSkills()
      if (data.ok) {
        availableSkills.value = data.skills || []
        // Default: all enabled
        enabledSkills.value = new Set(availableSkills.value.map(s => s.name))
      }
    } catch (err) { /* silent */ }
    loadingSkills.value = false
  }

  function isSkillEnabled(name) {
    const cfg = form.value.skills_config || {}
    return cfg[name] !== false
  }

  function toggleSkill_(name) { // renamed to avoid conflict
    const cfg = { ...(form.value.skills_config || {}) }
    cfg[name] = !isSkillEnabled(name)
    form.value.skills_config = cfg
  }

  function selectAllSkills() { form.value.skills_config = {} }
  function deselectAllSkills() {
    const cfg = {}
    availableSkills.value.forEach(s => { cfg[s.name] = false })
    form.value.skills_config = cfg
  }

  // ── Knowledge Base Docs ──
  const knowledgeDocs = ref([])
  const loadingDocs = ref(false)
  const enabledDocIds = ref(new Set())

  async function loadKnowledgeDocs() {
    loadingDocs.value = true
    try {
      const data = await fetchKnowledgeDocuments()
      if (data.ok) {
        knowledgeDocs.value = data.data?.documents || []
        enabledDocIds.value = new Set(knowledgeDocs.value.map(d => d.id))
      }
    } catch (err) { /* silent */ }
    loadingDocs.value = false
  }

  function isDocEnabled(docId) {
    const sources = form.value.knowledge_sources || []
    if (sources.includes('__none__')) return false
    if (!sources.length) return true
    return sources.includes(docId)
  }

  function toggleDoc(docId) {
    let sources = [...(form.value.knowledge_sources || [])]
    const wasNone = sources.includes('__none__')
    sources = sources.filter(s => s !== '__none__')
    if (wasNone) { sources = [docId] }
    else if (sources.length === 0) {
      sources = knowledgeDocs.value.map(d => d.id).filter(s => s !== docId)
    } else {
      sources.includes(docId) ? sources = sources.filter(s => s !== docId) : sources.push(docId)
    }
    const allIds = new Set(knowledgeDocs.value.map(d => d.id))
    const selectedIds = new Set(sources)
    if (sources.length === 0) { form.value.knowledge_sources = ['__none__'] }
    else if (allIds.size === selectedIds.size && [...allIds].every(id => selectedIds.has(id))) {
      form.value.knowledge_sources = []
    } else { form.value.knowledge_sources = sources }
  }

  function selectAllDocs() { form.value.knowledge_sources = [] }
  function deselectAllDocs() { form.value.knowledge_sources = ['__none__'] }

  // ── MCP ──
  const mcpTools = ref([])
  const mcpDialogVisible = ref(false)
  const mcpDialogMode = ref('add')
  const mcpEditingIndex = ref(-1)
  const mcpForm = ref({
    name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}',
  })
  const mcpJsonError = ref('')
  const mcpTestingId = ref(null)
  const mcpTestResults = ref({})

  async function loadAgentTools() {
    if (isNew.value) return
    try {
      const data = await fetchAgentTools(agentId.value)
      if (data.ok) {
        mcpTools.value = data.data?.mcp || []
        skills.value = data.data?.skills || []
      }
    } catch (err) { /* silent */ }
  }

  function openMcpDialog(mode, index) {
    mcpDialogMode.value = mode
    mcpEditingIndex.value = index ?? -1
    mcpJsonError.value = ''
    if (mode === 'edit' && index !== undefined) {
      const source = isNew.value ? form.value.tools[index] : mcpTools.value[index]
      if (source) {
        let cfg = {}
        try { cfg = typeof source.config_json === 'string' ? JSON.parse(source.config_json) : (source.config_json || source.config || {}) } catch (e) { /* empty */ }
        mcpForm.value = { name: source.name || '', config_json: JSON.stringify(cfg, null, 2) }
      }
    } else {
      mcpForm.value = { name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}' }
    }
    mcpDialogVisible.value = true
  }

  async function saveMcpTool() {
    mcpJsonError.value = ''
    let config
    try { config = JSON.parse(mcpForm.value.config_json) }
    catch (e) { mcpJsonError.value = 'JSON 格式错误: ' + e.message; return }
    const name = mcpForm.value.name.trim()
    if (!name) { mcpJsonError.value = '请输入名称'; return }

    if (isNew.value) {
      if (mcpDialogMode.value === 'add') {
        form.value.tools.push({ name, tool_type: 'mcp', enabled: true, config_json: mcpForm.value.config_json })
      } else {
        const i = mcpEditingIndex.value
        if (i >= 0) { form.value.tools[i].name = name; form.value.tools[i].config_json = mcpForm.value.config_json }
      }
    } else {
      try {
        if (mcpDialogMode.value === 'add') {
          const payload = { tool_type: 'mcp', name, config_json: mcpForm.value.config_json, enabled: true }
          await saveMcpApi(agentId.value, payload)
        } else {
          const t = mcpTools.value[mcpEditingIndex.value]
          if (t?.id) { await toggleToolEnabled(agentId.value, t.id, t.enabled) }
        }
        await loadAgentTools()
      } catch (err) { mcpJsonError.value = err?.response?.data?.error || '保存失败' }
    }
    mcpDialogVisible.value = false
  }

  async function testMcp(index) {
    const source = isNew.value ? form.value.tools[index] : mcpTools.value[index]
    if (!source) return
    let config = {}
    try { config = typeof source.config_json === 'string' ? JSON.parse(source.config_json) : (source.config_json || source.config || {}) } catch (e) { /* empty */ }
    const name = source.name
    mcpTestingId.value = name
    try {
      if (isNew.value) {
        mcpTestResults.value[name] = { connected: true, message: '创建模式，跳过测试' }
      } else {
        const data = await testMcpConnection(agentId.value, name)
        mcpTestResults.value[name] = { connected: data.ok, message: data.message || (data.ok ? '连通' : '未连通') }
      }
    } catch (err) {
      mcpTestResults.value[name] = { connected: false, message: err?.response?.data?.error || '测试失败' }
    }
    mcpTestingId.value = null
  }

  async function toggleMcp(index) {
    if (!isNew.value) {
      const t = mcpTools.value[index]
      if (t?.id) {
        try { await toggleToolEnabled(agentId.value, t.id, t.enabled) } catch (err) { /* silent */ }
      }
    }
  }

  async function removeMcpApi(index) {
    const t = mcpTools.value[index]
    if (t?.id) {
      try { await deleteToolById(agentId.value, t.id) } catch (err) { /* silent */ }
      await loadAgentTools()
    }
  }

  function removeMcpLocal(index) { form.value.tools.splice(index, 1) }

  // ── Custom Skills ──
  const skills = ref([])
  const skillUploading = ref(false)
  const skillFolderInput = ref(null)

  async function uploadSkill(files) {
    skillUploading.value = true
    try {
      const formData = new FormData()
      for (const f of files) { formData.append('files', f, f.webkitRelativePath || f.name) }
      await uploadSkillApi(agentId.value, formData)
      await loadAgentTools()
    } catch (err) { /* silent */ }
    skillUploading.value = false
  }

  async function removeSkill(index) {
    const s = skills.value[index]
    if (s?.id) {
      try { await deleteToolById(agentId.value, s.id) } catch (err) { /* silent */ }
      await loadSkills()
    }
  }

  function formatSkillSize(bytes) {
    if (!bytes) return '0 B'
    return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes/1024).toFixed(1)} KB` : `${(bytes/1048576).toFixed(1)} MB`
  }

  // ── Computed badges ──
  const platformToolSelectedCount = computed(() => selectedPlatformTools.value.size)
  const wsSkillEnabledCount = computed(() => availableSkills.value.filter(s => isSkillEnabled(s.name)).length)
  const kbDocSelectedCount = computed(() => {
    const sources = form.value.knowledge_sources || []
    if (sources.includes('__none__')) return 0
    if (!sources.length) return knowledgeDocs.value.length
    return sources.filter(id => id !== '__none__').length
  })
  const mcpCount = computed(() => isNew.value ? form.value.tools.length : mcpTools.value.length)
  const customSkillCount = computed(() => skills.value.length)

  return {
    // platform tools
    availablePlatformTools, selectedPlatformTools, loadingPlatformTools,
    loadPlatformTools, togglePlatformTool, isPlatformToolSelected,
    // skills
    availableSkills, loadingSkills, enabledSkills,
    loadAvailableSkills, isSkillEnabled, toggleSkill: toggleSkill_,
    selectAllSkills, deselectAllSkills,
    // knowledge docs
    knowledgeDocs, loadingDocs, enabledDocIds,
    loadKnowledgeDocs, isDocEnabled, toggleDoc, selectAllDocs, deselectAllDocs,
    // MCP
    mcpTools, mcpDialogVisible, mcpDialogMode, mcpForm, mcpJsonError,
    mcpTestingId, mcpTestResults,
    loadAgentTools, openMcpDialog, saveMcpTool, testMcp, toggleMcp,
    removeMcpApi, removeMcpLocal,
    // custom skills
    skills, skillUploading, skillFolderInput, uploadSkill, removeSkill, formatSkillSize,
    // computed
    platformToolSelectedCount, wsSkillEnabledCount, kbDocSelectedCount,
    mcpCount, customSkillCount,
  }
}
