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
  createCase: []
  createFolder: [parentId: string | null]
  export: [node: LibNode]
  enterFolder: [folderId: string]
}>()

const lib = useLibraryStore()
const filter = ref<'all' | 'page_flow' | 'test_case'>('all')
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
  return list.slice().sort((a, b) => {
    if (a.type !== b.type) return a.type === 'page_flow' ? -1 : 1
    return a.name.localeCompare(b.name, 'zh')
  })
}

function filesOf(parentId: string | null): LibNode[] {
  let list = lib.nodes.filter(n => n.type !== 'folder' && n.parentId === parentId)
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
        <button type="button" class="btn case" @click="emit('createCase')">+ 用例</button>
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
      <button
        type="button"
        class="chip"
        :class="{ on: filter === 'test_case' }"
        @click="filter = 'test_case'"
      >
        测试用例
      </button>
    </div>

    <div v-if="!directFiles.length && !childFolders.length" class="empty">
      <div class="empty-ico">📂</div>
      <p>这个目录还是空的</p>
      <p class="empty-tip">新建页面流 / 用例，或添加子目录整理文件</p>
      <div class="empty-btns">
        <button type="button" class="btn flow solid" @click="emit('createFlow')">新建页面流</button>
        <button type="button" class="btn case solid" @click="emit('createCase')">新建测试用例</button>
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
              <span class="file-ico">{{ f.type === 'page_flow' ? '🗺️' : '🧩' }}</span>
              <span class="file-type">{{ f.type === 'page_flow' ? '页面流' : '测试用例' }}</span>
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
                <span class="file-ico">{{ f.type === 'page_flow' ? '🗺️' : '🧩' }}</span>
                <span class="file-type">{{ f.type === 'page_flow' ? '页面流' : '测试用例' }}</span>
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
  padding: 16px 18px 20px;
  overflow: auto;
  background:
    radial-gradient(circle at 10% 0%, rgba(162,210,255,0.22), transparent 40%),
    transparent;
}
.board-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}
.board-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: var(--app-text);
}
.board-sub {
  margin: 4px 0 0;
  font-size: 12px;
  font-weight: 600;
  color: var(--ac-ink-faint);
}
.board-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn {
  padding: 7px 12px;
  border: 1.5px dashed var(--ac-border);
  border-radius: 999px;
  font-size: 12px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  background: transparent;
  color: var(--ac-ink-muted);
}
.btn.ghost:hover,
.btn.flow:hover {
  border-color: var(--app-blue);
  color: var(--app-green-deep);
  background: rgba(162,210,255,0.14);
}
.btn.case:hover {
  border-color: #e0b52e;
  color: var(--ac-ink);
  background: rgba(247, 205, 103, 0.2);
}
.btn.solid.flow {
  background: linear-gradient(135deg, var(--app-green-deep), var(--app-blue));
  color: #fff;
  border: 2px solid var(--app-green-deep);
  border-style: solid;
}
.btn.solid.case {
  background: rgba(255,214,165,0.72);
  color: var(--ac-ink);
  border: 2px solid #e0b52e;
  border-style: solid;
}
.filters { display: flex; gap: 8px; margin-bottom: 14px; }
.chip {
  padding: 5px 12px;
  border-radius: 999px;
  border: 1.5px solid var(--ac-border);
  background: #fff;
  font-size: 11px;
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  color: var(--ac-ink-muted);
}
.chip.on {
  background: rgba(162,210,255,0.18);
  border-color: rgba(162,210,255,0.55);
  color: var(--app-green-deep);
}
.empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  color: var(--ac-ink-muted);
  font-weight: 700;
}
.empty-ico { font-size: 40px; margin-bottom: 8px; }
.empty-tip {
  max-width: 360px;
  font-size: 12px;
  color: var(--ac-ink-faint);
  font-weight: 600;
  line-height: 1.5;
  margin: 8px 0 16px;
}
.empty-btns { display: flex; gap: 10px; }
.section { margin-bottom: 20px; }
.section-title {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border: 1px solid var(--doodle-ink, #2d2d2d);
  border-radius: 12px;
  background: #fff;
  font-family: inherit;
  font-size: 13px;
  font-weight: 800;
  color: var(--ac-ink);
  cursor: pointer;
  text-align: left;
}
.section-title.static { cursor: default; }
.section-title:not(.static):hover { border-color: var(--ac-teal); }
.chev { width: 14px; color: var(--app-text-secondary); }
.sec-ico { font-size: 15px; }
.sec-name { flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.sec-count {
  font-size: 11px;
  font-weight: 800;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(162,210,255,0.14);
  color: var(--ac-ink-muted);
}
.enter {
  font-size: 11px;
  color: var(--app-green-deep);
  padding: 2px 8px;
  border-radius: 8px;
}
.enter:hover { background: rgba(162,210,255,0.16); }
.section-body { padding: 14px 2px 0 8px; }
.sec-empty {
  padding: 12px 14px;
  font-size: 12px;
  font-weight: 700;
  color: var(--ac-ink-faint);
  display: flex;
  gap: 10px;
  align-items: center;
}
.linkish {
  border: none;
  background: transparent;
  color: var(--app-green-deep);
  font-weight: 800;
  font-family: inherit;
  cursor: pointer;
  font-size: 12px;
}
/* 本目录文件：标题与卡片之间留白（对齐子目录 section-body） */
.section > .file-grid {
  margin-top: 14px;
  padding-left: 8px;
}
.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}
.file-card {
  text-align: left;
  padding: 14px;
  border: 2px solid var(--ac-border);
  border-radius: 16px;
  background: #fff;
  cursor: pointer;
  font-family: inherit;
  box-shadow: var(--app-shadow-sm);
  transition: transform 0.12s ease, border-color 0.12s ease;
}
.file-card:hover {
  transform: translateY(-2px);
  border-color: var(--ac-teal);
}
.file-card.page_flow { border-left: 5px solid var(--app-green-deep); }
.file-card.test_case { border-left: 5px solid #ffd6a5; }
.file-top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.file-ico { font-size: 18px; }
.file-type {
  font-size: 10px;
  font-weight: 800;
  color: var(--ac-ink-faint);
}
.file-ops {
  margin-left: auto;
  display: flex;
  opacity: 0;
}
.file-card:hover .file-ops { opacity: 1; }
.file-ops button {
  border: none;
  background: transparent;
  cursor: pointer;
  color: var(--app-text-secondary);
  padding: 2px 5px;
  border-radius: 6px;
}
.file-ops button:hover { background: rgba(162,210,255,0.14); }
.file-ops button.danger:hover { color: #e85f5f; }
.file-name {
  font-size: 14px;
  font-weight: 800;
  color: var(--ac-ink);
  margin-bottom: 4px;
  word-break: break-word;
}
.file-id {
  font-size: 9px;
  font-weight: 700;
  color: var(--app-green-deep);
  margin-bottom: 6px;
  word-break: break-all;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  line-height: 1.3;
}
.file-meta {
  font-size: 10px;
  font-weight: 600;
  color: var(--ac-ink-faint);
}
.file-cta {
  margin-top: 10px;
  font-size: 11px;
  font-weight: 800;
  color: var(--app-green-deep);
}
.rename-inp {
  width: 100%;
  margin-bottom: 6px;
  padding: 4px 8px;
  border: 2px solid var(--app-green-deep);
  border-radius: 8px;
  font-size: 13px;
  font-weight: 800;
  font-family: inherit;
}
</style>
