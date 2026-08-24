<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import DirectoryTree from "./components/DirectoryTree.vue";
import UiCaseList from "./components/ui/UiCaseList.vue";
import StorageCaseList from "./components/storage/StorageCaseList.vue";
import ApiCaseList from "./components/api/ApiCaseList.vue";
import WebCaseList from "./components/web/WebCaseList.vue";
import { fetchDirectories } from "./api/directories";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";

const route = useRoute();

// ── TAB state（侧边栏子项路由驱动，/cases/ui|web|storage|api）──
const TAB_BY_PATH = {
  "/cases/ui": "ui",
  "/cases/web": "web",
  "/cases/storage": "storage",
  "/cases/api": "api",
};
const activeTab = computed(() => TAB_BY_PATH[route.path] || "ui");
const error = ref("");

function onTabChange(key) {
  activeDirectoryId.value = null;
  activeDirName.value = "";
  activeCaseId.value = null;
  // Load tree for this tab if it hasn't been loaded yet
  if (!treeCache.value[key] || !treeCache.value[key].length) {
    loadTree();
  }
}

// 路由切换子项时执行与旧 Tab 切换相同的重置/懒加载逻辑
watch(activeTab, (key, prevKey) => {
  if (key !== prevKey) onTabChange(key);
});

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

// ── 顶部 WorkbenchHeader 随侧边栏子项变化 ──
const pageMeta = computed(() => {
  const map = {
    ui: {
      title: "Android UI 自动化用例 Android UI Automation",
      subtitle: "管理 Android UI 自动化用例：定义基本信息、编排执行步骤，从元素库选取 XPath",
    },
    web: {
      title: "Web 自动化测试用例 Web Automation Cases",
      subtitle: "管理 Web 自动化测试用例：页面跳转、元素点击、表单填充、文本验证、截图",
    },
    storage: {
      title: "业务功能用例 Business Function Cases",
      subtitle: "管理业务功能用例：维护前置条件、步骤与预期结果",
    },
    api: {
      title: "API 接口用例 API Testing Cases",
      subtitle: "管理 API 接口用例：定义接口请求、测试数据与校验规则",
    },
  };
  return map[activeTab.value] || map.ui;
});

// ── Per-tab directory trees (independent per module) ──
const treeCache = ref({ ui: [], web: [], storage: [], api: [] });
const activeDirectoryId = ref(null);
const activeDirName = ref("");
const activeCaseId = ref(null);

const currentTree = computed(() => treeCache.value[activeTab.value] || []);
const activeTreeId = computed(() =>
  activeCaseId.value != null ? `case:${activeCaseId.value}` : activeDirectoryId.value,
);

async function loadTree() {
  try {
    const { data } = await fetchDirectories(caseType.value);
    if (data.status) {
      treeCache.value[activeTab.value] = data.tree;
      error.value = "";
    } else {
      error.value = data.message || "加载目录失败";
    }
  } catch (e) {
    error.value = "加载目录失败，请检查网络连接";
    console.error(e);
  }
}

/** 在目录树中查找用例节点的父目录（孤儿用例返回 null） */
function findParentDirectory(nodes, caseNodeId, parentDir = null) {
  for (const node of nodes) {
    if (String(node.id) === String(caseNodeId)) return parentDir;
    if (node.children?.length) {
      const nextParent = node.node_type === "directory" ? node : parentDir;
      const found = findParentDirectory(node.children, caseNodeId, nextParent);
      if (found !== undefined) return found;
    }
  }
  return undefined;
}

function handleDirSelect(node) {
  if (node.node_type === "case") {
    activeCaseId.value = node.case_id;
    const parentDir = findParentDirectory(currentTree.value, node.id);
    if (parentDir) {
      activeDirectoryId.value = parentDir.id;
      activeDirName.value = parentDir.name;
    } else {
      activeDirectoryId.value = null;
      activeDirName.value = "";
    }
    return;
  }
  if (node.node_type === "directory") {
    activeDirectoryId.value = node.id;
    activeDirName.value = node.name;
    activeCaseId.value = null;
  }
}

function handleClearCase() {
  activeCaseId.value = null;
}

function handleSelectCase(id) {
  activeCaseId.value = id;
}

function handleGoAll() {
  activeCaseId.value = null;
  activeDirectoryId.value = null;
  activeDirName.value = "";
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
      :title="pageMeta.title"
      :subtitle="pageMeta.subtitle"
      icon="layers"
      icon-gradient="linear-gradient(135deg,var(--c-workflow),#60a5fa)"
    />

    <div :ref="setCaseLayoutRef" class="doc-body case-layout" :class="{ 'case-layout--resizing': isResizingSidebar }">
      <aside class="case-sidebar" :style="{ width: sidebarWidth + 'px' }">
        <ErrorState v-if="error" :message="error" @retry="loadTree" />
        <DirectoryTree
          v-else
          :tree-data="currentTree"
          :active-id="activeTreeId"
          :case-type="activeTabConfig.caseType"
          @select="handleDirSelect"
          @refresh="handleTreeRefresh"
        />
      </aside>
      <div class="case-sidebar-resizer" :class="{ 'is-dragging': isResizingSidebar }"
        title="拖动调整宽度，双击恢复默认"
        @mousedown="onSidebarResizeStart" @dblclick="resetSidebarWidth" />
      <main class="case-main">
        <component :is="activeTabConfig.component"
          :tree-data="currentTree"
          :active-directory-id="activeDirectoryId"
          :active-dir-name="activeDirName"
          :active-case-id="activeCaseId"
          @refresh-tree="handleTreeRefresh"
          @clear-case="handleClearCase"
          @select-case="handleSelectCase"
          @go-all="handleGoAll"
        />
      </main>
    </div>
  </div>
</template>

<style scoped>
/* Doodle Craft — 用例列表 */
.case-layout{display:flex;flex-direction:row;height:100%;overflow:hidden;gap:0;padding:0;max-width:none}
.case-layout--resizing{pointer-events:none}
.case-sidebar{flex-shrink:0;overflow-y:auto;padding:8px 8px 8px 0;border-right:2px solid var(--ink)}
.case-sidebar-resizer{width:4px;cursor:col-resize;background:transparent;transition:background var(--app-duration-slow);flex-shrink:0}
.case-sidebar-resizer:hover,.case-sidebar-resizer.is-dragging{background:var(--c-case)}
.case-main{flex:1;overflow-y:auto;padding:0 0 0 14px;min-width:0}
</style>
