/**
 * 工作流资源库 — 目录 / 页面流 / 接口流（Django JSON 持久化，doc_id 权威）
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { WorkflowSaveData } from '@/modules/workflow/types/workflow'
import {
  NODE_TYPES,
  DEFAULT_NAMES,
  isFlowDocType,
  type FlowDocType,
} from '@/modules/workflow/constants'
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
} from '@/modules/workflow/api'

export type LibNodeType = 'folder' | FlowDocType

export interface LibNode {
  id: string
  name: string
  type: LibNodeType
  parentId: string | null
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
  /** 当前原型作用域（进入工作台时设置） */
  const currentPrototypeId = ref<number | null>(null)
  /** doc_id → 已拉取的 config（缓存，避免每次打开都打 GET） */
  const configCache = ref<Record<string, unknown>>({})

  function requirePrototypeId(): number {
    if (currentPrototypeId.value == null) {
      throw new Error('未选择原型')
    }
    return currentPrototypeId.value
  }

  function setPrototypeId(id: number | null): void {
    if (currentPrototypeId.value !== id) {
      nodes.value = []
      activeId.value = null
      configCache.value = {}
    }
    currentPrototypeId.value = id
  }

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
        const order: Record<string, number> = {
          folder: 0,
          [NODE_TYPES.PAGE_FLOW]: 1,
          [NODE_TYPES.API_FLOW]: 2,
        }
        return (order[a.type] ?? 9) - (order[b.type] ?? 9) || a.name.localeCompare(b.name, 'zh')
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
      else localStorage.removeItem(ACTIVE_KEY)
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
  }): LibNode | null {
    if (!isFlowDocType(d.doc_type)) return null
    return {
      id: d.doc_id,
      name: d.title,
      type: d.doc_type,
      parentId: d.directory_id != null ? folderId(d.directory_id) : null,
      createdAt: d.created_at || '',
      updatedAt: d.updated_at || '',
    }
  }

  async function refreshFromServer(): Promise<void> {
    const prototypeId = requirePrototypeId()
    loading.value = true
    try {
      const [dirRes, docRes] = await Promise.all([
        listWorkflowDirectories({ prototype_id: prototypeId }),
        listWorkflowDocuments({ prototype_id: prototypeId }),
      ])
      const dirs = dirRes.data?.directories || []
      const docs = (docRes.data?.documents || []).filter(
        (d: { doc_type?: string }) => !d.doc_type || isFlowDocType(d.doc_type)
      )
      const folderNodes = dirs.map(mapDir)
      const docNodes = docs
        .map((d: any) => mapDoc(d))
        .filter((n: LibNode | null): n is LibNode => n != null)
      nodes.value = [...folderNodes, ...docNodes]
      for (const n of folderNodes) {
        if (expanded.value[n.id] === undefined) expanded.value[n.id] = true
      }
      persistUi()
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '加载失败'
      status.value = `加载目录失败: ${msg}`
      throw new Error(status.value)
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
        prototype_id: requirePrototypeId(),
      })
      if (!res.data?.status) throw new Error(res.data?.message || '创建目录失败')
      const node = mapDir(res.data.directory)
      nodes.value.push(node)
      if (parentId) expanded.value[parentId] = true
      persistUi()
      status.value = `已创建目录「${node.name}」`
      return node
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '创建目录失败'
      throw new Error(msg)
      throw e
    }
  }

  async function createFlowDoc(
    docType: FlowDocType,
    name: string,
    parentId: string | null = null
  ): Promise<LibNode> {
    const title =
      name.trim() ||
      (docType === NODE_TYPES.API_FLOW ? DEFAULT_NAMES.API_FLOW : DEFAULT_NAMES.PAGE_FLOW)
    const empty: WorkflowSaveData = {
      name: title,
      version: '1.0',
      savedAt: nowIso(),
      nodes: [],
      links: [],
    }
    const label = docType === NODE_TYPES.API_FLOW ? '接口流' : '页面流'
    try {
      const res = await saveWorkflowDocument({
        title,
        doc_type: docType,
        directory_id: parentToDirectoryId(parentId),
        prototype_id: requirePrototypeId(),
        config: empty,
      })
      if (!res.data?.status) throw new Error(res.data?.message || '创建失败')
      const doc = res.data.document
      const node = mapDoc(doc)
      if (!node) throw new Error('创建失败')
      configCache.value[node.id] = doc.config || empty
      nodes.value.push(node)
      if (parentId) expanded.value[parentId] = true
      persistUi()
      status.value = `已创建${label}「${title}」（${node.id}）`
      return node
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || `创建${label}失败`
      throw new Error(msg)
      throw e
    }
  }

  async function createPageFlow(name: string, parentId: string | null = null): Promise<LibNode> {
    return createFlowDoc(NODE_TYPES.PAGE_FLOW, name, parentId)
  }

  async function createApiFlow(name: string, parentId: string | null = null): Promise<LibNode> {
    return createFlowDoc(NODE_TYPES.API_FLOW, name, parentId)
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
        if (!res.data?.status) throw new Error(res.data?.message || '重命名失败')
      } else {
        // 只改标题，禁止附带 config：configCache 可能是创建时的空图或过期快照，
        // 一旦 PUT 会把未落库的画布数据洗成空（多端/改名失焦时尤其易发）。
        const res = await updateWorkflowDocument(id, {
          title,
          doc_type: n.type,
          directory_id: parentToDirectoryId(n.parentId),
        })
        if (!res.data?.status) throw new Error(res.data?.message || '重命名失败')
        if (res.data.document?.updated_at) n.updatedAt = res.data.document.updated_at
      }
      n.name = title
      if (!n.updatedAt) n.updatedAt = nowIso()
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '重命名失败'
      throw new Error(msg)
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
        if (!res.data?.status) throw new Error(res.data?.message || '删除失败')
        await refreshFromServer()
      } else {
        const res = await deleteWorkflowDocument(id)
        if (!res.data?.status) throw new Error(res.data?.message || '删除失败')
        delete configCache.value[id]
        nodes.value = nodes.value.filter(n => n.id !== id)
        if (activeId.value === id) activeId.value = null
        persistUi()
      }
      status.value = `已删除「${target.name}」`
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '删除失败'
      throw new Error(msg)
      throw e
    }
  }

  /** 移动节点到目标目录（targetFolderId=null 表示根） */
  async function moveNode(id: string, targetFolderId: string | null): Promise<void> {
    const n = findNode(id)
    if (!n) return
    if (n.parentId === targetFolderId) return
    if (n.type === 'folder' && targetFolderId === id) {
      throw new Error('不能将目录移入自身')
      return
    }
    // 禁止移入子孙目录
    if (n.type === 'folder' && targetFolderId) {
      let p: string | null = targetFolderId
      while (p) {
        if (p === id) {
          throw new Error('不能将目录移入其子目录')
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
        if (!res.data?.status) throw new Error(res.data?.message || '移动失败')
      } else {
        const res = await moveWorkflowDocument(id, parentToDirectoryId(targetFolderId))
        if (!res.data?.status) throw new Error(res.data?.message || '移动失败')
      }
      n.parentId = targetFolderId
      n.updatedAt = nowIso()
      if (targetFolderId) {
        expanded.value[targetFolderId] = true
        persistUi()
      }
      status.value = `已移动「${n.name}」`
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '移动失败'
      throw new Error(msg)
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

  async function savePageFlowPayload(
    id: string,
    data: WorkflowSaveData,
    opts?: { confirmEmptyOverwrite?: boolean; skipEmptyOverwrite?: boolean }
  ): Promise<void> {
    const n = findNode(id)
    if (!n || !isFlowDocType(n.type)) return
    data.name = n.name
    data.savedAt = nowIso()
    const incomingEmpty = !((data.nodes && data.nodes.length) || (data.links && data.links.length))
    if (incomingEmpty) {
      const remote = await fetchDocumentConfig(id, { force: true })
      const remoteNodes = Array.isArray((remote as any)?.nodes) ? (remote as any).nodes.length : 0
      if (remoteNodes > 0) {
        if (opts?.skipEmptyOverwrite) {
          // 自动保存/切页：拒绝空覆盖，保留服务器数据
          return
        }
        if (opts?.confirmEmptyOverwrite) {
          const ok = window.confirm(
            `服务器上已有 ${remoteNodes} 个节点，当前画布为空。确定要用空图覆盖吗？`
          )
          if (!ok) {
            // 已取消保存，未覆盖服务器数据（调用方处理提示）
            return
          }
        } else {
          // 默认保护：不覆盖
          // 画布为空，已跳过保存（调用方处理提示）
          return
        }
      }
    }
    try {
      const res = await updateWorkflowDocument(id, {
        title: n.name,
        doc_type: n.type,
        directory_id: parentToDirectoryId(n.parentId),
        config: data,
      })
      if (!res.data?.status) throw new Error(res.data?.message || '保存失败')
      // 以服务端回写为准，保证缓存与库一致
      const saved = res.data.document?.config ?? data
      configCache.value[id] = saved
      n.updatedAt = res.data.document?.updated_at || nowIso()
    } catch (e: any) {
      const msg = e?.response?.data?.message || e?.message || '保存失败'
      throw new Error(msg)
      throw e
    }
  }

  /**
   * @param force 为 true 时忽略内存缓存，强制 GET（打开文档/多端同步时必须）
   */
  async function fetchDocumentConfig(
    docId: string,
    opts?: { force?: boolean }
  ): Promise<any | null> {
    if (!opts?.force && configCache.value[docId] !== undefined) {
      return configCache.value[docId]
    }
    try {
      const res = await getWorkflowDocument(docId)
      if (!res.data?.status) return null
      const cfg = res.data.document?.config ?? {}
      configCache.value[docId] = cfg
      const n = findNode(docId)
      if (n && res.data.document?.title) n.name = res.data.document.title
      if (n && res.data.document?.updated_at) n.updatedAt = res.data.document.updated_at
      return cfg
    } catch (e: any) {
      throw new Error(e?.response?.data?.message || e?.message || '加载文档失败')
      return null
    }
  }

  /** 打开页面流：始终拉服务端最新，避免多端/多标签读到过期空缓存 */
  async function loadPageFlowPayload(id: string): Promise<WorkflowSaveData | null> {
    const cfg = await fetchDocumentConfig(id, { force: true })
    if (!cfg) return null
    return cfg as WorkflowSaveData
  }

  async function exportDoc(docId: string): Promise<Record<string, unknown> | null> {
    try {
      const res = await exportWorkflowDocument(docId)
      if (!res.data?.status) throw new Error(res.data?.message || '导出失败')
      return res.data.envelope
    } catch (e: any) {
      throw new Error(e?.response?.data?.message || e?.message || '导出失败')
      return null
    }
  }

  async function importDoc(
    envelope: Record<string, unknown>,
    opts?: { overwrite?: boolean; directoryId?: string | null }
  ): Promise<LibNode | null> {
    try {
      const payload: Record<string, unknown> = {
        ...envelope,
        prototype_id: requirePrototypeId(),
      }
      if (opts?.directoryId !== undefined) {
        payload.directory_id = parentToDirectoryId(opts.directoryId)
      }
      const res = await importWorkflowDocument(payload, { overwrite: !!opts?.overwrite })
      if (!res.data?.status) throw new Error(res.data?.message || '导入失败')
      await refreshFromServer()
      const doc = res.data.document
      if (doc?.config) configCache.value[doc.doc_id] = doc.config
      const mapped = doc ? mapDoc(doc) : null
      const node = (doc && findNode(doc.doc_id)) || mapped
      if (!node) {
        status.value = `已导入「${doc?.title || ''}」，但类型不支持展示`
        return null
      }
      status.value = `已导入「${doc.title}」（${doc.doc_id}）`
      // success — 调用方处理 toast
      return node
    } catch (e: any) {
      const statusCode = e?.response?.status
      const msg = e?.response?.data?.message || e?.message || '导入失败'
      if (statusCode === 409) {
        throw new Error(`${msg}（可勾选覆盖后重试）`)
      } else {
        throw new Error(msg)
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
    status.value = '已创建「默认目录」，可新建页面流或接口流'
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
    currentPrototypeId,
    setPrototypeId,
    tree,
    loadMeta,
    refreshFromServer,
    findNode,
    childrenOf,
    createFolder,
    createPageFlow,
    createApiFlow,
    createFlowDoc,
    configCache,
    renameNode,
    deleteNode,
    moveNode,
    setActive,
    toggleExpand,
    savePageFlowPayload,
    loadPageFlowPayload,
    exportDoc,
    importDoc,
    bootstrapIfEmpty,
    persistMeta: persistUi,
  }
})
