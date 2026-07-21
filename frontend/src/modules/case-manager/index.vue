<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import DirectoryTree from "./components/DirectoryTree.vue";
import UiCaseList from "./components/ui/UiCaseList.vue";
import StorageCaseList from "./components/storage/StorageCaseList.vue";
import ApiCaseList from "./components/api/ApiCaseList.vue";
import WebCaseList from "./components/web/WebCaseList.vue";
import { fetchDirectories } from "./api/directories.js";

// ── TAB state ──
const TAB_STORAGE_KEY = "case-manager-active-tab";
const activeTab = ref(localStorage.getItem(TAB_STORAGE_KEY) || "ui");
const tabs = [
  { key: "ui", label: "📱 Android UI 自动化用例" },
  { key: "web", label: "🌍 Web 自动化测试用例" },
  { key: "storage", label: "业务功能用例" },
  { key: "api", label: "🌐 API 接口用例" },
];

function onTabChange(key) {
  activeTab.value = key;
  localStorage.setItem(TAB_STORAGE_KEY, key);
  activeDirectoryId.value = null;
  activeDirName.value = "";
  // Load tree for this tab if it hasn't been loaded yet
  if (!treeCache.value[key] || !treeCache.value[key].length) {
    loadTree();
  }
}

const caseType = computed(() => {
  const map = { ui: "ui_automation", web: "web_automation", storage: "storage", api: "api_testing" };
  return map[activeTab.value] || "ui_automation";
});

// ── Per-tab directory trees (independent per module) ──
const treeCache = ref({ ui: [], web: [], storage: [], api: [] });
const activeDirectoryId = ref(null);
const activeDirName = ref("");

const currentTree = computed(() => treeCache.value[activeTab.value] || []);

async function loadTree() {
  try {
    const { data } = await fetchDirectories(caseType.value);
    if (data.ok) treeCache.value[activeTab.value] = data.tree;
  } catch (_) {}
}

function handleDirSelect(node) {
  if (node.node_type === "directory") {
    activeDirectoryId.value = node.id;
    activeDirName.value = node.name;
  }
}

function handleTreeRefresh() {
  loadTree();
}

// ── Sidebar resize ──
const SIDEBAR_WIDTH_KEY = "case-manager-sidebar-width";
const SIDEBAR_MIN = 220;
const SIDEBAR_MAX = 560;
const SIDEBAR_DEFAULT = 300;
function clampW(w) { return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, w)); }
const sidebarWidth = ref(clampW(Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) || SIDEBAR_DEFAULT));
const isResizingSidebar = ref(false);
const caseLayoutRef = ref(null);

function onSidebarResizeStart(e) {
  if (e.button !== 0) return;
  e.preventDefault();
  isResizingSidebar.value = true;
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";
}
function onSidebarResizeMove(e) {
  if (!isResizingSidebar.value || !caseLayoutRef.value) return;
  sidebarWidth.value = clampW(e.clientX - caseLayoutRef.value.getBoundingClientRect().left);
}
function onSidebarResizeEnd() {
  if (!isResizingSidebar.value) return;
  isResizingSidebar.value = false;
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth.value));
}
function resetSidebarWidth() {
  sidebarWidth.value = SIDEBAR_DEFAULT;
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(SIDEBAR_DEFAULT));
}

