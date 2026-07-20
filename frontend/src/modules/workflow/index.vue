<script setup lang="ts">
/**
 * 工作流工作台
 * 左：目录+文件树（右键/长按移动）
 * 右：点击文件后直接编辑内容（不再显示文件网格）
 */
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import { useTestCaseStore } from '@/modules/workflow/stores/testCaseStore'
import { useLibraryStore, type LibNode } from '@/modules/workflow/stores/libraryStore'
import type { Block } from '@/modules/workflow/types/testCase'
import { fromCaseManagerSteps } from '@/modules/workflow/composables/caseBridge'
import { getDefinition } from '@/modules/workflow/api.js'
import PageFlowVueFlow from './components/vueflow/PageFlowVueFlow.vue'
import TestCaseBlockly from './components/blockly/TestCaseBlockly.vue'
import WorkflowDirTree from './components/WorkflowDirTree.vue'
import WorkflowFileBrowser from './components/WorkflowFileBrowser.vue'
import ImportCasesDialog from './components/ImportCasesDialog.vue'
// animal-theme.css removed — tokens now in shared/styles/tokens.css

const store = useWorkflowStore()
const tcStore = useTestCaseStore()
const lib = useLibraryStore()

const selectedFolderId = ref<string | null>(null)
const ready = ref(false)
const createName = ref('')
const creatingKind = ref<'folder' | null>(null)
const createParentId = ref<string | null>(null)
const editDocName = ref('')
const overwriteImport = ref(false)
const showImportCases = ref(false)
const importTargetFolderId = ref<string | null>(null)
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
  const kind = cur.type === 'page_flow' ? '页面流' : '测试用例'
  const title = editDocName.value || cur.name
  return parent
    ? `${parent.name} / ${kind}「${title}」`
    : `${kind}「${title}」`
})

async function persistActive() {
  await applyDocRename()
  const cur = lib.activeNode
  if (!cur || cur.type === 'folder') return
  if (cur.type === 'page_flow') {
    await lib.savePageFlowPayload(cur.id, store.snapshotGraph(cur.name))
  } else if (cur.type === 'test_case') {
    await lib.saveCaseDraft(cur.id, {
      name: tcStore.caseName || editDocName.value || cur.name,
      package_name: tcStore.packageName,
      blocks: JSON.parse(JSON.stringify(tcStore.rootBlocks)),
      linkedCaseId: tcStore.linkedCaseId || cur.caseId || '',
    })
  }
}

async function closeEditor() {
  await persistActive()
  lib.setActive(null)
  lib.status = '已关闭编辑'
}

/** 点左侧目录 → 回到看板（保存并关闭编辑） */
async function browseFolder() {
  if (editing.value) await persistActive()
  lib.setActive(null)
}

function enterFolder(folderId: string) {
  selectedFolderId.value = folderId
  lib.expanded[folderId] = true
  lib.persistMeta()
  browseFolder()
}

async function saveCurrent() {
  await persistActive()
  const cur = lib.activeNode
  if (!cur) return
  const parentName = cur.parentId
    ? lib.findNode(cur.parentId)?.name || '…'
    : folderName.value
  lib.status = `已保存「${editDocName.value || cur.name}」→ ${parentName} · ${cur.id}`
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
  if (lib.activeNode?.id === node.id && editing.value) return
  await persistActive()
  lib.setActive(node.id)
  editDocName.value = node.name
  if (node.parentId) selectedFolderId.value = node.parentId

  if (node.type === 'page_flow') {
    const data = await lib.loadPageFlowPayload(node.id)
    if (data) store.applySnapshot({ ...data, name: node.name })
    else store.clearGraph()
  } else if (node.type === 'test_case') {
    const draft = await lib.loadCaseDraft(node.id)
    if (draft?.linkedCaseId || node.caseId) {
      const cid = draft?.linkedCaseId || node.caseId
      try {
        const res = await getDefinition(cid)
        const d = res.data?.definition
        if (d) {
          const steps = fromCaseManagerSteps(d.steps_data || [])
          tcStore.loadStepBlocks(steps as Block[], {
            id: d.id,
            title: d.title || node.name,
            packageName: d.package_name || 'com.example.app',
            directoryId: d.directory_id ?? null,
          })
          editDocName.value = d.title || node.name
          return
        }
      } catch { /* use draft */ }
    }
    if (draft) {
      tcStore.loadStepBlocks((draft.blocks || []) as Block[], {
        id: draft.linkedCaseId || node.caseId || '',
        title: draft.name || node.name,
        packageName: draft.package_name || 'com.example.app',
      })
      editDocName.value = draft.name || node.name
    } else {
      tcStore.clearAll()
      tcStore.caseName = node.name
      tcStore.setLinkedCase(node.caseId || '', node.name)
      editDocName.value = node.name
    }
  }
}

