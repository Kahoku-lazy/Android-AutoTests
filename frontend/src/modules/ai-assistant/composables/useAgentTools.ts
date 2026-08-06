/** useAgentTools — Agent Detail Step 4 (Memory & Tools) state management */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import {
  fetchPlatformTools, fetchAvailableSkills, getKnowledgeDocuments,
  fetchAgentTools, saveMcp as saveMcpApi, testMcpConnection,
  uploadSkill as uploadSkillApi, toggleToolEnabled, deleteToolById,
} from '../api/toolbox'

interface ToolItem {
  id?: number
  name: string
  tool_type?: string
  enabled?: boolean
  config_json?: string
  config?: object
}

interface ToolCategory {
  name: string
  tools: ToolItem[]
}

interface SkillItem {
  id?: number
  name: string
  size?: number
}

interface KnowledgeDoc {
  id: number | string
  name?: string
}

interface McpTestResult {
  connected: boolean
  message: string
}

export interface UseAgentToolsReturn {
  toolCategories: Ref<ToolCategory[]>
  selectedPlatformTools: Ref<Set<string>>
  loadingPlatformTools: Ref<boolean>
  loadPlatformTools: () => Promise<void>
  togglePlatformTool: (name: string) => void
  isPlatformToolSelected: (name: string) => boolean
  toggleCategory: (cat: ToolCategory) => void
  isCategorySelected: (cat: ToolCategory) => boolean
  availableSkills: Ref<SkillItem[]>
  loadingSkills: Ref<boolean>
  enabledSkills: Ref<Set<string>>
  loadAvailableSkills: () => Promise<void>
  isSkillEnabled: (name: string) => boolean
  toggleSkill: (name: string) => void
  selectAllSkills: () => void
  deselectAllSkills: () => void
  knowledgeDocs: Ref<KnowledgeDoc[]>
  loadingDocs: Ref<boolean>
  showImportDialog: Ref<boolean>
  loadKnowledgeDocs: () => Promise<void>
  isDocEnabled: (docId: number | string) => boolean
  toggleDocEnabled: (docId: number | string) => void
  importDocs: (selectedIds: (number | string)[]) => void
  removeDoc: (docId: number | string) => void
  openImportDialog: () => void
  closeImportDialog: () => void
  importedDocIds: ComputedRef<string[]>
  mcpTools: Ref<ToolItem[]>
  mcpDialogVisible: Ref<boolean>
  mcpDialogMode: Ref<string>
  mcpForm: Ref<{ name: string; config_json: string }>
  mcpJsonError: Ref<string>
  mcpTestingId: Ref<string | null>
  mcpTestResults: Ref<Record<string, McpTestResult>>
  loadAgentTools: () => Promise<void>
  openMcpDialog: (mode: string, index?: number) => void
  saveMcpTool: () => Promise<void>
  testMcp: (index: number) => Promise<void>
  toggleMcp: (index: number) => Promise<void>
  removeMcpApi: (index: number) => Promise<void>
  removeMcpLocal: (index: number) => void
  skills: Ref<SkillItem[]>
  skillUploading: Ref<boolean>
  skillFolderInput: Ref<HTMLInputElement | null>
  uploadSkill: (files: File[]) => Promise<void>
  removeSkill: (index: number) => Promise<void>
  formatSkillSize: (bytes: number) => string
  platformToolSelectedCount: ComputedRef<number>
  wsSkillEnabledCount: ComputedRef<number>
  kbDocSelectedCount: ComputedRef<number>
  mcpCount: ComputedRef<number>
  customSkillCount: ComputedRef<number>
}

