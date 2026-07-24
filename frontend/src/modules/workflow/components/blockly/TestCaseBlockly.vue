<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as Blockly from 'blockly'
import { registerAutotestBlocks } from '@/modules/workflow/composables/blocklyBlocks'
import {
  workspaceToBlocks,
  loadBlocksIntoWorkspace,
  applyXpathToSelected,
} from '@/modules/workflow/composables/blocklySerializer'
import { useTestCaseStore } from '@/modules/workflow/stores/testCaseStore'
import { useWorkflowStore } from '@/modules/workflow/stores/workflowStore'
import { useImportExport } from '@/modules/workflow/composables/useImportExport'
import {
  buildCaseSaveForm,
  fromCaseManagerSteps,
} from '@/modules/workflow/composables/caseBridge'
import {
  listDefinitions,
  getDefinition,
  saveDefinition,
  fetchDirectories,
} from '@/modules/workflow/api.js'
import ScratchPalette from './ScratchPalette.vue'

const props = withDefaults(
  defineProps<{ active?: boolean; docId?: string }>(),
  { active: true, docId: '' }
)

const emit = defineEmits<{ back: [] }>()

const tcStore = useTestCaseStore()
const wfStore = useWorkflowStore()
const iexport = useImportExport()

const hostRef = ref<HTMLDivElement | null>(null)
const status = ref('积木步骤可保存到「测试用例」模块 · 与用例设计同步')
const showBridge = ref(false)
const showCasePicker = ref(false)
const caseList = ref<any[]>([])
const caseDirs = ref<any[]>([])
const caseLoading = ref(false)
const caseSaving = ref(false)
const caseFilter = ref('')
let workspace: Blockly.WorkspaceSvg | null = null
let syncing = false
let resizeObs: ResizeObserver | null = null

/** Blockly sizes SVG from host at inject time; v-show:none → tiny canvas until resize */
function resizeWorkspace() {
  if (!workspace || !hostRef.value) return
  const { width, height } = hostRef.value.getBoundingClientRect()
  if (width < 8 || height < 8) return
  Blockly.svgResize(workspace)
}

const ANIMAL_THEME = Blockly.Theme.defineTheme('autotest-scratch', {
  name: 'autotest-scratch',
  base: Blockly.Themes.Zelos,
  componentStyles: {
    workspaceBackgroundColour: '#f7f0e4',
    toolboxBackgroundColour: '#eef7ff',
    toolboxForegroundColour: 'var(--ink)',
    flyoutBackgroundColour: '#ffffff',
    flyoutForegroundColour: 'var(--ink)',
    flyoutOpacity: 1,
    scrollbarColour: '#c4b5a0',
    insertionMarkerColour: '#6f9fd8',
    insertionMarkerOpacity: 0.5,
    scrollbarOpacity: 0.5,
    cursorColour: '#8b7355',
  },
  fontStyle: {
    family: "'Quicksand', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    weight: '700',
    size: 12,
  },
})

function pushToStore() {
  if (!workspace || syncing) return
  syncing = true
  try {
    const blocks = workspaceToBlocks(workspace)
    tcStore.rootBlocks = blocks
    status.value = `积木已同步 · ${tcStore.stepCount} 个步骤`
  } finally {
    syncing = false
  }
}

function pullFromStore() {
  if (!workspace || syncing) return
  syncing = true
  try {
    loadBlocksIntoWorkspace(workspace, tcStore.rootBlocks)
    status.value = '已加载用例积木'
  } finally {
    syncing = false
  }
}

function loadMock() {
  tcStore.loadMock()
  nextTick(pullFromStore)
}

function saveLocal() {
  pushToStore()
  tcStore.saveToLocal()
  status.value = '已存本地草稿: ' + tcStore.caseName
}

