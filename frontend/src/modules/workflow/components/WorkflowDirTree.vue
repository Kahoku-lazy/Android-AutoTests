<script setup lang="ts">
/**
 * 左侧资源树：目录 + 文件
 * - 点击文件 → 右侧打开编辑
 * - 右键目录 → 新建子目录 / 页面流
 * - 右键文件 → 打开 / 重命名 / 导出 / 删除
 * - 长按拖拽 → 移入目录
 */
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useLibraryStore, type LibNode } from '@/modules/workflow/stores/libraryStore'

const props = defineProps<{
  selectedFolderId: string | null
  activeFileId?: string | null
}>()

const emit = defineEmits<{
  'update:selectedFolderId': [id: string | null]
  browse: []
  open: [node: LibNode]
  createFolder: [parentId: string | null]
  createFlow: [parentId: string | null]
  export: [node: LibNode]
}>()

const lib = useLibraryStore()
const renamingId = ref<string | null>(null)
const renameValue = ref('')

/** 右键菜单 */
const ctx = ref<{
  x: number
  y: number
  node: LibNode | null
  kind: 'root' | 'folder' | 'file'
} | null>(null)

/** 长按拖拽 */
const LONG_MS = 420
const dragId = ref<string | null>(null)
const dropTargetId = ref<string | null | undefined>(undefined) // null=root
const pressTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const dragging = ref(false)
const DIR_COLLAPSE_KEY = 'wf_dir_pane_collapsed'
const paneCollapsed = ref(localStorage.getItem(DIR_COLLAPSE_KEY) === '1')

function togglePane() {
  paneCollapsed.value = !paneCollapsed.value
  localStorage.setItem(DIR_COLLAPSE_KEY, paneCollapsed.value ? '1' : '0')
}

type TreeRow = { node: LibNode; depth: number }

const treeRows = computed(() => {
  const rows: TreeRow[] = []
  function walk(parentId: string | null, depth: number) {
    const kids = lib.nodes
      .filter(n => n.parentId === parentId)
      .slice()
      .sort((a, b) => {
        const order = { folder: 0, page_flow: 1 }
        return (order[a.type] - order[b.type]) || a.name.localeCompare(b.name, 'zh')
      })
    for (const n of kids) {
      rows.push({ node: n, depth })
      if (n.type === 'folder' && lib.expanded[n.id]) walk(n.id, depth + 1)
    }
  }
  walk(null, 0)
  return rows
})

function fileCount(folderId: string): number {
  return lib.nodes.filter(
    n => n.parentId === folderId && n.type === 'page_flow'
  ).length
}

function closeCtx() {
  ctx.value = null
}

function onDocClick() {
  closeCtx()
}

onMounted(() => document.addEventListener('click', onDocClick))
onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  clearPress()
})

function setFolderId(id: string | null) {
  if (id) {
    lib.expanded[id] = true
    lib.persistMeta()
  }
  emit('update:selectedFolderId', id)
}

/** 点击目录 / 根 → 切看板 */
function selectFolder(id: string | null) {
  setFolderId(id)
  emit('browse')
}

function onRowClick(n: LibNode) {
  if (dragging.value) return
  if (n.type === 'folder') {
    selectFolder(n.id)
    return
  }
  setFolderId(n.parentId)
  emit('open', n)
}

function onCtxMenu(e: MouseEvent, n: LibNode | null, kind: 'root' | 'folder' | 'file') {
  e.preventDefault()
  e.stopPropagation()
  ctx.value = { x: e.clientX, y: e.clientY, node: n, kind }
}

function startRename(n: LibNode) {
  renamingId.value = n.id
  renameValue.value = n.name
  closeCtx()
}

async function confirmRename() {
  if (renamingId.value) {
    await lib.renameNode(renamingId.value, renameValue.value)
    renamingId.value = null
  }
}

async function removeNode(n: LibNode) {
  const tip =
    n.type === 'folder'
      ? `删除目录「${n.name}」？其中的页面流也会删除。`
      : `删除「${n.name}」？\n${n.id}`
  if (!confirm(tip)) return
  await lib.deleteNode(n.id)
  if (props.selectedFolderId === n.id) emit('update:selectedFolderId', null)
  closeCtx()
}

