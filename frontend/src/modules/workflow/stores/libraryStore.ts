/**
 * 工作流资源库 — 目录 / 页面流 / 测试用例（Django JSON 持久化，doc_id 权威）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import type { WorkflowSaveData } from '@/modules/workflow/types/workflow'
import {
  listWorkflowDirectories,
  createWorkflowDirectory,
  updateWorkflowDirectory,
  deleteWorkflowDirectory,
  listWorkflowDocuments,
  getWorkflowDocument,
  saveWorkflowDocument,
  updateWorkflowDocument,
  deleteWorkflowDocument,
  importWorkflowDocument,
  exportWorkflowDocument,
  moveWorkflowDocument,
  moveWorkflowDirectory,
} from '@/modules/workflow/api.js'

export type LibNodeType = 'folder' | 'page_flow' | 'test_case'

export interface LibNode {
  id: string
  name: string
  type: LibNodeType
  parentId: string | null
  /** 平台用例 id（可选，存在 config.linkedCaseId） */
  caseId?: string
  createdAt: string
  updatedAt: string
}

const ACTIVE_KEY = 'wf_lib_active'
const EXPANDED_KEY = 'wf_lib_expanded'

function nowIso(): string {
  return new Date().toISOString()
}

function folderId(dbId: number | string): string {
  return `dir_${dbId}`
}

function parseDirDbId(id: string): number | null {
  if (!id.startsWith('dir_')) return null
  const n = Number(id.slice(4))
  return Number.isFinite(n) ? n : null
}

function parentToDirectoryId(parentId: string | null): number | null {
  if (!parentId) return null
  return parseDirDbId(parentId)
}