async function saveToCaseLibrary() {
  pushToStore()
  const title = tcStore.caseName.trim()
  if (!title || title === '未命名用例') {
    status.value = '请先填写用例名称'
    return
  }
  if (!tcStore.packageName.trim()) {
    status.value = '请填写 App 包名（与用例设计必填一致）'
    return
  }
  if (tcStore.stepCount === 0) {
    status.value = '没有可保存的步骤'
    return
  }
  caseSaving.value = true
  try {
    const form = buildCaseSaveForm({
      id: tcStore.linkedCaseId || '',
      title,
      packageName: tcStore.packageName,
      directoryId: tcStore.directoryId,
      blocks: tcStore.rootBlocks,
    })
    const res = await saveDefinition(form)
    const data = res.data
    if (!data?.ok) {
      status.value = data?.error || '保存到用例库失败'
      return
    }
    tcStore.setLinkedCase(data.id || tcStore.linkedCaseId, title, tcStore.packageName)
    status.value = `已同步到用例设计「${title}」· id=${data.id}`
  } catch (e: any) {
    const msg = e?.response?.data?.error || e?.message || '保存失败'
    status.value = String(msg)
  } finally {
    caseSaving.value = false
  }
}

async function openCasePicker() {
  showCasePicker.value = true
  caseLoading.value = true
  caseFilter.value = ''
  try {
    const [defsRes, dirRes] = await Promise.all([
      listDefinitions(),
      fetchDirectories().catch(() => ({ data: { directories: [] } })),
    ])
    caseList.value = defsRes.data?.definitions || []
    caseDirs.value = dirRes.data?.directories || []
    if (!Array.isArray(caseDirs.value)) caseDirs.value = []
  } catch (e: any) {
    caseList.value = []
    status.value = e?.response?.data?.error || e?.message || '加载用例列表失败'
  } finally {
    caseLoading.value = false
  }
}

async function loadCaseFromLibrary(item: { id: string }) {
  caseLoading.value = true
  try {
    const res = await getDefinition(item.id)
    const d = res.data?.definition
    if (!d) {
      status.value = '用例不存在'
      return
    }
    const steps = fromCaseManagerSteps(d.steps_data || [])
    tcStore.loadStepBlocks(steps, {
      id: d.id,
      title: d.title,
      packageName: d.package_name || tcStore.packageName,
      directoryId: d.directory_id ?? null,
    })
    nextTick(() => {
      pullFromStore()
      status.value = `已从用例设计加载「${d.title}」· ${steps.length} 步`
    })
    showCasePicker.value = false
  } catch (e: any) {
    status.value = e?.response?.data?.error || e?.message || '加载失败'
  } finally {
    caseLoading.value = false
  }
}

function filteredCases() {
  const q = caseFilter.value.trim().toLowerCase()
  if (!q) return caseList.value
  return caseList.value.filter(
    (c) =>
      (c.title || '').toLowerCase().includes(q) ||
      (c.id || '').toLowerCase().includes(q) ||
      (c.package_name || '').toLowerCase().includes(q)
  )
}

function exportJson() {
  pushToStore()
  const data = iexport.buildExport(tcStore.caseName, '', tcStore.rootBlocks, tcStore.packageName)
  iexport.downloadFile(data)
  status.value = '已导出 JSON'
}

function clearWs() {
  if (!confirm('清空积木画布？')) return
  workspace?.clear()
  tcStore.clearAll()
  status.value = '画布已清空'
}

function applyBridge(el: { xpath: string; label: string }) {
  if (!workspace) return
  const ok = applyXpathToSelected(workspace, el.xpath, el.label)
  status.value = ok ? `已写入定位: ${el.label}` : '请先选中带「定位」字段的积木'
  if (ok) pushToStore()
  showBridge.value = false
}

/** Place a new block near viewport center / stacked below last top block */
function addBlockType(type: string) {
  if (!workspace) return
  const b = workspace.newBlock(type) as Blockly.BlockSvg
  if (type === 'at_start_app' || type === 'at_kill_app' || type === 'at_restart_app') {
    const f = b.getField('PACKAGE')
    if (f) b.setFieldValue(tcStore.packageName || 'com.example.app', 'PACKAGE')
  }
  b.initSvg()
  b.render()

  const metrics = workspace.getMetrics()
  const tops = workspace.getTopBlocks(true)
  let x = (metrics?.viewLeft || 0) + 48
  let y = (metrics?.viewTop || 0) + 40
  if (tops.length) {
    const last = tops[tops.length - 1] as Blockly.BlockSvg
    const xy = last.getRelativeToSurfaceXY()
    x = xy.x
    y = xy.y + last.getHeightWidth().height + 16
  }
  b.moveBy(x, y)
  workspace.centerOnBlock(b.id)
  b.select()
  pushToStore()
  status.value = `已添加积木`
}

