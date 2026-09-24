<script setup lang="ts">
import { ref, watch, onMounted } from "vue"
import { ElMessageBox } from "element-plus"
import type { CatalogPage } from "@/modules/workflow/data/pageCatalog"
import { fetchCatalogPages } from "@/modules/workflow/data/pageCatalog"
import { NODE_MENU_SIZE } from "@/modules/workflow/helpers/overlayPosition"
import { useContainedOverlay } from "@/modules/workflow/composables/useContainedOverlay"

const props = defineProps<{
  show: boolean
  x: number
  y: number
  nodeId: string
  nodeLabel: string
  canLinkPage?: boolean
  linkedPageId?: string
  linkedPageName?: string
}>()

const emit = defineEmits<{
  close: []
  linkPage: [page: CatalogPage]
  resyncPage: []
  deleteNode: []
}>()

const mode = ref<"menu" | "link">("menu")
const pages = ref<CatalogPage[]>([])
const catalogError = ref("")
const loading = ref(false)
const search = ref("")
const source = ref<string>("")
/** 浮层根元素 + 已收敛到屏内的位置（光标锚点越界时向屏内平移） */
const { el: menuRef, position, place } = useContainedOverlay(NODE_MENU_SIZE)

function reposition() {
  if (!props.show) return
  void place({ x: props.x, y: props.y })
}

watch(() => [props.show, props.x, props.y] as const, reposition, { immediate: true })
// 切到「选择 Android 页面」后浮层更高，需要按新尺寸再收敛一次
watch(mode, reposition)

async function loadPages() {
  loading.value = true
  catalogError.value = ""
  try {
    const res = await fetchCatalogPages()
    pages.value = res.pages
    source.value = res.source
    if (res.message) catalogError.value = res.message
  } finally {
    loading.value = false
  }
}

watch(
  () => props.show,
  (v) => {
    if (v) {
      mode.value = "menu"
      search.value = ""
      setTimeout(() => document.addEventListener("click", onOutside), 0)
    } else {
      document.removeEventListener("click", onOutside)
    }
  },
)

function onOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    emit("close")
  }
}

async function openLink() {
  mode.value = "link"
  search.value = ""
  await loadPages()
  // 列表渲染后浮层更高：按新尺寸再收敛一次，避免底部超出视口
  reposition()
}

function selectPage(page: CatalogPage) {
  emit("linkPage", page)
  emit("close")
}

async function doDelete() {
  try {
    await ElMessageBox.confirm(
      `确定删除节点「${props.nodeLabel}」？相关连线也会删除。`,
      "删除确认",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      },
    )
  } catch {
    // 用户取消删除：ElMessageBox 以 reject 表示取消，不触发删除（非静默吞错）
    return
  }
  emit("deleteNode")
  emit("close")
}

function doResync() {
  emit("resyncPage")
  emit("close")
}

const filtered = () => {
  const q = search.value.trim().toLowerCase()
  if (!q) return pages.value
  return pages.value.filter(
    (p) => p.name.toLowerCase().includes(q) || (p.description || "").toLowerCase().includes(q),
  )
}

