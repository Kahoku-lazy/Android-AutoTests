<script setup lang="ts">
/**
 * 目录看板：当前目录下的文件（卡片）+ 子目录（可折叠标题区）
 */
import { computed, ref, watch } from 'vue'
import { useLibraryStore, type LibNode } from '@/modules/workflow/stores/libraryStore'

const props = defineProps<{
  folderId: string | null
  folderName: string
}>()

const emit = defineEmits<{
  open: [node: LibNode]
  createFlow: []
  createFolder: [parentId: string | null]
  export: [node: LibNode]
  enterFolder: [folderId: string]
}>()

const lib = useLibraryStore()
const filter = ref<'all' | 'page_flow'>('all')
const renamingId = ref<string | null>(null)
const renameValue = ref('')
/** 子目录折叠：默认全部展开 */
const sectionOpen = ref<Record<string, boolean>>({})

watch(
  () => props.folderId,
  () => {
    // 进入新目录时，展开其直接子目录
    const kids = lib.nodes.filter(n => n.type === 'folder' && n.parentId === props.folderId)
    for (const k of kids) {
      if (sectionOpen.value[k.id] === undefined) sectionOpen.value[k.id] = true
    }
  },
  { immediate: true }
)

function sortFiles(list: LibNode[]): LibNode[] {
  return list.slice().sort((a, b) => a.name.localeCompare(b.name, 'zh'))
}

function filesOf(parentId: string | null): LibNode[] {
  let list = lib.nodes.filter(n => n.type === 'page_flow' && n.parentId === parentId)
  if (filter.value !== 'all') list = list.filter(n => n.type === filter.value)
  return sortFiles(list)
}

/** 本层直接文件 */
const directFiles = computed(() => filesOf(props.folderId))

/** 子目录分段 */
const childFolders = computed(() =>
  lib.nodes
    .filter(n => n.type === 'folder' && n.parentId === props.folderId)
    .slice()
    .sort((a, b) => a.name.localeCompare(b.name, 'zh'))
)

const totalVisible = computed(() => {
  let n = directFiles.value.length
  for (const f of childFolders.value) n += filesOf(f.id).length
  return n
})

function toggleSection(id: string) {
  sectionOpen.value[id] = !sectionOpen.value[id]
}

function startRename(n: LibNode) {
  renamingId.value = n.id
  renameValue.value = n.name
}

async function confirmRename() {
  if (renamingId.value) {
    await lib.renameNode(renamingId.value, renameValue.value)
    renamingId.value = null
  }
}

async function removeFile(n: LibNode) {
  if (!confirm(`删除「${n.name}」？\nID: ${n.id}`)) return
  await lib.deleteNode(n.id)
}

function fmtTime(iso: string) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch {
    return ''
  }
}
</script>