function ctxCreateFolder() {
  const parent =
    ctx.value?.kind === 'folder' ? ctx.value.node?.id ?? null : null
  emit('createFolder', parent)
  if (parent) {
    lib.expanded[parent] = true
    selectFolder(parent)
  }
  closeCtx()
}

function ctxCreateFlow() {
  const parent =
    ctx.value?.kind === 'folder'
      ? ctx.value.node?.id ?? null
      : props.selectedFolderId
  emit('createFlow', parent)
  closeCtx()
}

function ctxOpen() {
  const n = ctx.value?.node
  if (n && n.type !== 'folder') emit('open', n)
  closeCtx()
}

function ctxExport() {
  const n = ctx.value?.node
  if (n && n.type !== 'folder') emit('export', n)
  closeCtx()
}

function ctxRename() {
  if (ctx.value?.node) startRename(ctx.value.node)
}

function ctxDelete() {
  if (ctx.value?.node) removeNode(ctx.value.node)
}

/* ── 长按拖拽移动 ── */
function clearPress() {
  if (pressTimer.value) {
    clearTimeout(pressTimer.value)
    pressTimer.value = null
  }
}

function onPointerDown(e: PointerEvent, n: LibNode) {
  if (e.button !== 0) return
  clearPress()
  pressTimer.value = setTimeout(() => {
    dragging.value = true
    dragId.value = n.id
    dropTargetId.value = undefined
    window.addEventListener('pointerup', onPointerUp, { once: true })
  }, LONG_MS)
}

function onPointerUp() {
  clearPress()
  if (dragging.value && dragId.value && dropTargetId.value !== undefined) {
    const target = dropTargetId.value
    const src = dragId.value
    if (src !== target) {
      lib.moveNode(src, target)
    }
  }
  // 短延迟避免长按结束后立刻触发 click
  setTimeout(() => {
    dragging.value = false
    dragId.value = null
    dropTargetId.value = undefined
  }, 80)
}

function onPointerEnterDrop(folderId: string | null) {
  if (!dragging.value) return
  dropTargetId.value = folderId
}

function onPointerCancel() {
  clearPress()
  dragging.value = false
  dragId.value = null
  dropTargetId.value = undefined
}

function onCreateRoot() {
  emit('createFolder', null)
}
</script>

