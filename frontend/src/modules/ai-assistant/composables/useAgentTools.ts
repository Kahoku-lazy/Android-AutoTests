/** useAgentTools — Agent Detail Step 4 (Memory & Tools) state management */
import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchPlatformTools, fetchAvailableSkills, getKnowledgeDocuments,
  fetchAgentTools, deleteToolById,
} from '../api/toolbox'
import type { ToolItem, KnowledgeDoc } from '../api/toolbox'

interface ToolCategory {
  name: string
  tools: ToolItem[]
}

interface SkillItem {
  id?: number
  name: string
  size?: number
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
  agentImportedTools: Ref<ToolItem[]>
  loadAgentTools: () => Promise<void>
  removeImportedTool: (toolId: number) => Promise<void>
  formatSkillSize: (bytes: number) => string
  platformToolSelectedCount: ComputedRef<number>
  wsSkillEnabledCount: ComputedRef<number>
  kbDocSelectedCount: ComputedRef<number>
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
      if (data.status) toolCategories.value = (data.data?.categories || []) as ToolCategory[]
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
        availableSkills.value = (data.data?.skills || []) as SkillItem[]
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
      if (data.status) knowledgeDocs.value = data.data?.documents || []
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

  // ── 已从 AI 工具箱导入的工具副本（mcp / skill）──
  const agentImportedTools = ref<ToolItem[]>([])

  async function loadAgentTools() {
    if (isNew.value) { agentImportedTools.value = []; return }
    try {
      const data = await fetchAgentTools(agentId.value)
      if (data.status) {
        const mcp = data.data?.mcp || []
        const skills = data.data?.skills || []
        agentImportedTools.value = [...mcp, ...skills].filter(
          (t) => t.tool_type === 'mcp' || t.tool_type === 'skill',
        )
      }
    } catch (err) { console.warn(err) }
  }

  async function removeImportedTool(toolId: number) {
    try { await ElMessageBox.confirm('确定要移除该工具吗？', '移除工具', { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }) } catch { return }
    try {
      await deleteToolById(agentId.value, toolId)
      ElMessage.success('已移除')
      await loadAgentTools()
    } catch (err) { ElMessage.error('移除失败，请稍后重试') }
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
    agentImportedTools, loadAgentTools, removeImportedTool,
    formatSkillSize,
    platformToolSelectedCount, wsSkillEnabledCount, kbDocSelectedCount,
  }
}