<template>
  <div class="board">
    <div class="board-head">
      <div>
        <h2 class="board-title">{{ folderName }}</h2>
        <p class="board-sub">
          文件以卡片展示 · 子目录可折叠 · 点卡片打开编辑
        </p>
      </div>
      <div class="board-actions">
        <button type="button" class="btn ghost" @click="emit('createFolder', folderId)">
          + 子目录
        </button>
        <button type="button" class="btn flow" @click="emit('createFlow')">+ 页面流</button>
      </div>
    </div>

    <div class="filters">
      <button
        type="button"
        class="chip"
        :class="{ on: filter === 'all' }"
        @click="filter = 'all'"
      >
        全部 {{ totalVisible }}
      </button>
      <button
        type="button"
        class="chip"
        :class="{ on: filter === 'page_flow' }"
        @click="filter = 'page_flow'"
      >
        页面流
      </button>
    </div>

    <div v-if="!directFiles.length && !childFolders.length" class="empty">
      <div class="empty-ico">📂</div>
      <p>这个目录还是空的</p>
      <p class="empty-tip">新建页面流，或添加子目录整理文件</p>
      <div class="empty-btns">
        <button type="button" class="btn flow solid" @click="emit('createFlow')">新建页面流</button>
      </div>
    </div>

    <template v-else>
      <!-- 本层文件卡片 -->
      <section v-if="directFiles.length" class="section">
        <div class="section-title static">
          <span class="sec-ico">📄</span>
          <span>本目录文件</span>
          <span class="sec-count">{{ directFiles.length }}</span>
        </div>
        <div class="file-grid">
          <button
            v-for="f in directFiles"
            :key="f.id"
            type="button"
            class="file-card"
            :class="f.type"
            @click="emit('open', f)"
          >
            <div class="file-top">
              <span class="file-ico">🗺️</span>
              <span class="file-type">页面流</span>
              <span class="file-ops" @click.stop>
                <button type="button" title="导出" @click="emit('export', f)">↓</button>
                <button type="button" title="重命名" @click="startRename(f)">✎</button>
                <button type="button" class="danger" title="删除" @click="removeFile(f)">×</button>
              </span>
            </div>
            <input
              v-if="renamingId === f.id"
              v-model="renameValue"
              class="rename-inp"
              @click.stop
              @keydown.enter="confirmRename"
              @blur="confirmRename"
            />
            <div v-else class="file-name">{{ f.name }}</div>
            <div class="file-id">{{ f.id }}</div>
            <div class="file-meta">更新 {{ fmtTime(f.updatedAt) }}</div>
            <div class="file-cta">打开 →</div>
          </button>
        </div>
      </section>

      <!-- 子目录：下拉标题 -->
      <section
        v-for="folder in childFolders"
        :key="folder.id"
        class="section folder-sec"
      >
        <button
          type="button"
          class="section-title"
          @click="toggleSection(folder.id)"
        >
          <span class="chev">{{ sectionOpen[folder.id] !== false ? '▾' : '▸' }}</span>
          <span class="sec-ico">{{ sectionOpen[folder.id] !== false ? '📂' : '📁' }}</span>
          <span class="sec-name">{{ folder.name }}</span>
          <span class="sec-count">{{ filesOf(folder.id).length }} 文件</span>
          <span
            class="enter"
            title="进入此目录"
            @click.stop="emit('enterFolder', folder.id)"
          >
            进入 →
          </span>
        </button>

        <div v-show="sectionOpen[folder.id] !== false" class="section-body">
          <div v-if="!filesOf(folder.id).length" class="sec-empty">
            子目录暂无文件
            <button type="button" class="linkish" @click="emit('enterFolder', folder.id)">
              进入并新建
            </button>
          </div>
          <div v-else class="file-grid">
            <button
              v-for="f in filesOf(folder.id)"
              :key="f.id"
              type="button"
              class="file-card"
              :class="f.type"
              @click="emit('open', f)"
            >
              <div class="file-top">
                <span class="file-ico">🗺️</span>
                <span class="file-type">页面流</span>
                <span class="file-ops" @click.stop>
                  <button type="button" title="导出" @click="emit('export', f)">↓</button>
                  <button type="button" title="重命名" @click="startRename(f)">✎</button>
                  <button type="button" class="danger" title="删除" @click="removeFile(f)">×</button>
                </span>
              </div>
              <input
                v-if="renamingId === f.id"
                v-model="renameValue"
                class="rename-inp"
                @click.stop
                @keydown.enter="confirmRename"
                @blur="confirmRename"
              />
              <div v-else class="file-name">{{ f.name }}</div>
              <div class="file-id">{{ f.id }}</div>
              <div class="file-meta">更新 {{ fmtTime(f.updatedAt) }}</div>
              <div class="file-cta">打开 →</div>
            </button>
          </div>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.board {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  padding: 20px var(--app-space-lg) var(--app-space-lg);
  overflow: auto;
  background: transparent;
}
.board-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  margin-bottom: var(--app-space-md);
}
.board-title {
  margin: 0;
  font-size: var(--app-size-lg);
  font-weight: 800;
  color: var(--ink);
}
.board-sub {
  margin: var(--app-space-xs) 0 0;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--app-text-secondary);
}
.board-actions { display: flex; gap: var(--app-space-sm); flex-wrap: wrap; }
.btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 14px;
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  background: var(--app-bg-card);
  color: var(--ink);
  box-shadow: var(--app-shadow-sm);
  transition: background 0.12s var(--app-ease), box-shadow 0.12s var(--app-ease),
    transform 0.12s var(--app-ease);
}
.btn.ghost:hover,
.btn.flow:hover {
  background: var(--ac-accent-soft);
  box-shadow: var(--app-shadow-md);
}
.btn:active {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.05);
}
.btn:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 2px;
}
.btn.flow,
.btn.solid.flow {
  background: var(--c-workflow);
}
.btn.flow:hover,
.btn.solid.flow:hover {
  background: var(--c-workflow);
  filter: brightness(1.04);
}
.filters { display: flex; gap: var(--app-space-sm); margin-bottom: var(--app-space-md); }
.chip {
  padding: 5px 13px;
  border-radius: 999px;
  border: 2px solid var(--ink);
  background: var(--app-bg-card);
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  color: var(--app-text-secondary);
  transition: background 0.12s var(--app-ease), color 0.12s var(--app-ease);
}
.chip.on {
  background: var(--ac-accent-soft);
  border-color: var(--c-workflow);
  color: var(--ac-accent-deep);
}
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--app-space-2xl) 20px;
  color: var(--app-text-secondary);
  font-weight: 600;
}
.empty-ico { font-size: var(--app-size-2xl); margin-bottom: 10px; }
.empty-tip {
  max-width: 360px;
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
  font-weight: 600;
  line-height: 1.6;
  margin: var(--app-space-sm) 0 18px;
}
.empty-btns { display: flex; gap: 10px; }
.section { margin-bottom: 22px; }
.section-title {
  width: 100%;
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  padding: 11px 14px;
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  font-family: inherit;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
  cursor: pointer;
  text-align: left;
  box-shadow: var(--app-shadow-sm);
  transition: border-color 0.12s var(--app-ease);
}
.section-title.static { cursor: default; }
.section-title:not(.static):hover { border-color: var(--c-workflow); }
.chev { width: 14px; color: var(--app-text-secondary); }
.sec-ico { font-size: var(--app-size-md); }
.sec-name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.sec-count {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 2px var(--app-space-sm);
  border-radius: 999px;
  background: var(--ac-accent-soft);
  color: var(--ac-accent-deep);
}
.enter {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ac-accent-deep);
  padding: 2px var(--app-space-sm);
  border-radius: 8px;
}
.enter:hover { background: var(--ac-accent-soft); }
.section-body { padding: 14px 2px 0 var(--app-space-sm); }
.sec-empty {
  padding: 12px 14px;
  font-size: var(--app-size-sm);
  font-weight: 600;
  color: var(--app-text-secondary);
  display: flex;
  gap: 10px;
  align-items: center;
}
.linkish {
  border: none;
  background: transparent;
  color: var(--ac-accent-deep);
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  font-size: var(--app-size-sm);
}
/* 本目录文件：标题与卡片之间留白（对齐子目录 section-body） */
.section > .file-grid {
  margin-top: 14px;
  padding-left: var(--app-space-sm);
}
.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 14px;
}
.file-card {
  text-align: left;
  padding: 15px;
  border: 2px solid var(--ac-border-soft);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  cursor: pointer;
  font-family: inherit;
  box-shadow: var(--app-shadow-sm);
  transition: transform 0.12s var(--app-ease), border-color 0.12s var(--app-ease),
    box-shadow 0.12s var(--app-ease);
}
.file-card:hover {
  transform: translateY(-2px);
  border-color: var(--c-workflow);
  box-shadow: var(--app-shadow-md);
}
.file-card:focus-visible {
  outline: 2px solid var(--c-workflow);
  outline-offset: 2px;
}
.file-card.page_flow { border-left: 4px solid var(--c-workflow); }
.file-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: var(--app-space-sm);
}
.file-ico { font-size: var(--app-size-lg); }
.file-type {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--app-text-secondary);
}
.file-ops {
  margin-left: auto;
  display: flex;
  opacity: 0;
  transition: opacity 0.12s var(--app-ease);
}
.file-card:hover .file-ops,
.file-card:focus-visible .file-ops { opacity: 1; }
.file-ops button {
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--app-text-secondary);
  padding: 3px 6px;
  border-radius: 6px;
  font-size: var(--app-size-sm);
}
.file-ops button:hover { background: var(--ac-accent-soft); color: var(--ink); }
.file-ops button.danger:hover { background: var(--app-status-danger-bg); color: var(--app-status-danger-text); }
.file-name {
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  margin-bottom: 5px;
  word-break: break-word;
  line-height: 1.45;
}
.file-id {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--ac-accent-deep);
  margin-bottom: var(--app-space-sm);
  word-break: break-all;
  font-family: var(--app-font-mono);
  line-height: 1.4;
}
.file-meta {
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-text-secondary);
}
.file-cta {
  margin-top: 12px;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ac-accent-deep);
}
.rename-inp {
  width: 100%;
  margin-bottom: 6px;
  padding: 5px 9px;
  border: 2px solid var(--c-workflow);
  border-radius: 8px;
  font-size: var(--app-size-sm);
  font-weight: 700;
  font-family: inherit;
  color: var(--ink);
  outline: none;
}
</style>