<template>
  <aside
    class="dir-pane"
    :class="{ 'dir-pane--collapsed': paneCollapsed }"
    @pointerup="onPointerUp"
    @pointercancel="onPointerCancel"
  >
    <!-- 折叠态：细条 -->
    <button
      v-if="paneCollapsed"
      type="button"
      class="dir-rail"
      title="展开资源树"
      @click="togglePane"
    >
      <span class="rail-chev">›</span>
      <span class="rail-label">资源</span>
    </button>

    <template v-else>
      <div class="dir-head">
        <div class="dir-head-top">
          <div class="dir-title">资源</div>
          <button
            type="button"
            class="dir-toggle"
            title="收起资源树"
            @click="togglePane"
          >
            ‹
          </button>
        </div>
        <p class="dir-desc">右键新建 · 长按拖入目录 · 点文件编辑</p>
        <div class="dir-actions">
          <button type="button" class="mini" @click="onCreateRoot">+ 根目录</button>
          <button
            type="button"
            class="mini"
            @click="emit('createFlow', selectedFolderId)"
          >
            + 页面流
          </button>
        </div>
      </div>

      <div class="dir-scroll">
        <div
          class="dir-row root"
          :class="{
            active: selectedFolderId === null && !activeFileId,
            'drop-on': dragging && dropTargetId === null,
          }"
          @click="selectFolder(null)"
          @contextmenu="onCtxMenu($event, null, 'root')"
          @pointerenter="onPointerEnterDrop(null)"
        >
          <span class="ico">🗂</span>
          <span class="name">全部 / 根</span>
          <span class="badge">{{ lib.nodes.filter(n => n.type !== 'folder').length }}</span>
        </div>

        <div v-if="!treeRows.length" class="empty-state">
          还没有内容。<br />右键空白处或点「+ 根目录」开始。
        </div>

        <div
          v-for="row in treeRows"
          :key="row.node.id"
          class="dir-row"
          :class="{
            active:
              row.node.type === 'folder'
                ? selectedFolderId === row.node.id && !activeFileId
                : activeFileId === row.node.id,
            file: row.node.type !== 'folder',
            flow: row.node.type === 'page_flow',
            dragging: dragId === row.node.id,
            'drop-on':
              dragging &&
              row.node.type === 'folder' &&
              dropTargetId === row.node.id,
          }"
          :style="{ paddingLeft: `${10 + row.depth * 14}px` }"
          @click="onRowClick(row.node)"
          @contextmenu="
            onCtxMenu(
              $event,
              row.node,
              row.node.type === 'folder' ? 'folder' : 'file'
            )
          "
          @pointerdown="onPointerDown($event, row.node)"
          @pointerenter="
            row.node.type === 'folder' && onPointerEnterDrop(row.node.id)
          "
        >
          <button
            v-if="row.node.type === 'folder'"
            type="button"
            class="chev"
            @click.stop="lib.toggleExpand(row.node.id)"
          >
            {{ lib.expanded[row.node.id] ? '▾' : '▸' }}
          </button>
          <span v-else class="chev-sp" />
          <span class="ico">
            <template v-if="row.node.type === 'folder'">
              {{ lib.expanded[row.node.id] ? '📂' : '📁' }}
            </template>
            <template v-else>🗺️</template>
          </span>
          <input
            v-if="renamingId === row.node.id"
            v-model="renameValue"
            class="rename-inp"
            @click.stop
            @keydown.enter="confirmRename"
            @blur="confirmRename"
          />
          <span v-else class="name" :title="row.node.type !== 'folder' ? row.node.id : ''">
            {{ row.node.name }}
          </span>
          <span v-if="row.node.type === 'folder'" class="badge">
            {{ fileCount(row.node.id) }}
          </span>
        </div>
      </div>

      <div v-if="dragging" class="drag-hint">
        拖到目标目录后松手 · 可放到「全部 / 根」
      </div>
    </template>

    <!-- 右键菜单 -->
    <Teleport to="body">
      <div
        v-if="ctx"
        class="wf-ctx"
        :style="{ left: `${ctx.x}px`, top: `${ctx.y}px` }"
        @click.stop
        @contextmenu.prevent
      >
        <template v-if="ctx.kind === 'root' || ctx.kind === 'folder'">
          <button type="button" @click="ctxCreateFolder">新建子目录</button>
          <button type="button" @click="ctxCreateFlow">新建页面流</button>
          <template v-if="ctx.kind === 'folder' && ctx.node">
            <hr />
            <button type="button" @click="ctxRename">重命名</button>
            <button type="button" class="danger" @click="ctxDelete">删除目录</button>
          </template>
        </template>
        <template v-else-if="ctx.kind === 'file' && ctx.node">
          <button type="button" @click="ctxOpen">打开 / 编辑</button>
          <button type="button" @click="ctxRename">重命名</button>
          <button type="button" @click="ctxExport">导出 JSON</button>
          <hr />
          <button type="button" class="danger" @click="ctxDelete">删除</button>
        </template>
      </div>
    </Teleport>
  </aside>
</template>