// ── Lifecycle ──
onMounted(() => {
  window.addEventListener("mousemove", onSidebarResizeMove);
  window.addEventListener("mouseup", onSidebarResizeEnd);
  loadTree();
});
onUnmounted(() => {
  window.removeEventListener("mousemove", onSidebarResizeMove);
  window.removeEventListener("mouseup", onSidebarResizeEnd);
  document.body.style.cursor = "";
  document.body.style.userSelect = "";
});
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="测试用例"
      subtitle="按类型管理测试用例：UI 自动化 · 存储业务功能 · API 接口"
      icon="layers"
      icon-gradient="linear-gradient(135deg,#89CFF0,#60a5fa)"
    />

    <AppTabs
      :items="tabs"
      :model-value="activeTab"
      @update:model-value="onTabChange"
      :leaf-animation="true"
      :shadow="true"
      class="case-tabs"
    >
      <template #ui>
        <div ref="caseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
          <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
            <DirectoryTree
              :tree-data="currentTree"
              :active-id="activeDirectoryId"
              case-type="ui_automation"
              @select="handleDirSelect"
              @refresh="handleTreeRefresh"
            />
          </aside>
          <div class="case-sidebar-resizer" :class="{ 'is-dragging': isResizingSidebar }"
            title="拖动调整宽度，双击恢复默认"
            @mousedown="onSidebarResizeStart" @dblclick="resetSidebarWidth" />
          <main class="case-main">
            <UiCaseList
              :tree-data="currentTree"
              :active-directory-id="activeDirectoryId"
              :active-dir-name="activeDirName"
              @refresh-tree="handleTreeRefresh"
            />
          </main>
        </div>
      </template>

      <template #web>
        <div ref="caseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
          <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
            <DirectoryTree
              :tree-data="currentTree"
              :active-id="activeDirectoryId"
              case-type="web_automation"
              @select="handleDirSelect"
              @refresh="handleTreeRefresh"
            />
          </aside>
          <div class="case-sidebar-resizer" :class="{ 'is-dragging': isResizingSidebar }"
            title="拖动调整宽度，双击恢复默认"
            @mousedown="onSidebarResizeStart" @dblclick="resetSidebarWidth" />
          <main class="case-main">
            <WebCaseList
              :tree-data="currentTree"
              :active-directory-id="activeDirectoryId"
              :active-dir-name="activeDirName"
              @refresh-tree="handleTreeRefresh"
            />
          </main>
        </div>
      </template>

      <template #storage>
        <div ref="caseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
          <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
            <DirectoryTree
              :tree-data="currentTree"
              :active-id="activeDirectoryId"
              case-type="storage"
              @select="handleDirSelect"
              @refresh="handleTreeRefresh"
            />
          </aside>
          <div class="case-sidebar-resizer" :class="{ 'is-dragging': isResizingSidebar }"
            title="拖动调整宽度，双击恢复默认"
            @mousedown="onSidebarResizeStart" @dblclick="resetSidebarWidth" />
          <main class="case-main">
            <StorageCaseList
              :tree-data="currentTree"
              :active-directory-id="activeDirectoryId"
              :active-dir-name="activeDirName"
              @refresh-tree="handleTreeRefresh"
            />
          </main>
        </div>
      </template>

      <template #api>
        <div ref="caseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
          <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
            <DirectoryTree
              :tree-data="currentTree"
              :active-id="activeDirectoryId"
              case-type="api_testing"
              @select="handleDirSelect"
              @refresh="handleTreeRefresh"
            />
          </aside>
          <div class="case-sidebar-resizer" :class="{ 'is-dragging': isResizingSidebar }"
            title="拖动调整宽度，双击恢复默认"
            @mousedown="onSidebarResizeStart" @dblclick="resetSidebarWidth" />
          <main class="case-main">
            <ApiCaseList
              :tree-data="currentTree"
              :active-directory-id="activeDirectoryId"
              :active-dir-name="activeDirName"
              @refresh-tree="handleTreeRefresh"
            />
          </main>
        </div>
      </template>
    </AppTabs>
  </div>
</template>

<style scoped>
.case-tabs {
  margin-top: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.case-tabs :deep(.el-tabs__header) {
  margin: 0 0 8px;
  width: 100%;
}
.case-tabs :deep(.el-tabs__nav-wrap),
.case-tabs :deep(.el-tabs__nav-scroll) {
  width: 100%;
}
.case-tabs :deep(.el-tabs__nav) {
  display: flex;
  width: 100%;
  box-sizing: border-box;
  border-radius: var(--app-radius-md);
}
.case-tabs :deep(.el-tabs__item) {
  flex: 1;
  width: auto;
  max-width: none;
  justify-content: center;
  text-align: center;
  height: 40px;
  padding: 0 8px;
  border-radius: var(--app-radius-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.case-tabs :deep(.el-tabs__content) {
  flex: 1;
  min-height: 0;
}
.case-tabs :deep(.el-tab-pane) {
  height: 100%;
}
.case-layout {
  display: flex;
  flex-direction: row;
  height: 100%;
  overflow: hidden;
  gap: 0;
  padding: 0;
  max-width: none;
}
.case-layout--resizing {
  pointer-events: none;
}
.case-sidebar {
  flex-shrink: 0;
  overflow-y: auto;
  padding: 8px 8px 8px 0;
  border-right: 1px solid #eee;
}
.case-sidebar-resizer {
  width: 4px;
  cursor: col-resize;
  background: transparent;
  transition: background 0.2s;
  flex-shrink: 0;
}
.case-sidebar-resizer:hover,
.case-sidebar-resizer.is-dragging {
  background: var(--animal-primary-color, #89CFF0);
}
.case-main {
  flex: 1;
  overflow-y: auto;
  padding: 0 0 0 16px;
  min-width: 0;
}
</style>