export const useLibraryStore = defineStore('wf-library', () => {
  const nodes = ref<LibNode[]>([])
  const activeId = ref<string | null>(null)
  const status = ref('')
  const expanded = ref<Record<string, boolean>>({})
  const loading = ref(false)
  /** doc_id → 已拉取的 config（缓存，避免每次打开都打 GET） */
  const configCache = ref<Record<string, unknown>>({})

  const activeNode = computed(() => nodes.value.find(n => n.id === activeId.value) || null)

  const tree = computed(() => {
    const byParent = new Map<string | null, LibNode[]>()
    for (const n of nodes.value) {
      const key = n.parentId
      if (!byParent.has(key)) byParent.set(key, [])
      byParent.get(key)!.push(n)
    }
    for (const list of byParent.values()) {
      list.sort((a, b) => {
        const order = { folder: 0, page_flow: 1, test_case: 2 }
        return (order[a.type] - order[b.type]) || a.name.localeCompare(b.name, 'zh')
      })
    }
    function build(parentId: string | null): (LibNode & { children: any[] })[] {
      return (byParent.get(parentId) || []).map(n => ({
        ...n,
        children: n.type === 'folder' ? build(n.id) : [],
      }))
    }
    return build(null)
  })

  function persistUi(): void {
    try {
      localStorage.setItem(EXPANDED_KEY, JSON.stringify(expanded.value))
      if (activeId.value) localStorage.setItem(ACTIVE_KEY, activeId.value)
    } catch { /* ignore */ }
  }

  function loadUi(): void {
    try {
      const raw = localStorage.getItem(EXPANDED_KEY)
      if (raw) expanded.value = JSON.parse(raw) || {}
      activeId.value = localStorage.getItem(ACTIVE_KEY)
    } catch {
      expanded.value = {}
    }
  }

  function findNode(id: string): LibNode | undefined {
    return nodes.value.find(n => n.id === id)
  }

  function childrenOf(parentId: string | null): LibNode[] {
    return nodes.value.filter(n => n.parentId === parentId)
  }

  function mapDir(d: {
    id: number
    name: string
    parent_id: number | null
    created_at?: string
    updated_at?: string
  }): LibNode {
    return {
      id: folderId(d.id),
      name: d.name,
      type: 'folder',
      parentId: d.parent_id != null ? folderId(d.parent_id) : null,
      createdAt: d.created_at || '',
      updatedAt: d.updated_at || '',
    }
  }

  function mapDoc(d: {
    doc_id: string
    title: string
    doc_type: string
    directory_id: number | null
    created_at?: string
    updated_at?: string
    config?: { linkedCaseId?: string }
  }): LibNode {
    return {
      id: d.doc_id,
      name: d.title,
      type: d.doc_type === 'test_case' ? 'test_case' : 'page_flow',
      parentId: d.directory_id != null ? folderId(d.directory_id) : null,
      caseId: d.config?.linkedCaseId || undefined,
      createdAt: d.created_at || '',
      updatedAt: d.updated_at || '',
    }
  }

  async function refreshFromServer(): Promise<void> {
    loading.value = true
    try {
      const [dirRes, docRes] = await Promise.all([
        listWorkflowDirectories(),
        listWorkflowDocuments(),
      ])
      const dirs = dirRes.data?.directories || []
      const docs = docRes.data?.documents || []
      const folderNodes = dirs.map(mapDir)
      const docNodes = docs.map((d: any) => mapDoc(d))
      nodes.value = [...folderNodes, ...docNodes]
      for (const n of folderNodes) {
        if (expanded.value[n.id] === undefined) expanded.value[n.id] = true
      }
      persistUi()
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '加载失败'
      status.value = `加载目录失败: ${msg}`
      ElMessage.error(status.value)
      throw e
    } finally {
      loading.value = false
    }
  }

  async function createFolder(name: string, parentId: string | null = null): Promise<LibNode> {
    const title = name.trim() || '新建目录'
    try {
      const res = await createWorkflowDirectory({
        name: title,
        parent_id: parentToDirectoryId(parentId),
      })
      if (!res.data?.ok) throw new Error(res.data?.error || '创建目录失败')
      const node = mapDir(res.data.directory)
      nodes.value.push(node)
      if (parentId) expanded.value[parentId] = true
      persistUi()
      status.value = `已创建目录「${node.name}」`
      return node
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '创建目录失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function createPageFlow(name: string, parentId: string | null = null): Promise<LibNode> {
    const title = name.trim() || '未命名页面流'
    const empty: WorkflowSaveData = {
      name: title,
      version: '1.0',
      savedAt: nowIso(),
      nodes: [],
      links: [],
    }
    try {
      const res = await saveWorkflowDocument({
        title,
        doc_type: 'page_flow',
        directory_id: parentToDirectoryId(parentId),
        config: empty,
      })
      if (!res.data?.ok) throw new Error(res.data?.error || '创建失败')
      const doc = res.data.document
      const node = mapDoc(doc)
      configCache.value[node.id] = doc.config || empty
      nodes.value.push(node)
      if (parentId) expanded.value[parentId] = true
      persistUi()
      status.value = `已创建页面流「${title}」（${node.id}）`
      return node
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '创建页面流失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function createTestCase(
    name: string,
    parentId: string | null = null,
    _opts?: {
      packageName?: string
      syncPlatform?: boolean
      blocks?: unknown[]
      linkedCaseId?: string
    }
  ): Promise<LibNode> {
    const title = name.trim() || '未命名用例'
    const config = {
      format: 'testcase-scratch-v1',
      name: title,
      package_name: _opts?.packageName || 'com.example.app',
      blocks: Array.isArray(_opts?.blocks) ? _opts!.blocks! : ([] as unknown[]),
      linkedCaseId: _opts?.linkedCaseId || '',
    }
    try {
      const res = await saveWorkflowDocument({
        title,
        doc_type: 'test_case',
        directory_id: parentToDirectoryId(parentId),
        config,
      })
      if (!res.data?.ok) throw new Error(res.data?.error || '创建失败')
      const doc = res.data.document
      const node = mapDoc(doc)
      configCache.value[node.id] = doc.config || config
      nodes.value.push(node)
      if (parentId) expanded.value[parentId] = true
      persistUi()
      status.value = `已创建测试用例「${title}」（${node.id}）`
      return node
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '创建用例失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function renameNode(id: string, name: string): Promise<void> {
    const n = findNode(id)
    const title = name.trim()
    if (!n || !title) return
    try {
      if (n.type === 'folder') {
        const dbId = parseDirDbId(id)
        if (dbId == null) return
        const res = await updateWorkflowDirectory(dbId, { name: title })
        if (!res.data?.ok) throw new Error(res.data?.error || '重命名失败')
      } else {
        const cached = configCache.value[id]
        const res = await updateWorkflowDocument(id, {
          title,
          doc_type: n.type === 'test_case' ? 'test_case' : 'page_flow',
          directory_id: parentToDirectoryId(n.parentId),
          ...(cached !== undefined ? { config: cached } : {}),
        })
        if (!res.data?.ok) throw new Error(res.data?.error || '重命名失败')
        if (res.data.document?.config) configCache.value[id] = res.data.document.config
      }
      n.name = title
      n.updatedAt = nowIso()
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '重命名失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function deleteNode(id: string): Promise<void> {
    const target = findNode(id)
    if (!target) return
    try {
      if (target.type === 'folder') {
        const dbId = parseDirDbId(id)
        if (dbId == null) return
        const res = await deleteWorkflowDirectory(dbId)
        if (!res.data?.ok) throw new Error(res.data?.error || '删除失败')
        await refreshFromServer()
      } else {
        const res = await deleteWorkflowDocument(id)
        if (!res.data?.ok) throw new Error(res.data?.error || '删除失败')
        delete configCache.value[id]
        nodes.value = nodes.value.filter(n => n.id !== id)
        if (activeId.value === id) activeId.value = null
        persistUi()
      }
      status.value = `已删除「${target.name}」`
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '删除失败'
      ElMessage.error(msg)
      throw e
    }
  }

  /** 移动节点到目标目录（targetFolderId=null 表示根） */
  async function moveNode(id: string, targetFolderId: string | null): Promise<void> {
    const n = findNode(id)
    if (!n) return
    if (n.parentId === targetFolderId) return
    if (n.type === 'folder' && targetFolderId === id) {
      ElMessage.error('不能将目录移入自身')
      return
    }
    // 禁止移入子孙目录
    if (n.type === 'folder' && targetFolderId) {
      let p: string | null = targetFolderId
      while (p) {
        if (p === id) {
          ElMessage.error('不能将目录移入其子目录')
          return
        }
        p = findNode(p)?.parentId ?? null
      }
    }
    try {
      if (n.type === 'folder') {
        const dbId = parseDirDbId(id)
        if (dbId == null) return
        const res = await moveWorkflowDirectory(dbId, parentToDirectoryId(targetFolderId))
        if (!res.data?.ok) throw new Error(res.data?.error || '移动失败')
      } else {
        const res = await moveWorkflowDocument(id, parentToDirectoryId(targetFolderId))
        if (!res.data?.ok) throw new Error(res.data?.error || '移动失败')
      }
      n.parentId = targetFolderId
      n.updatedAt = nowIso()
      if (targetFolderId) {
        expanded.value[targetFolderId] = true
        persistUi()
      }
      status.value = `已移动「${n.name}」`
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '移动失败'
      ElMessage.error(msg)
      throw e
    }
  }

  function setActive(id: string | null): void {
    activeId.value = id
    persistUi()
  }

  function toggleExpand(id: string): void {
    expanded.value[id] = !expanded.value[id]
    persistUi()
  }

  async function savePageFlowPayload(id: string, data: WorkflowSaveData): Promise<void> {
    const n = findNode(id)
    if (!n || n.type !== 'page_flow') return
    data.name = n.name
    data.savedAt = nowIso()
    try {
      const res = await updateWorkflowDocument(id, {
        title: n.name,
        doc_type: 'page_flow',
        directory_id: parentToDirectoryId(n.parentId),
        config: data,
      })
      if (!res.data?.ok) throw new Error(res.data?.error || '保存失败')
      configCache.value[id] = data
      n.updatedAt = nowIso()
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '保存页面流失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function fetchDocumentConfig(docId: string): Promise<any | null> {
    if (configCache.value[docId] !== undefined) return configCache.value[docId]
    try {
      const res = await getWorkflowDocument(docId)
      if (!res.data?.ok) return null
      const cfg = res.data.document?.config ?? {}
      configCache.value[docId] = cfg
      const n = findNode(docId)
      if (n && res.data.document?.title) n.name = res.data.document.title
      if (n && cfg?.linkedCaseId) n.caseId = cfg.linkedCaseId
      return cfg
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.error || e?.message || '加载文档失败')
      return null
    }
  }

  async function loadPageFlowPayload(id: string): Promise<WorkflowSaveData | null> {
    const cfg = await fetchDocumentConfig(id)
    if (!cfg) return null
    return cfg as WorkflowSaveData
  }

  async function saveCaseDraft(id: string, draft: {
    name: string
    package_name: string
    blocks: unknown[]
    linkedCaseId?: string
  }): Promise<void> {
    const n = findNode(id)
    if (!n || n.type !== 'test_case') return
    const config = {
      format: 'testcase-scratch-v1',
      name: draft.name || n.name,
      package_name: draft.package_name || 'com.example.app',
      blocks: draft.blocks || [],
      linkedCaseId: draft.linkedCaseId || '',
    }
    try {
      const res = await updateWorkflowDocument(id, {
        title: config.name,
        doc_type: 'test_case',
        directory_id: parentToDirectoryId(n.parentId),
        config,
      })
      if (!res.data?.ok) throw new Error(res.data?.error || '保存失败')
      configCache.value[id] = config
      if (draft.linkedCaseId) n.caseId = draft.linkedCaseId
      n.name = config.name
      n.updatedAt = nowIso()
    } catch (e: any) {
      const msg = e?.response?.data?.error || e?.message || '保存用例失败'
      ElMessage.error(msg)
      throw e
    }
  }

  async function loadCaseDraft(id: string): Promise<{
    name: string
    package_name: string
    blocks: unknown[]
    linkedCaseId?: string
  } | null> {
    const cfg = await fetchDocumentConfig(id)
    if (!cfg || typeof cfg !== 'object') return null
    const c = cfg as Record<string, unknown>
    return {
      name: (c.name as string) || '',
      package_name: (c.package_name as string) || 'com.example.app',
      blocks: (c.blocks as unknown[]) || [],
      linkedCaseId: (c.linkedCaseId as string) || '',
    }
  }

  async function setCaseId(id: string, caseId: string): Promise<void> {
    const n = findNode(id)
    if (!n || n.type !== 'test_case') return
    const draft = await loadCaseDraft(id)
    await saveCaseDraft(id, {
      name: draft?.name || n.name,
      package_name: draft?.package_name || 'com.example.app',
      blocks: draft?.blocks || [],
      linkedCaseId: caseId,
    })
  }

  async function exportDoc(docId: string): Promise<Record<string, unknown> | null> {
    try {
      const res = await exportWorkflowDocument(docId)
      if (!res.data?.ok) throw new Error(res.data?.error || '导出失败')
      return res.data.envelope
    } catch (e: any) {
      ElMessage.error(e?.response?.data?.error || e?.message || '导出失败')
      return null
    }
  }

  async function importDoc(
    envelope: Record<string, unknown>,
    opts?: { overwrite?: boolean; directoryId?: string | null }
  ): Promise<LibNode | null> {
    try {
      const payload = { ...envelope }
      if (opts?.directoryId !== undefined) {
        payload.directory_id = parentToDirectoryId(opts.directoryId)
      }
      const res = await importWorkflowDocument(payload, { overwrite: !!opts?.overwrite })
      if (!res.data?.ok) throw new Error(res.data?.error || '导入失败')
      await refreshFromServer()
      const doc = res.data.document
      if (doc?.config) configCache.value[doc.doc_id] = doc.config
      const node = findNode(doc.doc_id) || mapDoc(doc)
      status.value = `已导入「${doc.title}」（${doc.doc_id}）`
      ElMessage.success(status.value)
      return node
    } catch (e: any) {
      const statusCode = e?.response?.status
      const msg = e?.response?.data?.error || e?.message || '导入失败'
      if (statusCode === 409) {
        ElMessage.error(`${msg}（可勾选覆盖后重试）`)
      } else {
        ElMessage.error(msg)
      }
      return null
    }
  }

  /** 首次进入：从服务端拉取；空库则建默认目录（不预置示例文件） */
  async function bootstrapIfEmpty(): Promise<{ folder: LibNode } | null> {
    loadUi()
    await refreshFromServer()
    if (nodes.value.some(n => n.type === 'folder')) {
      return null
    }
    const folder = await createFolder('默认目录', null)
    expanded.value[folder.id] = true
    activeId.value = folder.id
    persistUi()
    status.value = '已创建「默认目录」，可在右侧新建页面流/用例'
    return { folder }
  }

  /** 兼容旧调用名 */
  async function loadMeta(): Promise<void> {
    loadUi()
    await refreshFromServer()
  }

  return {
    nodes,
    activeId,
    activeNode,
    status,
    expanded,
    loading,
    tree,
    loadMeta,
    refreshFromServer,
    findNode,
    childrenOf,
    createFolder,
    createPageFlow,
    createTestCase,
    configCache,
    renameNode,
    deleteNode,
    moveNode,
    setActive,
    toggleExpand,
    savePageFlowPayload,
    loadPageFlowPayload,
    saveCaseDraft,
    loadCaseDraft,
    setCaseId,
    exportDoc,
    importDoc,
    bootstrapIfEmpty,
    persistMeta: persistUi,
  }
})