<style scoped>
.dir-pane {
  width: 264px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  overflow: hidden;
  position: relative;
  user-select: none;
  box-shadow: var(--app-shadow-sm);
  transition: width 0.2s ease;
}
.dir-pane--collapsed {
  width: 40px;
}
.dir-rail {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 14px 4px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  color: var(--ac-accent-deep);
}
.dir-rail:hover { background: var(--ac-accent-soft); }
.rail-chev { font-size: var(--app-size-lg); font-weight: 800; }
.rail-label {
  writing-mode: vertical-rl;
  font-size: var(--app-size-sm);
  font-weight: 700;
  letter-spacing: 0.12em;
}
.dir-head {
  padding: 14px 14px 12px;
  border-bottom: 2px solid var(--ac-border-soft);
}
.dir-head-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.dir-toggle {
  width: 26px;
  height: 26px;
  border: 2px solid var(--ink);
  border-radius: 8px;
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 800;
  cursor: pointer;
  color: var(--app-text-secondary);
  line-height: 1;
  flex-shrink: 0;
}
.dir-toggle:hover { border-color: var(--c-workflow); color: var(--ink); }
.dir-title {
  font-size: var(--app-size-md);
  font-weight: 800;
  color: var(--ink);
}
.dir-desc {
  margin: 4px 0 12px;
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  font-weight: 600;
  line-height: 1.5;
}
.dir-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.mini {
  padding: 5px 11px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  color: var(--ink);
  transition: background 0.12s var(--app-ease);
}
.mini:hover { background: var(--ac-accent-soft); }
.mini:focus-visible { outline: 2px solid var(--c-workflow); outline-offset: 2px; }
.dir-scroll { flex: 1; overflow: auto; padding: 8px 8px 12px; }
.empty-state {
  margin: 12px 8px;
  padding: 16px 12px;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--app-text-secondary);
  line-height: 1.6;
  text-align: center;
  background: var(--app-bg-subtle);
  border-radius: var(--app-radius-sm);
  border: 1px dashed var(--ac-border-soft);
}
.dir-row {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 4px 8px;
  border: none;
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  font-family: inherit;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--ink);
  text-align: left;
  box-sizing: border-box;
  transition: background 0.12s var(--app-ease);
}
.dir-row:hover { background: var(--ac-accent-soft); }
.dir-row.active {
  background: var(--ac-accent-soft);
  box-shadow: inset 3px 0 0 var(--c-workflow);
}
.dir-row.drop-on {
  outline: 2px dashed var(--c-workflow);
  outline-offset: -2px;
  background: var(--ac-accent-soft);
}
.dir-row.dragging {
  opacity: 0.45;
}
.dir-row.root {
  margin-bottom: 4px;
  font-weight: 700;
}
.dir-row.flow .name { color: var(--ac-accent-deep); }
.chev {
  border: none;
  background: transparent;
  width: 16px;
  cursor: pointer;
  color: var(--app-text-secondary);
  padding: 0;
  flex-shrink: 0;
  font-size: var(--app-size-xs);
}
.chev-sp { width: 16px; flex-shrink: 0; }
.ico { font-size: var(--app-size-sm); flex-shrink: 0; }
.name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.badge {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 1px 7px;
  border-radius: 999px;
  background: var(--ac-accent-soft);
  color: var(--ac-accent-deep);
  flex-shrink: 0;
}
.rename-inp {
  flex: 1;
  min-width: 0;
  padding: 3px 7px;
  border: 2px solid var(--c-workflow);
  border-radius: 8px;
  font-size: var(--app-size-sm);
  font-weight: 600;
  font-family: inherit;
  color: var(--ink);
  outline: none;
}
.drag-hint {
  padding: 8px 10px;
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--ac-accent-deep);
  background: var(--ac-accent-soft);
  border-top: 2px solid var(--ac-border-soft);
  text-align: center;
}
</style>

<style>
/* 右键菜单挂到 body：用全局 token + 字面量，不能依赖 .workflow-workbench 作用域变量 */
.wf-ctx {
  position: fixed;
  z-index: 60;
  min-width: 176px;
  padding: 6px;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-lg);
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.wf-ctx button {
  border: none;
  background: transparent;
  text-align: left;
  padding: 9px 12px;
  border-radius: 8px;
  font-size: var(--app-size-sm);
  font-weight: 600;
  font-family: inherit;
  color: var(--ink);
  cursor: pointer;
  transition: background 0.12s var(--app-ease);
}
.wf-ctx button:hover { background: rgba(137, 207, 240, 0.16); }
.wf-ctx button.danger { color: var(--app-status-danger-text); }
.wf-ctx button.danger:hover { background: var(--app-status-danger-bg); }
.wf-ctx hr {
  border: none;
  border-top: 1px solid var(--app-border-light);
  margin: 4px 6px;
}
</style>
