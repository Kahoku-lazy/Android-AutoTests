/**
 * useSidebarResize — 侧边栏宽度拖拽缩放 + 折叠状态
 * Extracted from AppSidebar.vue
 */
import { ref } from 'vue';

const SIDEBAR_WIDTH_KEY = 'app-sidebar-width';
const SIDEBAR_COLLAPSED_KEY = 'app-sidebar-collapsed';
const SIDEBAR_MIN = 180;
const SIDEBAR_MAX = 360;
const SIDEBAR_DEFAULT = 260;
const SIDEBAR_COLLAPSED_W = 64;

export function useSidebarResize() {
  const sidebarWidth = ref(SIDEBAR_DEFAULT);
  const isResizing = ref(false);
  const collapsed = ref(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1');

  function clampSidebarWidth(width) {
    return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, width));
  }

  function applySidebarWidth(width) {
    if (collapsed.value) {
      document.documentElement.style.setProperty('--side-w', `${SIDEBAR_COLLAPSED_W}px`);
      return;
    }
    const w = clampSidebarWidth(width);
    sidebarWidth.value = w;
    document.documentElement.style.setProperty('--side-w', `${w}px`);
  }

  function toggleCollapsed() {
    collapsed.value = !collapsed.value;
    localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed.value ? '1' : '0');
    applySidebarWidth(sidebarWidth.value);
  }

  function onSidebarResizeStart(e) {
    if (e.button !== 0 || collapsed.value) return;
    e.preventDefault();
    isResizing.value = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }

  function onSidebarResizeMove(e) {
    if (!isResizing.value) return;
    applySidebarWidth(e.clientX);
  }

  function onSidebarResizeEnd() {
    if (!isResizing.value) return;
    isResizing.value = false;
    document.body.style.cursor = '';
    document.body.style.userSelect = '';
    localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth.value));
  }

  function resetSidebarWidth() {
    applySidebarWidth(SIDEBAR_DEFAULT);
    localStorage.setItem(SIDEBAR_WIDTH_KEY, String(SIDEBAR_DEFAULT));
  }

  function initSidebarWidth() {
    applySidebarWidth(Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) || SIDEBAR_DEFAULT);
  }

  return {
    sidebarWidth, isResizing, collapsed,
    applySidebarWidth, toggleCollapsed,
    onSidebarResizeStart, onSidebarResizeMove, onSidebarResizeEnd,
    resetSidebarWidth, initSidebarWidth,
  };
}