function onCanvasDragOver(e: DragEvent) {
  if (e.dataTransfer?.types.includes('application/x-blockly-type')) {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'copy'
  }
}

function onCanvasDrop(e: DragEvent) {
  e.preventDefault()
  const type = e.dataTransfer?.getData('application/x-blockly-type')
  if (!type || !workspace || !hostRef.value) return

  const b = workspace.newBlock(type) as Blockly.BlockSvg
  b.initSvg()
  b.render()

  const rect = hostRef.value.getBoundingClientRect()
  const metrics = workspace.getMetrics()
  const scale = workspace.scale
  const x = (e.clientX - rect.left - (metrics?.absoluteLeft || 0)) / scale + (metrics?.viewLeft || 0)
  const y = (e.clientY - rect.top - (metrics?.absoluteTop || 0)) / scale + (metrics?.viewTop || 0)
  b.moveBy(x - 40, y - 20)
  b.select()
  pushToStore()
  status.value = '积木已放入画布'
}

onMounted(() => {
  registerAutotestBlocks()
  if (!hostRef.value) return

  workspace = Blockly.inject(hostRef.value, {
    // Custom ScratchPalette replaces native toolbox
    toolbox: undefined,
    theme: ANIMAL_THEME,
    trashcan: true,
    grid: { spacing: 24, length: 3, colour: '#d9cbb8', snap: true },
    zoom: {
      controls: true,
      wheel: true,
      startScale: 0.92,
      maxScale: 2,
      minScale: 0.4,
      scaleSpeed: 1.12,
    },
    move: { scrollbars: true, drag: true, wheel: true },
    renderer: 'zelos',
    sounds: false,
  })

  workspace.addChangeListener((e: Blockly.Events.Abstract) => {
    if (e.isUiEvent) return
    if (syncing) return
    pushToStore()
  })

  if (tcStore.rootBlocks.length === 0) {
    tcStore.initDemo()
  }
  pullFromStore()

  resizeObs = new ResizeObserver(() => resizeWorkspace())
  resizeObs.observe(hostRef.value)
  window.addEventListener('resize', resizeWorkspace)
  nextTick(() => requestAnimationFrame(resizeWorkspace))
})

onUnmounted(() => {
  resizeObs?.disconnect()
  resizeObs = null
  window.removeEventListener('resize', resizeWorkspace)
  workspace?.dispose()
  workspace = null
})

watch(
  () => props.active,
  (visible) => {
    if (!visible) return
    nextTick(() => {
      requestAnimationFrame(() => {
        resizeWorkspace()
        // second pass after layout paints (v-show → block)
        requestAnimationFrame(resizeWorkspace)
      })
    })
  },
  { immediate: true }
)

watch(
  () => tcStore.packageName,
  (pkg) => { status.value = '默认包名: ' + pkg }
)

// Library / 外部 loadStepBlocks 后刷新画布
watch(
  () => tcStore.contentRev,
  () => {
    if (!workspace || syncing) return
    nextTick(() => pullFromStore())
  }
)
</script>

