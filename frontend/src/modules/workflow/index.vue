<script setup lang="ts">
/**
 * 工作流工作台
 * 资源态：仅目录树；点击页面流后整页进入绘制
 * 绘制态：VueFlow 全宽；「返回上一级」保存后回到目录树
 */
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import { useLibraryStore, type LibNode } from '@/modules/workflow/stores/libraryStore'
import { getWorkflowPrototype } from '@/modules/workflow/api'
import {
  NODE_TYPE_LABELS,
  DEFAULT_NAMES,
  isFlowDocType,
} from '@/modules/workflow/constants'
import PageFlowVueFlow from './components/vueflow/PageFlowVueFlow.vue'
import WorkflowDirTree from './components/WorkflowDirTree.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'

const route = useRoute()
const router = useRouter()
const store = useWorkflowStore()
const lib = useLibraryStore()

const prototypeId = computed(() => Number(route.params.prototypeId))
const prototypeName = ref('')
const selectedFolderId = ref<string | null>(null)
const ready = ref(false)
const error = ref('')
function retryLoad() {
  error.value = ''
  ready.value = false
  void bootWorkbench()
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
  const root = prototypeName.value || '原型'
  const cur = lib.activeNode
  if (!editing.value) {
    return selectedFolderId.value
      ? `${root} / ${folderName.value}`
      : `${root} / 全部`
  }
  if (!cur) return `${root} / 编辑`
  const parent = cur.parentId ? lib.findNode(cur.parentId) : null
  const title = editDocName.value || cur.name
  const kind = NODE_TYPE_LABELS[cur.type] || '文档'
  return parent
    ? `${root} / ${parent.name} / ${kind}「${title}」`
    : `${root} / ${kind}「${title}」`
})

function goBackToList() {
  clearAutosaveTimer()
  void persistActive().finally(() => {
    router.push('/workflow')
  })
}

async function bootWorkbench() {
  if (!Number.isFinite(prototypeId.value) || prototypeId.value <= 0) {
    error.value = '无效的原型 ID'
    return
  }
  lib.setPrototypeId(prototypeId.value)
  try {
    const { data } = await getWorkflowPrototype(prototypeId.value)
    if (!data.status || !data.prototype) {
      error.value = data.message || '原型不存在'
      return
    }
    prototypeName.value = data.prototype.name || ''
    const boot = await lib.bootstrapIfEmpty()
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
    lib.setActive(null)
    hydratedFlowId.value = null
    ready.value = true
  } catch {
    selectedFolderId.value = null
    error.value = '加载工作流数据失败，请检查网络连接'
  }
}

function clearAutosaveTimer() {
  if (autosaveTimer) {
    clearTimeout(autosaveTimer)
    autosaveTimer = null
  }
}

async function persistPageFlow(opts?: { confirmEmptyOverwrite?: boolean }) {
  const cur = lib.activeNode
  if (!cur || !isFlowDocType(cur.type)) return
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
  if (!cur || !isFlowDocType(cur.type)) return
  await persistPageFlow()
}