onMounted(() => {
  if (props.show) loadPages()
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="show"
      ref="menuRef"
      class="node-menu"
      :style="{ left: position.x + 'px', top: position.y + 'px' }"
      @click.stop
    >
      <!-- Root menu -->
      <template v-if="mode === 'menu'">
        <div class="menu-title">{{ nodeLabel }}</div>
        <div v-if="linkedPageName" class="menu-hint">已关联: {{ linkedPageName }}</div>

        <button v-if="canLinkPage !== false" class="menu-item" @click="openLink">
          <span>📱</span> 关联 Android 页面…
        </button>

        <button v-if="linkedPageId" class="menu-item" @click="doResync">
          <span>🔄</span> 刷新元素目录
        </button>
        <button class="menu-item danger" @click="doDelete"><span>🗑</span> 删除节点</button>
      </template>

      <!-- Link page picker -->
      <template v-else>
        <div class="menu-header">
          <button class="back" @click="mode = 'menu'">←</button>
          <span>选择 Android 页面</span>
        </div>
        <input
          v-model="search"
          class="search"
          placeholder="搜索页面…"
          autofocus
          @keydown.escape="$emit('close')"
        />
        <div v-if="catalogError" class="empty">API 提示: {{ catalogError }}</div>
        <div v-if="loading" class="empty">加载中…</div>
        <div v-else class="list">
          <button
            v-for="p in filtered()"
            :key="p.id"
            class="page-item"
            :class="{ active: p.id === linkedPageId }"
            @click="selectPage(p)"
          >
            <div class="page-name">
              {{ p.name }}<span v-if="p.id === linkedPageId" class="badge">当前</span>
            </div>
            <div class="page-meta">
              {{ p.elements.length }} 个元素 · {{ p.description || p.package || "—" }}
            </div>
          </button>
          <div v-if="!filtered().length" class="empty">无匹配页面</div>
        </div>
      </template>
    </div>
  </Teleport>
</template>

<style scoped>
.node-menu {
  position: fixed;
  z-index: var(--z-popup);
  width: 288px;
  /* 视口兜底：窗口比浮层还矮时按视口收敛（脚本未执行的首帧也不会超出屏幕） */
  max-height: min(420px, calc(100vh - 16px));
  max-height: min(420px, calc(100dvh - 16px));
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: var(--app-bg-card);
  border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md);
  box-shadow: var(--app-shadow-lg);
  padding: var(--app-space-sm);
  font-family: var(--app-font);
  /* 本模块私有色：tokens.css 未登记，登记在菜单自身根类（Teleport 到 body 后变量仍可达） */
  --wf-nodemenu-hover-bg: var(--color-cyan-74-a18) /* -> --color-cyan-74-a18 */; /* 菜单项/页项悬停底（工作流蓝 16%） */
  --wf-nodemenu-hint: var(--color-cyan-40) /* -> --color-cyan-40 */; /* 已关联提示文字与「当前」徽章底（深蓝） */
}
.menu-title {
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  padding: 6px var(--app-space-sm) 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.menu-hint {
  font-size: var(--app-size-xs);
  color: var(--wf-nodemenu-hint);
  font-weight: 700;
  padding: 0 var(--app-space-sm) var(--app-space-sm);
}
.menu-item {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  width: 100%;
  padding: 9px 12px;
  border: none;
  border-radius: var(--app-radius-md);
  background: transparent;
  color: var(--ink);
  font-size: var(--app-size-sm);
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: background var(--app-duration-fast) var(--app-ease);
}
.menu-item:hover {
  background: var(--wf-nodemenu-hover-bg);
}
.menu-item.danger {
  color: var(--app-status-danger-text);
}
.menu-item.danger:hover {
  background: var(--app-status-danger-bg);
  color: var(--app-status-danger-text);
}
.menu-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: var(--app-space-xs) 6px var(--app-space-sm);
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
}
.back {
  border: 2px solid var(--ink);
  background: var(--app-bg-card);
  color: var(--ink);
  border-radius: var(--app-radius-md);
  width: 28px;
  height: 28px;
  cursor: pointer;
  font-weight: 700;
}
.back:hover {
  background: var(--wf-nodemenu-hover-bg);
}
.search {
  margin: 0 var(--app-space-xs) 6px;
  padding: var(--app-space-sm) 10px;
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  color: var(--ink);
  font-size: var(--app-size-sm);
  outline: none;
  font-family: inherit;
}
.search:focus {
  border-color: var(--c-workflow);
}
.list {
  /* 高度交给外层 max-height：收敛后条目区自行滚动，条目不会被裁掉 */
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
}
.page-item {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: none;
  border-radius: var(--app-radius-md);
  background: transparent;
  color: var(--ink);
  cursor: pointer;
  font-family: inherit;
}
.page-item:hover {
  background: var(--wf-nodemenu-hover-bg);
}
.page-item.active {
  background: var(--wf-nodemenu-hover-bg);
}
.page-name {
  font-size: var(--app-size-sm);
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 6px;
}
.badge {
  font-size: var(--app-size-xs);
  color: var(--app-text-inverse);
  background: var(--wf-nodemenu-hint);
  border-radius: var(--app-radius-sm);
  padding: 1px 6px;
  font-weight: 700;
}
.page-meta {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  margin-top: 3px;
  font-weight: 600;
}
.empty {
  padding: 18px;
  text-align: center;
  font-size: var(--app-size-sm);
  color: var(--app-text-secondary);
}
</style>
