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

const tabList = [
  { key: "ui", caseType: "ui_automation", component: UiCaseList },
  { key: "web", caseType: "web_automation", component: WebCaseList },
  { key: "storage", caseType: "storage", component: StorageCaseList },
  { key: "api", caseType: "api_testing", component: ApiCaseList },
];
const activeTabConfig = computed(() => tabList.find(t => t.key === activeTab.value) || tabList[0]);

// ── Per-tab directory trees (independent per module) ──
const treeCache = ref({ ui: [], web: [], storage: [], api: [] });
const activeDirectoryId = ref(null);
const activeDirName = ref("");

const currentTree = computed(() => treeCache.value[activeTab.value] || []);

async function loadTree() {
  try {
    const { data } = await fetchDirectories(caseType.value);
    if (data.ok) treeCache.value[activeTab.value] = data.tree;
  } catch (e) { console.error(e); }
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
const caseLayoutEl = ref(null);
function setCaseLayoutRef(el) { caseLayoutEl.value = el; }

function onSidebarResizeStart(e) {
  if (e.button !== 0) return;
  e.preventDefault();
  isResizingSidebar.value = true;
  document.body.style.cursor = "col-resize";
  document.body.style.userSelect = "none";
}
function onSidebarResizeMove(e) {
  if (!isResizingSidebar.value || !caseLayoutEl.value) return;
  sidebarWidth.value = clampW(e.clientX - caseLayoutEl.value.getBoundingClientRect().left);
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
      icon-gradient="linear-gradient(135deg,var(--c-workflow),#60a5fa)"
    />

    <AppTabs
      :items="tabs"
      :model-value="activeTab"
      @update:model-value="onTabChange"
      :leaf-animation="true"
      :shadow="true"
      class="case-tabs"
    >
      <template v-for="tab in tabList" :key="tab.key" #[tab.key]>
        <div :ref="setCaseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
          <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
            <DirectoryTree
              :tree-data="currentTree"
              :active-id="activeDirectoryId"
              :case-type="tab.caseType"
              @select="handleDirSelect"
              @refresh="handleTreeRefresh"
            />
          </aside>
          <div class="case-sidebar-resizer" :class="{ 'is-dragging': isResizingSidebar }"
            title="拖动调整宽度，双击恢复默认"
            @mousedown="onSidebarResizeStart" @dblclick="resetSidebarWidth" />
          <main class="case-main">
            <component :is="tab.component"
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
/* Doodle Craft — 用例列表 */
.case-tabs{flex:1;display:flex;flex-direction:column;min-height:0}
.case-tabs :deep(.el-tabs__header){margin:0 0 12px;width:100%}
.case-tabs :deep(.el-tabs__nav-wrap),.case-tabs :deep(.el-tabs__nav-scroll){width:100%}
.case-tabs :deep(.el-tabs__nav){display:flex;width:100%;border:none!important;gap:4px}
.case-tabs :deep(.el-tabs__item){flex:1;justify-content:center;text-align:center;height:38px;padding:0 10px;font-size:var(--app-size-xs);font-weight:700;border-radius:4px 8px 4px 8px;border:2px solid transparent;color:#999;line-height:1.4;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.case-tabs :deep(.el-tabs__item:hover){color:var(--ink)}
.case-tabs :deep(.el-tabs__item.is-active){color:var(--ink);background:#fff;border-color:var(--ink)}
.case-tabs :deep(.el-tabs__active-bar){display:none}
.case-tabs :deep(.el-tabs__content){flex:1;min-height:0}
.case-tabs :deep(.el-tab-pane){height:100%}
.case-layout{display:flex;flex-direction:row;height:100%;overflow:hidden;gap:0;padding:0;max-width:none}
.case-layout--resizing{pointer-events:none}
.case-sidebar{flex-shrink:0;overflow-y:auto;padding:8px 8px 8px 0;border-right:2px solid var(--ink)}
.case-sidebar-resizer{width:4px;cursor:col-resize;background:transparent;transition:background 0.2s;flex-shrink:0}
.case-sidebar-resizer:hover,.case-sidebar-resizer.is-dragging{background:var(--c-case)}
.case-main{flex:1;overflow-y:auto;padding:0 0 0 14px;min-width:0}
</style>
