<script setup lang="ts">
/**
 * 工作流工作台
 * 左：目录+文件树（右键/长按移动）
 * 右：点击文件后直接编辑内容（页面流 VueFlow）
 */
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import { useLibraryStore, type LibNode } from '@/modules/workflow/stores/libraryStore'
import PageFlowVueFlow from './components/vueflow/PageFlowVueFlow.vue'
import WorkflowDirTree from './components/WorkflowDirTree.vue'
import WorkflowFileBrowser from './components/WorkflowFileBrowser.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'

const store = useWorkflowStore()
const lib = useLibraryStore()

const selectedFolderId = ref<string | null>(null)
const ready = ref(false)
const error = ref('')
function retryLoad() {
  error.value = ''
  ready.value = false
  lib.bootstrapIfEmpty()
    .then(() => { ready.value = true })
    .catch(() => { error.value = '加载工作流数据失败，请检查网络连接' })
}
const createName = ref('')
const creatingKind = ref<'folder' | null>(null)
const createParentId = ref<string | null>(null)
const editDocName = ref('')
const overwriteImport = ref(false)
/**
 * 当前画布已从服务端 hydrate 的页面流 doc_id。
 * 未 hydrate 时禁止 persist（刷新后 localStorage 恢复 activeId 但 store 仍空，
 * 否则一点「保存/切文件」就会把空图写进库）。
 */
const hydratedFlowId = ref<string | null>(null)
/** 自动保存防抖 */
let autosaveTimer: ReturnType<typeof setTimeout> | null = null
let autosaveInFlight = false

/** 右侧是否打开文件编辑器 */
const editing = computed(() => {
  const n = lib.activeNode
  return !!(n && n.type !== 'folder')
})

const folderName = computed(() => {
  if (selectedFolderId.value === null) return '根目录'
  return lib.findNode(selectedFolderId.value)?.name || '目录'
})

const breadcrumb = computed(() => {
  const cur = lib.activeNode
  if (!editing.value) {
    return selectedFolderId.value
      ? `资源 / ${folderName.value}`
      : '资源 / 全部'
  }
  if (!cur) return '编辑'
  const parent = cur.parentId ? lib.findNode(cur.parentId) : null
  const title = editDocName.value || cur.name
  return parent
    ? `${parent.name} / 页面流「${title}」`
    : `页面流「${title}」`
})

function clearAutosaveTimer() {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
    autosaveTimer = null
  }
}

async function persistPageFlow(opts?: { confirmEmptyOverwrite?: boolean }) {
  const cur = lib.activeNode
  if (!cur || cur.type !== 'page_flow') return
  if (hydratedFlowId.value !== cur.id) return
  await lib.savePageFlowPayload(cur.id, store.snapshotGraph(cur.name), {
    confirmEmptyOverwrite: opts?.confirmEmptyOverwrite,
    // 自动/切页保存：绝不用空图静默覆盖服务器已有数据
    skipEmptyOverwrite: !opts?.confirmEmptyOverwrite,
  })
}

async function persistActive() {
  await applyDocRename()
  const cur = lib.activeNode
  if (!cur || cur.type !== 'page_flow') return
  await persistPageFlow()
}

function schedulePageFlowAutosave() {
  const cur = lib.activeNode
  if (!cur || cur.type !== 'page_flow') return
  if (hydratedFlowId.value !== cur.id) return
  clearAutosaveTimer()
  autosaveTimer = setTimeout(async () => {
    if (autosaveInFlight) return
    if (hydratedFlowId.value !== lib.activeNode?.id) return
    autosaveInFlight = true
    try {
      await persistPageFlow()
      lib.status = `已自动保存 ${new Date().toLocaleTimeString()}`
    } catch {
      /* libraryStore 已提示 */
    } finally {
      autosaveInFlight = false
    }
  }, 500)
}

async function closeEditor() {
  clearAutosaveTimer()
  await persistActive()
  lib.setActive(null)
  hydratedFlowId.value = null
  lib.status = '已关闭编辑'
}

/** 点左侧目录 → 回到看板（保存并关闭编辑） */
async function browseFolder() {
  clearAutosaveTimer()
  if (editing.value) await persistActive()
  lib.setActive(null)
  hydratedFlowId.value = null
}

function enterFolder(folderId: string) {
  selectedFolderId.value = folderId
  lib.expanded[folderId] = true
  lib.persistMeta()
  browseFolder()
}