<template>
  <div class="bx-root">
    <div class="bx-toolbar">
      <div class="toolbar-left">
        <button type="button" class="btn back" @click="emit('back')">← 看板</button>
        <input v-model="tcStore.caseName" class="inp name" placeholder="用例名称" />
        <input v-model="tcStore.packageName" class="inp pkg" placeholder="App 包名" />
        <span class="kind-chip">测试用例</span>
        <span v-if="docId" class="id-chip" :title="docId">{{ docId }}</span>
        <span v-if="tcStore.linkedCaseId" class="link-chip" :title="tcStore.linkedCaseId">
          已关联用例
        </span>
      </div>
      <div class="toolbar-actions">
        <button class="btn" @click="openCasePicker">打开用例</button>
        <button class="btn primary" :disabled="caseSaving" @click="saveToCaseLibrary">
          {{ caseSaving ? '保存中…' : '同步到用例库' }}
        </button>
        <button class="btn" @click="showBridge = !showBridge">绑定位</button>
        <button class="btn" @click="pullFromStore">刷新积木</button>
        <button class="btn" @click="saveLocal">本地草稿</button>
        <button class="btn" @click="exportJson">导出</button>
        <button class="btn" @click="loadMock">示例</button>
        <button class="btn danger" @click="clearWs">清空</button>
      </div>
      <span class="status">{{ status }}</span>
    </div>

    <div v-if="showCasePicker" class="case-picker-panel">
      <div class="case-picker-head">
        <strong>从用例设计加载</strong>
        <input v-model="caseFilter" class="inp" placeholder="搜索标题 / id / 包名…" />
        <button class="btn" @click="showCasePicker = false">关闭</button>
      </div>
      <div v-if="caseLoading" class="empty">加载中…</div>
      <div v-else-if="!filteredCases().length" class="empty">暂无用例 — 请先在「测试用例」中创建</div>
      <button
        v-for="c in filteredCases()"
        :key="c.id"
        type="button"
        class="case-item"
        @click="loadCaseFromLibrary(c)"
      >
        <strong>{{ c.title }}</strong>
        <span class="meta">{{ c.id }} · {{ c.package_name || '无包名' }} · {{ (c.steps_data || []).length }} 步</span>
      </button>
    </div>

    <div v-if="showBridge" class="bridge-panel">
      <div v-if="!wfStore.bridgedElements.length" class="empty">
        暂无页面元素 — 请先在「页面流」挂载元素端口
      </div>
      <button
        v-for="el in wfStore.bridgedElements"
        :key="el.element_id + el.page_node_id"
        class="bridge-item"
        @click="applyBridge(el)"
      >
        <strong>{{ el.page_name }} / {{ el.label }}</strong>
        <code>{{ el.xpath || '(无 xpath)' }}</code>
      </button>
    </div>

    <div class="bx-body">
      <ScratchPalette @add-block="addBlockType" />
      <div
        class="bx-stage"
        @dragover="onCanvasDragOver"
        @drop="onCanvasDrop"
      >
        <div class="stage-hint">
          <span class="hint-pill">积木画布</span>
          把左侧积木拖进来，或点击添加 · 上下卡扣可拼接
        </div>
        <div ref="hostRef" class="bx-host" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.bx-root {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--ac-paper);
  border: 2px solid var(--ac-border);
  border-radius: var(--ac-radius);
  box-shadow: var(--ac-shadow);
  overflow: hidden;
}
.bx-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.46);
  border-bottom: 1px solid var(--ink);
  flex-shrink: 0;
}
.toolbar-left,
.toolbar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.inp {
  padding: 7px 12px;
  border: 2px solid var(--ac-border);
  border-radius: 12px;
  background: var(--ac-cream);
  color: var(--ac-ink);
  font-size: 12px;
  font-family: inherit;
  font-weight: 700;
  outline: none;
}
.inp.name { width: 128px; }
.inp.pkg { width: 160px; font-family: ui-monospace, monospace; font-size: 11px; font-weight: 600; }
.inp:focus { border-color: var(--ac-teal); }
.link-chip {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  color: var(--app-green-deep);
  background: rgba(162,210,255,0.16);
  border: 1px solid rgba(162,210,255,0.28);
}
.kind-chip {
  font-size: 11px;
  font-weight: 800;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(247, 205, 103, 0.35);
  color: #6a5410;
}
.id-chip {
  font-size: 10px;
  font-weight: 700;
  color: var(--app-green-deep);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: rgba(162,210,255,0.12);
  padding: 3px 8px;
  border-radius: 8px;
}
.btn.back {
  background: #fff;
  color: var(--app-green-deep);
  border-color: rgba(162,210,255,0.42);
}
.case-picker-panel {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(162,210,255,0.10);
  border-bottom: 2px solid var(--ac-border-soft);
  max-height: 220px;
  overflow: auto;
}
.case-picker-head {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.case-picker-head .inp { flex: 1; min-width: 160px; }
.case-item {
  text-align: left;
  padding: 8px 12px;
  border: 2px solid var(--ac-border);
  border-radius: 12px;
  background: var(--ac-paper);
  color: var(--ac-ink);
  cursor: pointer;
  font-family: inherit;
}
.case-item:hover { border-color: var(--ac-teal); }
.case-item strong { display: block; font-size: 12px; }
.case-item .meta {
  display: block;
  font-size: 10px;
  color: var(--ac-ink-faint);
  margin-top: 2px;
}
.btn {
  padding: 7px 14px;
  border: 2px solid var(--ac-border);
  border-radius: 999px;
  background: var(--ac-paper);
  color: var(--ac-ink-muted);
  font-size: 12px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  box-shadow: var(--app-shadow-sm);
}
.btn:hover { border-color: var(--app-blue); color: var(--app-green-deep); }
.btn.primary {
  background: var(--ac-yellow);
  color: var(--ac-ink);
  border-color: #e0b52e;
}
.btn.danger:hover { border-color: var(--ac-red); color: var(--ac-red); }
.status {
  margin-left: auto;
  font-size: 12px;
  color: var(--app-green-deep);
  font-weight: 800;
}
.bridge-panel {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 14px;
  background: rgba(247, 205, 103, 0.18);
  border-bottom: 2px solid var(--ac-border-soft);
  max-height: 120px;
  overflow: auto;
}
.bridge-item {
  text-align: left;
  padding: 8px 12px;
  border: 2px solid var(--ac-border);
  border-radius: 12px;
  background: var(--ac-paper);
  color: var(--ac-ink);
  cursor: pointer;
  max-width: 280px;
  font-family: inherit;
}
.bridge-item:hover { border-color: var(--ac-teal); }
.bridge-item strong { display: block; font-size: 12px; }
.bridge-item code {
  display: block;
  font-size: 10px;
  color: var(--ac-ink-faint);
  margin-top: 2px;
}
.empty { font-size: 12px; color: var(--ac-ink-faint); font-weight: 700; }

.bx-body {
  flex: 1;
  min-height: 0;
  display: flex;
}
.bx-stage {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  position: relative;
  background:
    radial-gradient(circle at 20% 10%, rgba(162,210,255,0.22), transparent 40%),
    radial-gradient(circle at 90% 80%, rgba(111,185,141,0.12), transparent 35%),
    rgba(255,255,255,0.28);
}
.stage-hint {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  font-size: 12px;
  font-weight: 700;
  color: var(--ac-ink-faint);
  border-bottom: 1px dashed var(--ac-border-soft);
  flex-shrink: 0;
}
.hint-pill {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(162,210,255,0.16);
  color: var(--app-green-deep);
  font-size: 11px;
  font-weight: 800;
}
.bx-host {
  flex: 1;
  min-height: 0;
  width: 100%;
  position: relative;
  overflow: hidden;
}
</style>

<style>
/* Blockly injects fixed px on .injectionDiv — force fill + svgResize keeps in sync */
.bx-host .injectionDiv {
  width: 100% !important;
  height: 100% !important;
  position: absolute !important;
  inset: 0;
}
.bx-host .blocklySvg {
  width: 100% !important;
  height: 100% !important;
}
/* Zelos / Scratch feel — field bubbles & workspace chrome */
.blocklyMainBackground {
  stroke: none !important;
}
.blocklyText {
  font-family: var(--app-font, 'Quicksand', 'PingFang SC', sans-serif) !important;
  font-weight: 700 !important;
}
.blocklyHtmlInput {
  font-family: var(--app-font, 'Quicksand', 'PingFang SC', sans-serif) !important;
  font-weight: 700 !important;
  border-radius: 8px !important;
}
.blocklyZoom > image,
.blocklyZoom > .blocklyZoomReset > image {
  opacity: 0.75;
}
.blocklyScrollbarHandle {
  fill: #c4b5a0 !important;
}
.blocklyFlyout {
  display: none !important;
}
</style>
