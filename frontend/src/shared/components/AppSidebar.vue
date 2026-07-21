<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { animate } from 'animejs'
import { sidebarNavEnter } from '../animations.js'
import AnimatedMascot from './AnimatedMascot.vue'
import AnimatedMenuIcon from './AnimatedMenuIcon.vue'

const router = useRouter()
const route = useRoute()

// ── Multi-account auth ──
const POOL_KEY = 'auth_accounts'
const ACTIVE_KEY = 'auth_active'

function readPool() {
  try { return JSON.parse(localStorage.getItem(POOL_KEY) || '{}') } catch { return {} }
}
function getActive() {
  return sessionStorage.getItem(ACTIVE_KEY) || Object.keys(readPool())[0] || ''
}

const username = ref(getActive())
const allAccounts = ref(Object.keys(readPool()))
const showAccountMenu = ref(false)

function refreshAccountState() {
  username.value = getActive()
  allAccounts.value = Object.keys(readPool())
}

// Listen for pool changes from other tabs (new accounts added/removed)
function onStorageChange(e) {
  if (e.key === POOL_KEY) refreshAccountState()
}

function switchToAccount(name) {
  if (readPool()[name]) {
    sessionStorage.setItem(ACTIVE_KEY, name)
    showAccountMenu.value = false
    window.location.reload()
  }
}

function logout() {
  const active = getActive()
  if (active) {
    const pool = readPool()
    delete pool[active]
    localStorage.setItem(POOL_KEY, JSON.stringify(pool))
    const remaining = Object.keys(pool)
    if (remaining.length > 0) {
      sessionStorage.setItem(ACTIVE_KEY, remaining[0])
      window.location.reload()
    } else {
      localStorage.removeItem(POOL_KEY)
      sessionStorage.removeItem(ACTIVE_KEY)
      router.push('/login')
    }
  }
}

const SIDEBAR_WIDTH_KEY = 'app-sidebar-width'
const SIDEBAR_COLLAPSED_KEY = 'app-sidebar-collapsed'
const SIDEBAR_MIN = 180
const SIDEBAR_MAX = 360
const SIDEBAR_DEFAULT = 260
const SIDEBAR_COLLAPSED_W = 64

function clampSidebarWidth(width) {
  return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, width))
}

const sidebarWidth = ref(SIDEBAR_DEFAULT)
const isResizing = ref(false)
const collapsed = ref(localStorage.getItem(SIDEBAR_COLLAPSED_KEY) === '1')

function applySidebarWidth(width) {
  if (collapsed.value) {
    document.documentElement.style.setProperty('--side-w', `${SIDEBAR_COLLAPSED_W}px`)
    return
  }
  const w = clampSidebarWidth(width)
  sidebarWidth.value = w
  document.documentElement.style.setProperty('--side-w', `${w}px`)
}

function toggleCollapsed() {
  collapsed.value = !collapsed.value
  localStorage.setItem(SIDEBAR_COLLAPSED_KEY, collapsed.value ? '1' : '0')
  applySidebarWidth(sidebarWidth.value)
}

function onSidebarResizeStart(e) {
  if (e.button !== 0 || collapsed.value) return
  e.preventDefault()
  isResizing.value = true
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onSidebarResizeMove(e) {
  if (!isResizing.value) return
  applySidebarWidth(e.clientX)
}

function onSidebarResizeEnd() {
  if (!isResizing.value) return
  isResizing.value = false
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(sidebarWidth.value))
}

function resetSidebarWidth() {
  applySidebarWidth(SIDEBAR_DEFAULT)
  localStorage.setItem(SIDEBAR_WIDTH_KEY, String(SIDEBAR_DEFAULT))
}

// ── 导航分组（V6 原型结构）──
const expandedSections = ref({})

function toggleSection(key) {
  expandedSections.value[key] = !expandedSections.value[key]
}