async function saveCurrent() {
  clearAutosaveTimer()
  await applyDocRename()
  const cur = lib.activeNode
  if (!cur || cur.type !== 'page_flow') return
  await persistPageFlow({ confirmEmptyOverwrite: true })
  const parentName = cur.parentId
    ? lib.findNode(cur.parentId)?.name || '…'
    : folderName.value
  lib.status = `已保存「${editDocName.value || cur.name}」→ ${parentName} · ${cur.id}`
  ElMessage.success('已保存到服务器')
}

async function ensureParentFolder(preferred?: string | null): Promise<string> {
  let parentId = preferred ?? selectedFolderId.value
  if (parentId === null || (parentId && lib.findNode(parentId)?.type !== 'folder')) {
    let def = lib.nodes.find(n => n.type === 'folder' && n.name === '默认目录')
    if (!def) def = await lib.createFolder('默认目录', null)
    parentId = def.id
    selectedFolderId.value = def.id
  }
  return parentId
}

async function openFile(node: LibNode) {
  if (node.type === 'folder') return
  if (node.type !== 'page_flow') return
  if (lib.activeNode?.id === node.id && editing.value && hydratedFlowId.value === node.id) return
  clearAutosaveTimer()
  await persistActive()

  // 先暂停 hydrate，避免加载过程中误触发自动保存
  hydratedFlowId.value = null
  editDocName.value = node.name
  if (node.parentId) selectedFolderId.value = node.parentId

  // 关键：先把 config 灌进 store，再 setActive 挂载 VueFlow，避免空画布闪现/竞态写回
  const data = await lib.loadPageFlowPayload(node.id)
  if (data) store.applySnapshot({ ...data, name: node.name })
  else store.clearGraph()
  hydratedFlowId.value = node.id
  lib.setActive(node.id)
}

async function applyDocRename() {
  const cur = lib.activeNode
  const name = editDocName.value.trim()
  if (!cur || !name || cur.type === 'folder') return
  if (cur.name !== name) await lib.renameNode(cur.id, name)
}

function askCreateFolder(parentId: string | null) {
  creatingKind.value = 'folder'
  createParentId.value = parentId
  createName.value = parentId ? '新建子目录' : '新建目录'
}

const folderDialogTitle = computed(() =>
  createParentId.value ? '新建子目录' : '新建根目录'
)

const folderDialogHint = computed(() => {
  if (!createParentId.value) return '将创建在资源树根级'
  const p = lib.findNode(createParentId.value)
  return p ? `父目录：${p.name}` : '将创建为子目录'
})

async function confirmCreateFolder() {
  if (creatingKind.value !== 'folder') return
  const name = createName.value.trim()
  if (!name) {
    ElMessage.warning('请输入目录名称')
    return
  }
  try {
    const folder = await lib.createFolder(name, createParentId.value)
    selectedFolderId.value = folder.id
    creatingKind.value = null
  } catch {
    // libraryStore 已 ElMessage.error；弹窗保持打开以便重试
  }
}

function cancelCreate() {
  creatingKind.value = null
}

async function askCreateFlow(parentId?: string | null) {
  const pid = await ensureParentFolder(parentId ?? selectedFolderId.value)
  const flow = await lib.createPageFlow('未命名页面流', pid)
  await openFile(flow)
  lib.status = `已创建页面流（${flow.id}）`
}

async function exportCurrent() {
  const cur = lib.activeNode
  if (!cur || cur.type === 'folder') return
  await persistActive()
  await exportFile(cur)
}