function schedulePageFlowAutosave() {
  const cur = lib.activeNode
  if (!cur || !isFlowDocType(cur.type)) return
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

/** 关闭绘制 → 回到资源目录树 */
async function browseFolder() {
  clearAutosaveTimer()
  if (editing.value) await persistActive()
  lib.setActive(null)
  hydratedFlowId.value = null
}

async function saveCurrent() {
  clearAutosaveTimer()
  await applyDocRename()
  const cur = lib.activeNode
  if (!cur || !isFlowDocType(cur.type)) return
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
  if (!isFlowDocType(node.type)) return
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
  if (!createParentId.value) return '将创建在当前原型根级'
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
  const flow = await lib.createPageFlow(DEFAULT_NAMES.PAGE_FLOW, pid)
  await openFile(flow)
  lib.status = `已创建页面流（${flow.id}）`
}

async function askCreateApiFlow(parentId?: string | null) {
  const pid = await ensureParentFolder(parentId ?? selectedFolderId.value)
  const flow = await lib.createApiFlow(DEFAULT_NAMES.API_FLOW, pid)
  await openFile(flow)
  lib.status = `已创建接口流（${flow.id}）`
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
    if (node && isFlowDocType(node.type)) await openFile(node)
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
  await bootWorkbench()
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
    <WorkbenchHeader
      :title="prototypeName || '原型工作台'"
      :subtitle="breadcrumb"
      icon="git-branch"
    >
      <template #actions>
        <div class="wf-actions">
          <button type="button" class="wf-btn" @click="goBackToList">← 返回原型列表</button>
          <label class="wf-btn">
            导入 JSON
            <input type="file" accept="application/json,.json" hidden @change="onImportPick" />
          </label>
          <button
            v-if="editing"
            type="button"
            class="wf-btn"
            @click="exportCurrent"
          >
            导出 JSON
          </button>
          <label class="overwrite-lab">
            <input v-model="overwriteImport" type="checkbox" />
            同 ID 覆盖
          </label>
          <button
            v-if="editing"
            type="button"
            class="wf-btn wf-btn--primary"
            @click="saveCurrent"
          >
            保存
          </button>
          <span v-if="lib.status" class="status-pill" :title="lib.status">{{ lib.status }}</span>
        </div>
      </template>
    </WorkbenchHeader>

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
            <button type="button" class="wf-btn" @click="cancelCreate">取消</button>
            <button type="button" class="wf-btn wf-btn--primary" @click="confirmCreateFolder">确定</button>
          </div>
        </div>
      </div>
    </Teleport>

    <div class="wb-body" :class="{ 'wb-body--editing': editing }">
      <!-- 资源态：仅目录树 -->
      <WorkflowDirTree
        v-if="ready && !editing"
        v-model:selected-folder-id="selectedFolderId"
        solo
        :active-file-id="null"
        @browse="browseFolder"
        @open="openFile"
        @create-folder="askCreateFolder"
        @create-flow="askCreateFlow"
        @create-api-flow="askCreateApiFlow"
        @export="exportFile"
      />

      <!-- 绘制态：整页 VueFlow -->
      <main v-else-if="ready && editing" class="wb-main wb-main--canvas">
        <PageFlowVueFlow
          v-if="lib.activeNode && isFlowDocType(lib.activeNode.type)"
          v-model:doc-name="editDocName"
          :doc-id="lib.activeNode.id"
          :flow-kind="lib.activeNode.type"
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

/* ── 顶栏动作区 ── */
.wf-actions {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}
.wf-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  line-height: 1.4;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm);
  transition: background 0.12s var(--app-ease), box-shadow 0.12s var(--app-ease),
    transform 0.12s var(--app-ease);
}
.wf-btn:hover {
  background: var(--ac-accent-soft);
  box-shadow: var(--app-shadow-md);
}
.wf-btn:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.05);
}
.wf-btn:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 2px;
}
.wf-btn--primary {
  background: var(--c-workflow);
}
.wf-btn--primary:hover {
  background: var(--c-workflow);
  filter: brightness(1.04);
}
.overwrite-lab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px var(--app-space-sm);
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--app-text-secondary);
  cursor: pointer;
  white-space: nowrap;
}
.overwrite-lab input {
  width: 15px;
  height: 15px;
  accent-color: var(--c-workflow);
  cursor: pointer;
}
.status-pill {
  max-width: 240px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--ac-accent-deep);
  padding: var(--app-space-xs) 10px;
  background: var(--ac-accent-soft);
  border: 1.5px solid rgba(137, 207, 240, 0.4);
  border-radius: 999px;
}

/* ── 主体：资源两栏 / 绘制全宽 ── */
.wb-body {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 12px;
  padding: 12px;
}
.wb-body--editing {
  gap: 0;
}
.wb-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  overflow: hidden;
  box-shadow: var(--app-shadow-sm);
}
.wb-main--canvas {
  /* 绘制态占满 wb-body，无侧栏挤占 */
  width: 100%;
}
</style>

<style>
.wf-modal-backdrop {
  position: fixed;
  inset: 0;
  /* z-index 70 = 弹窗层（.agents/skills/android-autotests-rules/references/frontend.md z-index 层级） */
  z-index: 70;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: var(--app-overlay);
}
.wf-modal {
  width: min(400px, 100%);
  padding: 22px 22px 18px;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-lg);
  font-family: var(--app-font, 'Cascadia Mono', 'Noto Sans SC', sans-serif);
  color: var(--ink);
}
.wf-modal-title {
  margin: 0;
  font-size: var(--app-size-lg);
  font-weight: 800;
  color: var(--ink);
}
.wf-modal-hint {
  margin: 6px 0 var(--app-space-md);
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--app-text-secondary);
}
.wf-modal-label {
  display: block;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
  margin-bottom: 6px;
}
.wf-modal-inp {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: #ffffff;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 600;
  font-family: inherit;
  outline: none;
  transition: border-color 0.12s var(--app-ease);
}
.wf-modal-inp:focus {
  border-color: var(--c-workflow);
}
.wf-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
.wf-modal .wf-btn {
  padding: 7px var(--app-space-md);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  color: var(--ink);
  box-shadow: var(--app-shadow-sm);
  transition: background 0.12s var(--app-ease);
}
.wf-modal .wf-btn:hover {
  background: rgba(137, 207, 240, 0.16);
}
.wf-modal .wf-btn--primary {
  background: var(--c-workflow);
}
.wf-modal .wf-btn--primary:hover {
  background: var(--c-workflow);
  filter: brightness(1.04);
}
.wf-modal .wf-btn:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 2px;
}
</style>