// ── 导航分组（对齐 PRD §5 八模块体系）──
// 平台 8 大模块：仪表盘 / 设备管理 / 元素定位 / 用例管理 / 执行引擎 / 测试报告 / AI 助手 / 工作流工作台
// 三条操作通道：A.手动测试流程  B.AI 对话  C.可视化编排
const categories = [
  {
    key: 'main',
    label: '',
    items: [
      { path: '/dashboard', icon: 'layout-dashboard', label: '仪表盘' },
    ],
  },
  {
    key: 'test-flow',
    label: '测试全流程',
    items: [
      { path: '/devices', icon: 'smartphone', label: '设备管理' },
      { path: '/elements', icon: 'crosshair', label: '元素定位' },
      { path: '/cases', icon: 'layers', label: '用例管理' },
      { path: '/runner', icon: 'play-circle', label: '执行引擎' },
      { path: '/reports', icon: 'file-bar-chart', label: '测试报告' },
    ],
  },
  {
    key: 'ai-tools',
    label: 'AI 与编排',
    items: [
      { path: '/ai-assistant', icon: 'bot', label: 'AI 助手', isDev: true },
      { path: '/workflow', icon: 'git-branch', label: '工作流工作台', isDev: true },
    ],
  },
]

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function onNavClick(path, ev) {
  router.push(path)
}

onMounted(async () => {
  applySidebarWidth(Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) || SIDEBAR_DEFAULT)
  window.addEventListener('mousemove', onSidebarResizeMove)
  window.addEventListener('mouseup', onSidebarResizeEnd)
  window.addEventListener('storage', onStorageChange)

  await nextTick()
  // Lucide icons render
  if (window.lucide) window.lucide.createIcons()
  // Default expand first visible section
  categories.forEach(c => { if (c.label) expandedSections.value[c.key] = true })
  sidebarNavEnter('.sidebar-menu__item')

  // Brand entrance
  animate('.sidebar__brand', {
    opacity: [0, 1],
    translateY: [-8, 0],
    scale: [0.96, 1],
    duration: 600,
    ease: 'outCubic',
  })
  // Admin shimmer
  animate('.sidebar__user-name', {
    opacity: [0.75, 1],
    translateY: [1, 0],
    duration: 1200,
    loop: true,
    direction: 'alternate',
    ease: 'easeInOutSine',
  })
  // Menu labels subtle scale breath
  animate('.sidebar-menu__label', {
    scale: [1, 1.02],
    duration: 1800,
    loop: true,
    direction: 'alternate',
    ease: 'easeInOutSine',
    delay: (el, i) => i * 100,
  })
})

onUnmounted(() => {
  window.removeEventListener('mousemove', onSidebarResizeMove)
  window.removeEventListener('mouseup', onSidebarResizeEnd)
  window.removeEventListener('storage', onStorageChange)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
})
</script>