export function useAgentTools(
  form: Ref<Record<string, unknown>>,
  isNew: Ref<boolean>,
  agentId: Ref<number>,
): UseAgentToolsReturn {
  // ── Platform Tools (category-based) ──
  const toolCategories = ref<ToolCategory[]>([])
  const selectedPlatformTools = ref<Set<string>>(new Set())
  const loadingPlatformTools = ref(false)

  async function loadPlatformTools() {
    loadingPlatformTools.value = true
    try {
      const data = await fetchPlatformTools()
      if (data.status) toolCategories.value = (data as { categories?: ToolCategory[] }).categories || []
    } catch (err) { console.warn(err) }
    loadingPlatformTools.value = false
  }

  function togglePlatformTool(name: string) {
    const s = new Set(selectedPlatformTools.value)
    s.has(name) ? s.delete(name) : s.add(name)
    selectedPlatformTools.value = s
  }

  function isPlatformToolSelected(name: string) { return selectedPlatformTools.value.has(name) }

  function toggleCategory(cat: ToolCategory) {
    const allNames = cat.tools.map(t => t.name)
    const allSelected = allNames.every(n => selectedPlatformTools.value.has(n))
    const s = new Set(selectedPlatformTools.value)
    if (allSelected) { allNames.forEach(n => s.delete(n)) }
    else { allNames.forEach(n => s.add(n)) }
    selectedPlatformTools.value = s
  }

  function isCategorySelected(cat: ToolCategory) {
    return cat.tools.length > 0 && cat.tools.every(t => selectedPlatformTools.value.has(t.name))
  }

  // ── Workspace Skills ──
  const availableSkills = ref<SkillItem[]>([])
  const loadingSkills = ref(false)
  const enabledSkills = ref<Set<string>>(new Set())

  async function loadAvailableSkills() {
    loadingSkills.value = true
    try {
      const data = await fetchAvailableSkills()
      if (data.status) {
        availableSkills.value = (data as { skills?: SkillItem[] }).skills || []
        enabledSkills.value = new Set(availableSkills.value.map(s => s.name))
      }
    } catch (err) { console.warn(err) }
    loadingSkills.value = false
  }

  function isSkillEnabled(name: string) {
    const cfg = (form.value.skills_config || {}) as Record<string, boolean>
    return cfg[name] !== false
  }

  function toggleSkill_(name: string) {
    const cfg = { ...((form.value.skills_config || {}) as Record<string, boolean>) }
    cfg[name] = !isSkillEnabled(name)
    form.value.skills_config = cfg
  }

  function selectAllSkills() { form.value.skills_config = {} }
  function deselectAllSkills() {
    const cfg: Record<string, boolean> = {}
    availableSkills.value.forEach(s => { cfg[s.name] = false })
    form.value.skills_config = cfg
  }

  // ── Knowledge Base Docs ──
  const knowledgeDocs = ref<KnowledgeDoc[]>([])
  const loadingDocs = ref(false)
  const showImportDialog = ref(false)

  async function loadKnowledgeDocs() {
    loadingDocs.value = true
    try {
      const data = await getKnowledgeDocuments()
      if (data.status) knowledgeDocs.value = ((data as { data?: { documents?: KnowledgeDoc[] } }).data?.documents) || []
    } catch (err) { console.warn(err) }
    loadingDocs.value = false
  }

  function isDocEnabled(docId: number | string) {
    const sources = (form.value.knowledge_sources || {}) as Record<string, boolean>
    return sources[String(docId)] === true
  }

  function toggleDocEnabled(docId: number | string) {
    const sources = { ...((form.value.knowledge_sources || {}) as Record<string, boolean>) }
    sources[String(docId)] = !sources[String(docId)]
    form.value.knowledge_sources = sources
  }

  function importDocs(selectedIds: (number | string)[]) {
    const sources = { ...((form.value.knowledge_sources || {}) as Record<string, boolean>) }
    for (const id of selectedIds) {
      if (!(String(id) in sources)) sources[String(id)] = true
    }
    form.value.knowledge_sources = sources
  }

  function removeDoc(docId: number | string) {
    const sources = { ...((form.value.knowledge_sources || {}) as Record<string, boolean>) }
    delete sources[String(docId)]
    form.value.knowledge_sources = sources
  }

  function openImportDialog() { showImportDialog.value = true }
  function closeImportDialog() { showImportDialog.value = false }

  // ── MCP ──
  const mcpTools = ref<ToolItem[]>([])
  const mcpDialogVisible = ref(false)
  const mcpDialogMode = ref('add')
  const mcpEditingIndex = ref(-1)
  const mcpForm = ref<{ name: string; config_json: string }>({
    name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}',
  })
  const mcpJsonError = ref('')
  const mcpTestingId = ref<string | null>(null)
  const mcpTestResults = ref<Record<string, McpTestResult>>({})

  async function loadAgentTools() {
    if (isNew.value) return
    try {
      const data = await fetchAgentTools(agentId.value)
      if (data.status) {
        mcpTools.value = ((data as { data?: { mcp?: ToolItem[] } }).data?.mcp) || []
        skills.value = ((data as { data?: { skills?: SkillItem[] } }).data?.skills) || []
      }
    } catch (err) { console.warn(err) }
  }

  function openMcpDialog(mode: string, index?: number) {
    mcpDialogMode.value = mode
    mcpEditingIndex.value = index ?? -1
    mcpJsonError.value = ''
    if (mode === 'edit' && index !== undefined) {
      const source = isNew.value
        ? (form.value.tools as ToolItem[])?.[index]
        : mcpTools.value[index]
      if (source) {
        let cfg: object = {}
        try { cfg = typeof source.config_json === 'string' ? JSON.parse(source.config_json) : (source.config_json || source.config || {}) } catch { /* empty */ }
        mcpForm.value = { name: source.name || '', config_json: JSON.stringify(cfg, null, 2) }
      }
    } else {
      mcpForm.value = { name: '', config_json: '{\n  "transport": "stdio",\n  "command": "",\n  "args": []\n}' }
    }
    mcpDialogVisible.value = true
  }

  async function saveMcpTool() {
    mcpJsonError.value = ''
    let config: object
    try { config = JSON.parse(mcpForm.value.config_json) }
    catch (e) { mcpJsonError.value = 'JSON 格式错误: ' + (e as Error).message; return }
    const name = mcpForm.value.name.trim()
    if (!name) { mcpJsonError.value = '请输入名称'; return }

    if (isNew.value) {
      const tools = (form.value.tools || []) as ToolItem[]
      if (mcpDialogMode.value === 'add') {
        tools.push({ name, tool_type: 'mcp', enabled: true, config_json: mcpForm.value.config_json })
      } else {
        const i = mcpEditingIndex.value
        if (i >= 0) { tools[i].name = name; tools[i].config_json = mcpForm.value.config_json }
      }
      form.value.tools = tools
    } else {
      try {
        if (mcpDialogMode.value === 'add') {
          await saveMcpApi(agentId.value, name, mcpForm.value.config_json)
        } else {
          const t = mcpTools.value[mcpEditingIndex.value]
          if (t?.id) {
            await saveMcpApi(agentId.value, name, mcpForm.value.config_json)
            await toggleToolEnabled(agentId.value, t.id, !!t.enabled)
          }
        }
        await loadAgentTools()
      } catch (err) { mcpJsonError.value = (err as { response?: { data?: { error?: string } } })?.response?.data?.message || '保存失败' }
    }
    mcpDialogVisible.value = false
  }

  async function testMcp(index: number) {
    const source = isNew.value
      ? (form.value.tools as ToolItem[])?.[index]
      : mcpTools.value[index]
    if (!source) return
    let config: object = {}
    try { config = typeof source.config_json === 'string' ? JSON.parse(source.config_json) : (source.config_json || source.config || {}) } catch { /* empty */ }
    const name = source.name
    mcpTestingId.value = name
    try {
      if (isNew.value) {
        mcpTestResults.value[name] = { connected: true, message: '创建模式，跳过测试' }
      } else {
        const data = await testMcpConnection(agentId.value, config)
        mcpTestResults.value[name] = {
          connected: !!(data as { ok?: boolean }).status,
          message: ((data as { message?: string }).message) || ((data as { ok?: boolean }).status ? '连通' : '未连通'),
        }
      }
    } catch (err) {
      mcpTestResults.value[name] = {
        connected: false,
        message: (err as { response?: { data?: { error?: string } } })?.response?.data?.message || '测试失败',
      }
    }
    mcpTestingId.value = null
  }

  async function toggleMcp(index: number) {
    if (!isNew.value) {
      const t = mcpTools.value[index]
      if (t?.id) {
        try { await toggleToolEnabled(agentId.value, t.id, !!t.enabled) } catch (err) { console.warn(err) }
      }
    }
  }

  async function removeMcpApi(index: number) {
    const t = mcpTools.value[index]
    if (t?.id) {
      try { await deleteToolById(agentId.value, t.id) } catch (err) { console.warn(err) }
      await loadAgentTools()
    }
  }

  function removeMcpLocal(index: number) {
    const tools = (form.value.tools || []) as ToolItem[]
    tools.splice(index, 1)
    form.value.tools = tools
  }

  // ── Custom Skills ──
  const skills = ref<SkillItem[]>([])
  const skillUploading = ref(false)
  const skillFolderInput = ref<HTMLInputElement | null>(null)

  async function uploadSkill(files: File[]) {
    skillUploading.value = true
    try {
      await uploadSkillApi(agentId.value, files, '')
      await loadAgentTools()
    } catch (err) { console.warn(err) }
    skillUploading.value = false
  }

  async function removeSkill(index: number) {
    const s = skills.value[index]
    if (s?.id) {
      try { await deleteToolById(agentId.value, s.id) } catch (err) { console.error('removeSkill failed:', err) }
      await loadAgentTools()
    }
  }

  function formatSkillSize(bytes: number) {
    if (!bytes) return '0 B'
    return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes / 1024).toFixed(1)} KB` : `${(bytes / 1048576).toFixed(1)} MB`
  }

  // ── Computed badges ──
  const platformToolSelectedCount = computed(() => selectedPlatformTools.value.size)
  const wsSkillEnabledCount = computed(() => availableSkills.value.filter(s => isSkillEnabled(s.name)).length)
  const kbDocSelectedCount = computed(() => {
    const sources = (form.value.knowledge_sources || {}) as Record<string, boolean>
    return Object.values(sources).filter(v => v === true).length
  })
  const importedDocIds = computed(() => {
    const sources = (form.value.knowledge_sources || {}) as Record<string, boolean>
    return Object.keys(sources)
  })
  const mcpCount = computed(() => isNew.value ? ((form.value.tools as object[]) || []).length : mcpTools.value.length)
  const customSkillCount = computed(() => skills.value.length)

  return {
    toolCategories, selectedPlatformTools, loadingPlatformTools,
    loadPlatformTools, togglePlatformTool, isPlatformToolSelected,
    toggleCategory, isCategorySelected,
    availableSkills, loadingSkills, enabledSkills,
    loadAvailableSkills, isSkillEnabled, toggleSkill: toggleSkill_,
    selectAllSkills, deselectAllSkills,
    knowledgeDocs, loadingDocs, showImportDialog,
    loadKnowledgeDocs, isDocEnabled, toggleDocEnabled, importDocs, removeDoc,
    openImportDialog, closeImportDialog, importedDocIds,
    mcpTools, mcpDialogVisible, mcpDialogMode, mcpForm, mcpJsonError,
    mcpTestingId, mcpTestResults,
    loadAgentTools, openMcpDialog, saveMcpTool, testMcp, toggleMcp,
    removeMcpApi, removeMcpLocal,
    skills, skillUploading, skillFolderInput, uploadSkill, removeSkill, formatSkillSize,
    platformToolSelectedCount, wsSkillEnabledCount, kbDocSelectedCount,
    mcpCount, customSkillCount,
  }
}
