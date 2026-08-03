import { ref, computed } from 'vue'
import {
  fetchPlatformTools, fetchAvailableSkills, getKnowledgeDocuments,
  fetchAgentTools, saveMcp as saveMcpApi, testMcpConnection,
  uploadSkill as uploadSkillApi, toggleToolEnabled, deleteToolById,
} from '../api.js'

/**
 * Composable for the Agent Detail Step 4 (Memory & Tools) state management.
 * Extracted from AgentDetail.vue to keep the parent component under the 500-line limit.
 */
export function useAgentTools(form, isNew, agentId) {
  // ── Platform Tools (category-based) ──
  const toolCategories = ref([])
  const selectedPlatformTools = ref(new Set())
  const loadingPlatformTools = ref(false)

  async function loadPlatformTools() {
    loadingPlatformTools.value = true
    try {
      const data = await fetchPlatformTools()
      if (data.ok) toolCategories.value = data.categories || []
    } catch (err) { /* silent */ }
    loadingPlatformTools.value = false
  }

  function togglePlatformTool(name) {
    const s = new Set(selectedPlatformTools.value)
    s.has(name) ? s.delete(name) : s.add(name)
    selectedPlatformTools.value = s
  }

  function isPlatformToolSelected(name) { return selectedPlatformTools.value.has(name) }

  function toggleCategory(cat) {
    const allNames = cat.tools.map(t => t.name)
    const allSelected = allNames.every(n => selectedPlatformTools.value.has(n))
    const s = new Set(selectedPlatformTools.value)
    if (allSelected) { allNames.forEach(n => s.delete(n)) }
    else { allNames.forEach(n => s.add(n)) }
    selectedPlatformTools.value = s
  }

  function isCategorySelected(cat) {
    return cat.tools.length > 0 && cat.tools.every(t => selectedPlatformTools.value.has(t.name))
  }

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
  const knowledgeDocs = ref([])       // all KB documents (for import dialog)
  const loadingDocs = ref(false)
  const showImportDialog = ref(false)

  async function loadKnowledgeDocs() {
    loadingDocs.value = true
    try {
      const data = await getKnowledgeDocuments()
      if (data.ok) knowledgeDocs.value = data.data?.documents || []
    } catch (err) { /* silent */ }
    loadingDocs.value = false
  }

  function isDocEnabled(docId) {
    const sources = form.value.knowledge_sources || {}
    return sources[docId] === true
  }

  function toggleDocEnabled(docId) {
    const sources = { ...(form.value.knowledge_sources || {}) }
    sources[docId] = !sources[docId]
    form.value.knowledge_sources = sources
  }

  function importDocs(selectedIds) {
    const sources = { ...(form.value.knowledge_sources || {}) }
    for (const id of selectedIds) {
      if (!(id in sources)) sources[id] = true
    }
    form.value.knowledge_sources = sources
  }

  function removeDoc(docId) {
    const sources = { ...(form.value.knowledge_sources || {}) }
    delete sources[docId]
    form.value.knowledge_sources = sources
  }

  function openImportDialog() { showImportDialog.value = true }
  function closeImportDialog() { showImportDialog.value = false }

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
      try { await deleteToolById(agentId.value, s.id) } catch (err) { console.error('removeSkill failed:', err) }
      await loadAgentTools()
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
    const sources = form.value.knowledge_sources || {}
    return Object.values(sources).filter(v => v === true).length
  })
  const importedDocIds = computed(() => {
    const sources = form.value.knowledge_sources || {}
    return Object.keys(sources)
  })
  const mcpCount = computed(() => isNew.value ? form.value.tools.length : mcpTools.value.length)
  const customSkillCount = computed(() => skills.value.length)

  return {
    // platform tools
    toolCategories, selectedPlatformTools, loadingPlatformTools,
    loadPlatformTools, togglePlatformTool, isPlatformToolSelected,
    toggleCategory, isCategorySelected,
    // skills
    availableSkills, loadingSkills, enabledSkills,
    loadAvailableSkills, isSkillEnabled, toggleSkill: toggleSkill_,
    selectAllSkills, deselectAllSkills,
    // knowledge docs
    knowledgeDocs, loadingDocs, showImportDialog,
    loadKnowledgeDocs, isDocEnabled, toggleDocEnabled, importDocs, removeDoc,
    openImportDialog, closeImportDialog, importedDocIds,
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