<template>
  <aside
    class="sidebar"
    :class="{ 'sidebar--resizing': isResizing, 'sidebar--collapsed': collapsed }"
  >
    <!-- 头部品牌 + 折叠 -->
    <div class="sidebar__header-row">
      <div class="sidebar__header" @click="router.push('/dashboard')" :title="collapsed ? '自动化测试平台' : ''">
        <AnimatedMascot :size="26" />
        <div v-show="!collapsed" class="sidebar__brand">
          <span class="brand-title">自动化测试平台</span>
        </div>
      </div>
      <button
        type="button"
        class="sidebar__toggle"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click.stop="toggleCollapsed"
      >
        {{ collapsed ? '›' : '‹' }}
      </button>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar__nav">
      <div v-for="cat in categories" :key="cat.key" class="sidebar__group">
        <div
          v-if="cat.label && !collapsed"
          class="sidebar__group-title"
          :class="{ collapsed: !expandedSections[cat.key] }"
          @click="toggleSection(cat.key)"
        >
          {{ cat.label }}
          <span class="collapse-icon">▼</span>
        </div>
        <div
          class="nav-section-items"
          :class="{ collapsed: cat.label && !expandedSections[cat.key] }"
        >
          <div
            v-for="item in cat.items"
            :key="item.path"
            :class="['sidebar-menu__item', { active: isActive(item.path) }]"
            :title="collapsed ? item.label : ''"
            @click="onNavClick(item.path, $event)"
          >
            <i :data-lucide="item.icon" class="nav-lucide-icon"></i>
            <span v-show="!collapsed" class="sidebar-menu__label">{{ item.label }}</span>
            <span
              v-if="item.isDev && !collapsed"
              class="sidebar-menu__badge sidebar-menu__badge--dev"
            >开发中</span>
          </div>
        </div>
      </div>
    </nav>

    <!-- 底部用户区 / 账号切换器 -->
    <div class="sidebar__footer">
      <div class="sidebar__user-card">
        <div class="sidebar__user-label">Digital Human</div>
        <div class="sidebar__user-display" :class="{ 'has-menu': allAccounts.length > 1 }"
          :title="collapsed ? username : ''"
          @click="allAccounts.length > 1 ? (showAccountMenu = !showAccountMenu) : null">
          <AnimatedMascot :size="18" />
          <span v-show="!collapsed" class="sidebar__user-name">{{ username }}</span>
          <span v-if="!collapsed && allAccounts.length > 1" class="sidebar__user-arrow">▾</span>
        </div>
        <div v-show="!collapsed" class="sidebar__user-status">● 在线</div>
      </div>

      <!-- Account dropdown -->
      <div v-if="showAccountMenu && !collapsed" class="account-menu">
        <div
          v-for="name in allAccounts"
          :key="name"
          class="account-menu__item"
          :class="{ active: name === username }"
          @click="switchToAccount(name)"
        >
          <span>{{ name }}</span>
          <span v-if="name === username" class="account-menu__check">✓</span>
        </div>
        <div class="account-menu__divider"></div>
        <div class="account-menu__item account-menu__item--add" @click="showAccountMenu = false; router.push('/login?add=1')">
          添加账号
        </div>
      </div>

      <el-button
        v-show="!collapsed"
        type="text"
        size="small"
        danger
        class="logout-btn"
        @click.stop="logout"
      >
        退出
      </el-button>
      <button
        v-show="collapsed"
        type="button"
        class="sidebar__icon-logout"
        title="退出登录"
        @click.stop="logout"
      >
        ⎋
      </button>
    </div>

    <div
      v-if="!collapsed"
      class="sidebar__resizer"
      :class="{ 'is-dragging': isResizing }"
      title="拖动调整宽度，双击恢复默认"
      @mousedown="onSidebarResizeStart"
      @dblclick="resetSidebarWidth"
    />
  </aside>
</template>