async function exportFile(node: LibNode) {
  const envelope = await lib.exportDoc(node.id)
  if (!envelope) return
  const blob = new Blob([JSON.stringify(envelope, null, 2)], { type: 'application/json' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${node.id}.json`
  a.click()
  URL.revokeObjectURL(a.href)
  lib.status = `已导出 ${node.id}`
}

async function importJsonFile(file: File) {
  try {
    const text = await file.text()
    const envelope = JSON.parse(text)
    const node = await lib.importDoc(envelope, {
      overwrite: overwriteImport.value,
      directoryId: selectedFolderId.value,
    })
    if (node && node.type === 'page_flow') await openFile(node)
  } catch (e: any) {
    ElMessage.error(e?.message || 'JSON 解析失败')
  }
}

function onImportPick(ev: Event) {
  const input = ev.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (file) importJsonFile(file)
}

onMounted(async () => {
  await nextTick()
  if ((window as any).lucide) (window as any).lucide.createIcons()
  try {
    const boot = await lib.bootstrapIfEmpty()
    // bootstrap 内 loadUi 会恢复上次 activeId；只用来定位目录，绝不带着空 store 进入编辑
    const remembered = lib.activeId ? lib.findNode(lib.activeId) : null
    if (boot) {
      selectedFolderId.value = boot.folder.id
    } else {
      const folders = lib.nodes.filter(n => n.type === 'folder')
      selectedFolderId.value =
        (remembered?.type === 'folder' && remembered.id) ||
        remembered?.parentId ||
        folders[0]?.id ||
        null
    }
  } catch {
    selectedFolderId.value = null
    error.value = '加载工作流数据失败，请检查网络连接'
  }
  lib.setActive(null)
  hydratedFlowId.value = null
  ready.value = true
  document.addEventListener('visibilitychange', onVisibilitySave)
  window.addEventListener('pagehide', onVisibilitySave)
})

function onVisibilitySave() {
  if (document.visibilityState === 'hidden' || document.visibilityState === undefined) {
    clearAutosaveTimer()
    // fire-and-forget：切走/刷新前尽量落盘
    void persistActive()
  }
}

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', onVisibilitySave)
  window.removeEventListener('pagehide', onVisibilitySave)
  clearAutosaveTimer()
  void persistActive()
})

// 画布变更 → 防抖自动保存（刷新前通常已落库）
watch(
  () => ({
    n: store.nodes.length,
    l: store.links.length,
    hid: hydratedFlowId.value,
    aid: lib.activeId,
  }),
  () => schedulePageFlowAutosave()
)

// 深监听节点内容（改名、端口、属性）
watch(
  () => store.nodes,
  () => schedulePageFlowAutosave(),
  { deep: true }
)
</script>

<template>
  <div class="doc-page workflow-workbench">
    <header class="wb-header">
      <div class="brand">
        <span
          class="brand-mark brand-mark--lucide"
          style="background: linear-gradient(135deg,#BDE0FE,#93c5fd)"
        >
          <i data-lucide="git-branch"></i>
        </span>
        <div>
          <h1 class="brand-title">工作流工作台</h1>
          <p class="brand-sub">{{ breadcrumb }}</p>
        </div>
      </div>

      <div class="header-actions">
        <label class="hdr-btn import-label">
          导入 JSON
          <input type="file" accept="application/json,.json" hidden @change="onImportPick" />
        </label>
        <label class="overwrite-lab">
          <input v-model="overwriteImport" type="checkbox" />
          同 ID 覆盖
        </label>
        <template v-if="editing">
          <button type="button" class="hdr-btn" @click="closeEditor">关闭编辑</button>
          <button type="button" class="hdr-btn" @click="exportCurrent">导出 JSON</button>
          <button type="button" class="hdr-btn primary" @click="saveCurrent">保存</button>
        </template>
        <span v-if="lib.status" class="status-pill">{{ lib.status }}</span>
      </div>
    </header>

    <ErrorState v-if="error" :message="error" @retry="retryLoad" />

    <Teleport to="body">
      <div
        v-if="creatingKind === 'folder'"
        class="wf-modal-backdrop"
        @click.self="cancelCreate"
      >
        <div
          class="wf-modal"
          role="dialog"
          aria-modal="true"
          aria-labelledby="wf-folder-dialog-title"
          @keydown.esc="cancelCreate"
        >
          <h3 id="wf-folder-dialog-title" class="wf-modal-title">{{ folderDialogTitle }}</h3>
          <p class="wf-modal-hint">{{ folderDialogHint }}</p>
          <label class="wf-modal-label" for="wf-folder-name">目录名称</label>
          <input
            id="wf-folder-name"
            v-model="createName"
            class="wf-modal-inp"
            maxlength="80"
            autofocus
            @focus="($event.target as HTMLInputElement).select()"
            @keydown.enter="confirmCreateFolder"
          />
          <div class="wf-modal-actions">
            <button type="button" class="hdr-btn" @click="cancelCreate">取消</button>
            <button type="button" class="hdr-btn primary" @click="confirmCreateFolder">确定</button>
          </div>
        </div>
      </div>
    </Teleport>

    <div class="wb-body">
      <WorkflowDirTree
        v-model:selected-folder-id="selectedFolderId"
        :active-file-id="editing ? lib.activeId : null"
        @browse="browseFolder"
        @open="openFile"
        @create-folder="askCreateFolder"
        @create-flow="askCreateFlow"
        @export="exportFile"
      />

      <!-- 未打开文件：目录看板 -->
      <WorkflowFileBrowser
        v-if="ready && !editing"
        :folder-id="selectedFolderId"
        :folder-name="folderName"
        @open="openFile"
        @create-flow="askCreateFlow()"
        @create-folder="askCreateFolder"
        @export="exportFile"
        @enter-folder="enterFolder"
      />

      <!-- 打开文件：编辑区（页面流 VueFlow） -->
      <main v-else-if="ready && editing" class="wb-main">
        <PageFlowVueFlow
          v-if="lib.activeNode?.type === 'page_flow'"
          v-model:doc-name="editDocName"
          :doc-id="lib.activeNode.id"
          :seed-demo="false"
          @back="browseFolder"
          @rename="applyDocRename"
        />
      </main>
    </div>
  </div>
</template>

<style scoped>
.workflow-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: transparent;
  overflow: hidden;
}
.wb-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  background: rgba(255,255,255,0.52);
  border-bottom: 1px solid var(--ink);
  
  flex-shrink: 0;
  /* z-index 10 = 内容区之上（0 内容区 / 50 固定头部口径） */
  z-index: 10;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.brand-mark {
  width: 40px;
  height: 40px;
  display: grid;
  place-items: center;
  font-size: var(--app-size-xl);
  border-radius: 14px;
  box-shadow: var(--app-icon-shadow);
}
.brand-mark--lucide :deep(svg) {
  width: 20px;
  height: 20px;
  color: var(--app-bg-card);
  stroke: var(--app-bg-card);
}
.brand-title {
  margin: 0;
  font-size: var(--app-size-md);
  font-weight: 800;
  color: var(--ink);
}
.brand-sub {
  margin: 2px 0 0;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--app-ink-muted);
}
.header-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.hdr-btn {
  padding: 7px 14px;
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  color: var(--ac-ink-muted);
}
.import-label { display: inline-flex; align-items: center; }
.overwrite-lab {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--ac-ink-muted);
  cursor: pointer;
}
.hdr-btn.primary {
  background: linear-gradient(135deg, var(--app-green-deep), var(--app-blue));
  color: var(--app-bg-card);
  border-color: var(--app-green-deep);
}
.hdr-btn:hover { filter: brightness(1.03); }
.status-pill {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-green-deep);
  padding: 4px 10px;
  background: rgba(162,210,255,0.16);
  border-radius: 999px;
}
.wb-body {
  flex: 1;
  min-height: 0;
  display: flex;
}
.wb-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 10px 12px 12px;
}
</style>

<style>
.wf-modal-backdrop {
  position: fixed;
  inset: 0;
  /* z-index 70 = 弹窗层（.claude/rules/frontend.md z-index 层级；原 10000 超界收敛） */
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(74,78,105,0.26);
}
.wf-modal {
  width: min(400px, 100%);
  padding: 22px 22px 18px;
  background: var(--app-bg-card);
  border: 1px solid var(--ink);
  border-radius: 18px;
  box-shadow: var(--app-shadow-lg);
  font-family: var(--app-font, 'Cascadia Mono', 'Noto Sans SC', sans-serif);
  color: var(--ink);
  
}
.wf-modal-title {
  margin: 0;
  font-size: var(--app-size-md);
  font-weight: 800;
}
.wf-modal-hint {
  margin: 6px 0 16px;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--app-ink-muted);
}
.wf-modal-label {
  display: block;
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  margin-bottom: 6px;
}
.wf-modal-inp {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 1.5px solid var(--ink);
  border-radius: 12px;
  background: #ffffff;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  outline: none;
}
.wf-modal-inp:focus { border-color: var(--app-blue); }
.wf-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
.wf-modal .hdr-btn {
  padding: 8px 16px;
  border: 1.5px solid var(--ink);
  border-radius: 999px;
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  color: var(--app-ink-muted);
}
.wf-modal .hdr-btn.primary {
  background: linear-gradient(135deg, var(--app-green-deep), var(--app-blue));
  color: var(--app-bg-card);
  border-color: var(--app-green-deep);
}
.wf-modal .hdr-btn:hover { filter: brightness(1.03); }
</style>