async function applyDocRename() {
  const cur = lib.activeNode
  const name = editDocName.value.trim()
  if (!cur || !name || cur.type === 'folder') return
  if (cur.name !== name) await lib.renameNode(cur.id, name)
  if (cur.type === 'test_case' && tcStore.caseName !== name) {
    tcStore.caseName = name
  }
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

async function askCreateCase(parentId?: string | null) {
  const pid = await ensureParentFolder(parentId ?? selectedFolderId.value)
  const tc = await lib.createTestCase('未命名用例', pid, { syncPlatform: false })
  await openFile(tc)
  lib.status = `已创建测试用例（${tc.id}）`
}

async function openImportCases(parentId?: string | null) {
  importTargetFolderId.value = await ensureParentFolder(parentId ?? selectedFolderId.value)
  showImportCases.value = true
}

async function onCasesImported(ids: string[]) {
  if (ids.length === 1) {
    const n = lib.findNode(ids[0])
    if (n) await openFile(n)
  } else {
    lib.status = `已从用例库导入 ${ids.length} 条`
  }
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
    if (node && node.type !== 'folder') await openFile(node)
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

function handleAddToCase(payload: {
  nodeId: string
  slotIndex: number
  stepType: 'click' | 'wait'
}) {
  const node = store.findNode(payload.nodeId)
  const port = node?.outputs[payload.slotIndex]
  if (!port?.el) {
    tcStore.setStatus('该端口没有关联元素')
    return
  }
  if (lib.activeNode?.type !== 'test_case') {
    const parentId = lib.activeNode?.parentId ?? selectedFolderId.value ?? null
    lib.createTestCase(`用例-${port.name}`, parentId, { syncPlatform: false }).then((created) => {
      openFile(created).then(() => addBridgedStep(port, payload.stepType))
    })
    return
  }
  addBridgedStep(port, payload.stepType)
}

function addBridgedStep(
  port: { name: string; el?: { xpath?: string; id: string } },
  stepType: 'click' | 'wait'
) {
  const block = tcStore.addStepAfter(tcStore.selectedId, stepType)
  tcStore.updateStepData(block.id, {
    label: port.name,
    xpath: port.el?.xpath || '',
    element_id: port.el?.id,
    element_label: port.name,
    timeout: stepType === 'wait' ? 10 : 5,
  })
  tcStore.setStatus(`已添加步骤「${port.name}」`)
  persistActive()
}

onMounted(async () => {
  try {
    const boot = await lib.bootstrapIfEmpty()
    if (boot) {
      selectedFolderId.value = boot.folder.id
    } else {
      const folders = lib.nodes.filter(n => n.type === 'folder')
      selectedFolderId.value =
        (lib.activeNode?.type === 'folder' && lib.activeNode.id) ||
        lib.activeNode?.parentId ||
        folders[0]?.id ||
        null
    }
  } catch {
    selectedFolderId.value = null
  }
  // 进入时不自动打开编辑器
  if (lib.activeNode?.type === 'folder' || !lib.activeNode) {
    lib.setActive(null)
  }
  ready.value = true
})

watch(
  () => [tcStore.caseName, tcStore.linkedCaseId] as const,
  () => {
    const cur = lib.activeNode
    if (cur?.type !== 'test_case') return
    if (tcStore.caseName && editDocName.value !== tcStore.caseName) {
      editDocName.value = tcStore.caseName
    }
    if (tcStore.caseName && cur.name !== tcStore.caseName) {
      lib.renameNode(cur.id, tcStore.caseName)
    }
    if (tcStore.linkedCaseId && cur.caseId !== tcStore.linkedCaseId) {
      lib.setCaseId(cur.id, tcStore.linkedCaseId)
    }
  }
)
</script>

<template>
  <div class="doc-page workflow-workbench">
    <header class="wb-header">
      <div class="brand">
        <span class="brand-mark">🏝️</span>
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
        @create-case="askCreateCase"
        @import-cases="openImportCases"
        @export="exportFile"
      />

      <!-- 未打开文件：目录看板 -->
      <WorkflowFileBrowser
        v-if="ready && !editing"
        :folder-id="selectedFolderId"
        :folder-name="folderName"
        @open="openFile"
        @create-flow="askCreateFlow()"
        @create-case="askCreateCase()"
        @create-folder="askCreateFolder"
        @export="exportFile"
        @enter-folder="enterFolder"
      />

      <!-- 打开文件：编辑区（无侧栏，元信息进编辑器工具栏） -->
      <main v-else-if="ready && editing" class="wb-main">
        <PageFlowVueFlow
          v-if="lib.activeNode?.type === 'page_flow'"
          v-model:doc-name="editDocName"
          :doc-id="lib.activeNode.id"
          :seed-demo="false"
          @back="browseFolder"
          @rename="applyDocRename"
          @add-to-case="handleAddToCase"
        />
        <TestCaseBlockly
          v-else-if="lib.activeNode?.type === 'test_case'"
          :active="true"
          :doc-id="lib.activeNode.id"
          @back="browseFolder"
        />
      </main>
    </div>

    <ImportCasesDialog
      v-model="showImportCases"
      :target-folder-id="importTargetFolderId"
      @imported="onCasesImported"
    />
  </div>
</template>

<style scoped>
.workflow-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  background: var(--ac-cream, #fdf8f0);
  overflow: hidden;
}
.wb-header {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 18px;
  background: rgba(255, 251, 245, 0.95);
  border-bottom: 2px solid var(--ac-border, rgba(139, 115, 85, 0.16));
  flex-shrink: 0;
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
  font-size: 22px;
  background: linear-gradient(145deg, #f7cd67, #f5c6a3);
  border-radius: 14px;
  border: 2px solid rgba(139, 115, 85, 0.18);
}
.brand-title {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--ac-ink, #4a3a28);
}
.brand-sub {
  margin: 2px 0 0;
  font-size: 12px;
  font-weight: 700;
  color: var(--ac-ink-faint, #988b7a);
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
  border: 2px solid var(--ac-border);
  border-radius: 999px;
  background: #fffbf5;
  font-size: 12px;
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
  font-size: 11px;
  font-weight: 700;
  color: var(--ac-ink-muted);
  cursor: pointer;
}
.hdr-btn.primary {
  background: var(--ac-teal, #19c8b9);
  color: #fff;
  border-color: #14b3a5;
}
.hdr-btn:hover { filter: brightness(1.03); }
.status-pill {
  font-size: 11px;
  font-weight: 700;
  color: #0d7a70;
  padding: 4px 10px;
  background: rgba(25, 200, 185, 0.12);
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
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  background: rgba(74, 58, 40, 0.4);
}
.wf-modal {
  width: min(400px, 100%);
  padding: 22px 22px 18px;
  background: #fffbf5;
  border: 2px solid rgba(139, 115, 85, 0.28);
  border-radius: 18px;
  box-shadow: 0 18px 48px rgba(74, 58, 40, 0.28);
  font-family: 'Nunito', 'Noto Sans SC', system-ui, sans-serif;
  color: #4a3a28;
}
.wf-modal-title {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
}
.wf-modal-hint {
  margin: 6px 0 16px;
  font-size: 12px;
  font-weight: 600;
  color: #988b7a;
}
.wf-modal-label {
  display: block;
  font-size: 12px;
  font-weight: 800;
  color: #5c4a35;
  margin-bottom: 6px;
}
.wf-modal-inp {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: 2px solid rgba(139, 115, 85, 0.22);
  border-radius: 12px;
  background: #ffffff;
  color: #4a3a28;
  font-size: 14px;
  font-weight: 700;
  font-family: inherit;
  outline: none;
}
.wf-modal-inp:focus { border-color: #19c8b9; }
.wf-modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
.wf-modal .hdr-btn {
  padding: 8px 16px;
  border: 2px solid rgba(139, 115, 85, 0.2);
  border-radius: 999px;
  background: #fffbf5;
  font-size: 13px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  color: #5c4a35;
}
.wf-modal .hdr-btn.primary {
  background: #19c8b9;
  color: #fff;
  border-color: #14b3a5;
}
.wf-modal .hdr-btn:hover { filter: brightness(1.03); }
</style>