<style scoped>
.sidebar {
  flex: 0 0 var(--side-w, 220px);
  width: var(--side-w, 220px);
  min-width: var(--side-w, 220px);
  max-width: var(--side-w, 220px);
  height: 100%;
  background: rgba(255,255,255,0.45);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 2;
  border-right: 1px solid var(--app-glass-border, rgba(255,255,255,0.68));
  box-shadow: 8px 0 32px rgba(31, 38, 135, 0.06);
  color: var(--app-text, #4a4e69);
  font-family: var(--app-font, Quicksand, 'Noto Sans SC', sans-serif);
  transition: width 0.2s ease, min-width 0.2s ease, max-width 0.2s ease, flex-basis 0.2s ease;
}

.sidebar--collapsed {
  flex: 0 0 64px;
  width: 64px;
  min-width: 64px;
  max-width: 64px;
}

.sidebar__header-row {
  display: flex;
  align-items: center;
  gap: 2px;
  padding-right: 6px;
  border-bottom: 1px solid rgba(255,255,255,0.52);
  flex-shrink: 0;
}
.sidebar__toggle {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  margin-top: 4px;
  border: 1.5px solid rgba(255,255,255,0.75);
  border-radius: 999px;
  background: rgba(255,255,255,0.58);
  color: var(--app-text, #4a4e69);
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  line-height: 1;
  display: grid;
  place-items: center;
}
.sidebar__toggle:hover {
  border-color: var(--app-blue, #a2d2ff);
  color: var(--app-green-deep, #6f9fd8);
}

.sidebar--collapsed .sidebar__header-row {
  flex-direction: column;
  padding: 8px 6px;
  gap: 6px;
}
.sidebar--collapsed .sidebar__header {
  justify-content: center;
  padding: 4px 0;
}
.sidebar--collapsed .sidebar-menu__item {
  justify-content: center;
  padding: 10px 8px;
}
.sidebar--collapsed .sidebar__footer {
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 6px;
}
.sidebar__icon-logout {
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #c44;
  padding: 4px;
  border-radius: 6px;
}
.sidebar__icon-logout:hover { background: rgba(232, 95, 95, 0.12); }

.sidebar--resizing {
  user-select: none;
}

.sidebar__resizer {
  position: absolute;
  top: 0;
  right: 0;
  width: 6px;
  height: 100%;
  cursor: col-resize;
  z-index: 10;
  transform: translateX(50%);
}

.sidebar__resizer::before {
  content: '';
  position: absolute;
  top: 12px;
  bottom: 12px;
  left: 50%;
  width: 2px;
  transform: translateX(-50%);
  border-radius: 2px;
  background: rgba(255,255,255,0.62);
  transition: background 0.15s ease, width 0.15s ease;
}

.sidebar__resizer:hover::before,
.sidebar__resizer.is-dragging::before {
  width: 3px;
  background: var(--app-blue, #a2d2ff);
}

.sidebar__resizer:hover,
.sidebar__resizer.is-dragging {
  background: rgba(162,210,255,0.12);
}

/* Header */
.sidebar__header {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
  padding: 16px 8px 12px 16px;
  border-bottom: none;
  font-weight: 700;
  letter-spacing: -0.3px;
  cursor: pointer;
  transition: color 0.15s ease;
}

.sidebar__brand {
  display: flex;
  align-items: center;
  min-width: 0;
  font-size: 15px;
  line-height: 1.2;
  letter-spacing: 0.02em;
}

.brand-title {
  display: inline-block;
  font-weight: 800;
  white-space: nowrap;
  background-image: linear-gradient(
    105deg,
    #89CFF0 0%,
    #C9B6F2 22%,
    #95D5B2 42%,
    #F4D35E 62%,
    #FFB5A7 82%,
    #89CFF0 100%
  );
  background-size: 240% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
  animation: brand-chroma-flow 7s ease-in-out infinite;
}

.sidebar__header:hover .brand-title {
  animation-duration: 3.5s;
  filter: saturate(1.15) brightness(1.05);
}

.sidebar__header:hover {
  color: var(--app-green-deep, #6f9fd8);
}

@keyframes brand-chroma-flow {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

@media (prefers-reduced-motion: reduce) {
  .brand-title {
    animation: none;
    background-position: 30% 50%;
  }
}

/* Nav */
.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: 16px 14px;
}

.sidebar__group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sidebar-menu__item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 12px;
  height: 46px;
  padding: 0 16px;
  font-size: 14px;
  font-weight: 600;
  color: var(--app-text-secondary, #9a8c98);
  background: transparent;
  border-radius: var(--app-radius-sm, 16px);
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
}

.nav-lucide-icon {
  width: 18px;
  height: 18px;
  color: var(--app-text-secondary, #9a8c98);
  flex-shrink: 0;
}

.sidebar-menu__item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 0;
  border-radius: 0 4px 4px 0;
  background: linear-gradient(180deg, var(--app-green, #bde0fe), var(--app-blue, #a2d2ff));
  transition: height 0.25s ease;
}

.sidebar-menu__item:hover {
  background: rgba(255,255,255,0.8);
  color: var(--app-text, #4a4e69);
}

.sidebar-menu__item:hover::before {
  height: 20px;
}

.sidebar-menu__item.active {
  background: rgba(255,255,255,0.8);
  color: var(--app-green, #89CFF0);
  box-shadow: var(--app-shadow-sm);
}

.sidebar-menu__item.active .nav-lucide-icon {
  color: var(--app-green, #89CFF0);
}

.sidebar-menu__item.active::before {
  height: 32px;
}

.sidebar-menu__label {
  flex: 1;
  min-width: 0;
  line-height: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--app-text, #4a4e69);
  font-size: 15px;
  font-weight: 700;
}

.sidebar-menu__item.active .sidebar-menu__label {
  color: #89CFF0;
  font-weight: 700;
}

.sidebar-menu__item:hover .sidebar-menu__label {
  color: var(--app-text, #4a4e69);
}

.sidebar-menu__badge {
  flex-shrink: 0;
  padding: 2px 8px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.6px;
  color: #fff;
  background: linear-gradient(135deg, #fc736d, #f7825a);
  border-radius: 10px;
  line-height: 15px;
  box-shadow: 0 1px 0 rgba(114, 93, 66, 0.25);
  animation: menuBadgePulse 1.8s ease-in-out infinite;
  margin-left: auto;
}
.sidebar-menu__badge--dev {
  background: linear-gradient(135deg, #b39ef3, #889df0);
  animation: none;
}

.sidebar-menu__item.active .sidebar-menu__badge {
  color: #fc736d;
  background: #fff;
  box-shadow: 0 1px 0 rgba(114, 93, 66, 0.15);
}

@keyframes menuBadgePulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.08); }
}

/* V6 section title & collapse */
.sidebar__group-title {
  font-size: 11px;
  font-weight: 700;
  color: var(--app-text-secondary, #9a8c98);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 12px 0 4px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}

.collapse-icon {
  font-size: 9px;
  transition: transform 0.2s ease;
  margin-right: 8px;
}

.sidebar__group-title.collapsed .collapse-icon {
  transform: rotate(-90deg);
}

.nav-section-items {
  overflow: hidden;
  transition: max-height 0.3s ease, opacity 0.2s ease;
}

.nav-section-items.collapsed {
  max-height: 0 !important;
  opacity: 0;
}

/* Footer — V6 user card */
.sidebar__footer {
  position: relative;
  padding: 0;
  border-top: none;
  display: flex;
  flex-direction: column;
  background: transparent;
}

.sidebar__user-card {
  margin: 12px;
  padding: 14px;
  background: rgba(255,255,255,0.4);
  border-radius: var(--app-radius-sm, 16px);
  border: 1px solid var(--app-glass-border, rgba(255,255,255,0.85));
}

.sidebar__user-label {
  font-size: 11px;
  color: var(--app-text-secondary, #9a8c98);
  font-weight: 600;
}

.sidebar__user-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: var(--app-text, #4a4e69);
  margin: 4px 0;
}

.sidebar__user-status {
  font-size: 11px;
  color: #95D5B2;
  font-weight: 600;
}

.sidebar__user-name {
  display: inline-block;
  color: var(--app-text, #4a4e69);
  font-size: 14px;
  font-weight: 800;
  background: none;
  -webkit-text-fill-color: currentColor;
  background-clip: border-box;
}

.logout-btn {
  background: rgba(227, 155, 85, 0.14) !important;
  border: 1.5px solid rgba(227, 155, 85, 0.45) !important;
  border-radius: 20px !important;
  color: #9a4e2e !important;
  font-weight: 800 !important;
  padding: 5px 14px !important;
  transition: transform 0.1s ease, background 0.1s ease, border-color 0.1s ease !important;
}
.logout-btn:hover {
  background: rgba(227, 155, 85, 0.24) !important;
  border-color: rgba(227, 155, 85, 0.7) !important;
  color: #7a3b1c !important;
  transform: translateY(-1px) !important;
}
.logout-btn:active {
  transform: translateY(0) !important;
}

.sidebar__user-arrow {
  font-size: 10px;
  margin-left: auto;
  color: var(--app-text-secondary, #9a8c98);
}
.sidebar__user-display.has-menu {
  cursor: pointer;
}

/* Account dropdown */
.account-menu {
  position: absolute;
  bottom: 100%;
  left: 8px;
  right: 8px;
  margin-bottom: 4px;
  background: rgba(255,255,255,0.72);
  border: 1.5px solid var(--app-glass-border, rgba(255,255,255,0.68));
  border-radius: 18px;
  box-shadow: var(--app-shadow-md, 0 8px 32px rgba(31,38,135,0.07));
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  overflow: hidden;
  z-index: 100;
}
.account-menu__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 600;
  color: var(--app-text, #4a4e69);
  cursor: pointer;
  transition: background 0.15s ease;
}
.account-menu__item:hover {
  background: rgba(162,210,255,0.16);
}
.account-menu__item.active {
  color: var(--app-green-deep, #6f9fd8);
}
.account-menu__check {
  font-size: 14px;
  color: var(--app-green-deep, #6f9fd8);
}
.account-menu__item--add {
  color: var(--app-text-secondary, #9a8c98);
  font-size: 12px;
  justify-content: center;
}
.account-menu__divider {
  height: 1px;
  background: rgba(255,255,255,0.52);
  margin: 0 12px;
}
</style>
