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
      { path: '/digital-human', icon: 'user-round', label: '平台数字人', badge: '待开发', badgeClass: 'sidebar-menu__badge--pending' },
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

  // Brand entrance — restrained geometric reveal
  animate('.sidebar__brand', {
    opacity: [0, 1],
    duration: 400,
    ease: 'outCubic',
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
              v-if="(item.isDev || item.badge) && !collapsed"
              :class="['sidebar-menu__badge', item.badgeClass || 'sidebar-menu__badge--dev']"
            >{{ item.badge || '开发中' }}</span>
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
/* ═══════════════════════════════════════════
   Origami Tech — 折纸科技主题
   签名: clip-path 折角 + 几何菱形 Core + 极简黑白
   ═══════════════════════════════════════════ */

/* ── 容器 ── */
.sidebar {
  flex: 0 0 var(--side-w, 220px);
  width: var(--side-w, 220px);
  min-width: var(--side-w, 220px);
  max-width: var(--side-w, 220px);
  height: 100%;
  background: linear-gradient(180deg, #fdfdfc 0%, #f8f9fb 100%);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 2;
  border-right: 1px solid #e8ecf1;
  box-shadow: 8px 0 32px rgba(0,0,0,0.03);
  color: #1a202c;
  font-family: var(--app-font, Quicksand, 'PingFang SC', 'Microsoft YaHei', sans-serif);
  transition: width 0.2s ease, min-width 0.2s ease, max-width 0.2s ease, flex-basis 0.2s ease;
  border-radius: 0;
}

.sidebar--collapsed {
  flex: 0 0 64px;
  width: 64px;
  min-width: 64px;
  max-width: 64px;
}

/* ── 头部 ── */
.sidebar__header-row {
  display: flex;
  align-items: center;
  gap: 2px;
  padding-right: 6px;
  border-bottom: 1.5px solid #e8ecf1;
  flex-shrink: 0;
}
.sidebar__toggle {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  margin-top: 4px;
  border: 1.5px solid #d4d8dc;
  border-radius: 4px;
  background: #fff;
  color: #1a202c;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  line-height: 1;
  display: grid;
  place-items: center;
  transition: all 0.15s ease;
}
.sidebar__toggle:hover {
  border-color: #1a202c;
  background: #1a202c;
  color: #fff;
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
  border: 1.5px solid #e8ecf1;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #a0aec0;
  padding: 4px;
  border-radius: 4px;
}
.sidebar__icon-logout:hover {
  background: #1a202c;
  border-color: #1a202c;
  color: #fff;
}

.sidebar--resizing {
  user-select: none;
}

/* ── 拖拽调整 ── */
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
  border-radius: 1px;
  background: #d4d8dc;
  transition: background 0.15s ease, width 0.15s ease;
}
.sidebar__resizer:hover::before,
.sidebar__resizer.is-dragging::before {
  width: 3px;
  background: #1a202c;
}
.sidebar__resizer:hover,
.sidebar__resizer.is-dragging {
  background: rgba(26,32,44,0.04);
}

/* ── 品牌 ── */
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
.sidebar__header:hover {
  color: #1a202c;
}
.sidebar__brand {
  display: flex;
  align-items: center;
  min-width: 0;
  font-size: 15px;
  line-height: 1.2;
}
.brand-title {
  display: inline-block;
  font-weight: 800;
  font-size: 14px;
  white-space: nowrap;
  color: #1a202c;
  letter-spacing: -0.02em;
  background: none;
  -webkit-text-fill-color: currentColor;
  background-clip: border-box;
  animation: none;
}

/* ── 品牌图标 Origami 折纸容器 ── */
.sidebar__header :deep(img),
.sidebar__header :deep(svg) {
  border-radius: 0;
}

/* ── 导航 ── */
.sidebar__nav {
  flex: 1;
  overflow-y: auto;
  padding: 12px 12px;
}
.sidebar__group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

/* ── 分区标签 — 几何折线 ── */
.sidebar__group-title {
  font-size: 10px;
  font-weight: 700;
  color: #a0aec0;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  margin: 10px 0 2px 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  user-select: none;
}
.sidebar__group-title::after {
  content: '';
  display: block;
  width: 20px;
  height: 2px;
  margin-left: 8px;
  background: linear-gradient(90deg, #1a202c, transparent);
  border-radius: 1px;
}
.collapse-icon {
  font-size: 8px;
  transition: transform 0.2s ease;
  margin-right: 4px;
  color: #a0aec0;
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

/* ── 菜单项 ── */
.sidebar-menu__item {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 10px;
  height: 40px;
  padding: 0 12px;
  font-size: 13px;
  font-weight: 500;
  color: #718096;
  background: transparent;
  border: 1.5px solid transparent;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.nav-lucide-icon {
  width: 18px;
  height: 18px;
  color: #718096;
  flex-shrink: 0;
  stroke-width: 1.8;
}

.sidebar-menu__item:hover {
  background: #f7fafc;
  color: #1a202c;
}
.sidebar-menu__item:hover .nav-lucide-icon {
  color: #1a202c;
}

/* ── 活性状态: clip-path 折角 ── */
.sidebar-menu__item.active {
  color: #1a202c;
  font-weight: 700;
  background: #fff;
  border: 1.5px solid #1a202c;
  border-radius: 0;
  clip-path: polygon(0% 0%, calc(100% - 10px) 0%, 100% 10px, 100% 100%, 0% 100%);
  box-shadow: none;
}
.sidebar-menu__item.active .nav-lucide-icon {
  color: #1a202c;
}
.sidebar-menu__item.active .sidebar-menu__label {
  color: #1a202c;
  font-weight: 700;
}

/* 签名: 活性项菱形 Core */
.sidebar-menu__item.active::after {
  content: '';
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%) rotate(45deg);
  width: 6px;
  height: 6px;
  background: #89CFF0;
  border: 1px solid #1a202c;
}

/* 重置旧主题的 ::before */
.sidebar-menu__item::before {
  display: none;
}

/* ── 标签 ── */
.sidebar-menu__label {
  flex: 1;
  min-width: 0;
  line-height: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #718096;
  font-size: 13px;
  font-weight: 500;
}
.sidebar-menu__item:hover .sidebar-menu__label {
  color: #1a202c;
}

/* ── Badge ── */
.sidebar-menu__badge {
  flex-shrink: 0;
  padding: 2px 7px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #718096;
  background: #f7fafc;
  border-radius: 2px;
  line-height: 15px;
  margin-left: auto;
  animation: none;
  border: 1px solid #e8ecf1;
}
.sidebar-menu__badge--dev {
  background: #f7fafc;
  color: #718096;
  animation: none;
}
.sidebar-menu__badge--pending {
  background: #fefcbf;
  color: #975a16;
  border-color: #f0e090;
  animation: origami-pending 2s ease-in-out infinite;
}
@keyframes origami-pending {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.55; }
}
.sidebar-menu__item.active .sidebar-menu__badge {
  color: #1a202c;
  background: #f7fafc;
  border-color: #1a202c;
}

/* ── 底部用户区 ── */
.sidebar__footer {
  position: relative;
  padding: 0;
  border-top: none;
  display: flex;
  flex-direction: column;
  background: transparent;
}
.sidebar__user-card {
  margin: 10px;
  padding: 12px;
  background: #fff;
  border-radius: 4px;
  border: 1px solid #e8ecf1;
}
.sidebar__user-label {
  font-size: 10px;
  color: #a0aec0;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.sidebar__user-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 700;
  color: #1a202c;
  margin: 3px 0;
}
.sidebar__user-display.has-menu {
  cursor: pointer;
}
.sidebar__user-arrow {
  font-size: 10px;
  margin-left: auto;
  color: #a0aec0;
}
.sidebar__user-status {
  font-size: 10px;
  color: #2f9e44;
  font-weight: 600;
}
.sidebar__user-name {
  display: inline-block;
  color: #1a202c;
  font-size: 13px;
  font-weight: 700;
  background: none;
  -webkit-text-fill-color: currentColor;
  background-clip: border-box;
}

/* ── 退出按钮 ── */
.logout-btn {
  background: transparent !important;
  border: 1.5px solid #e8ecf1 !important;
  border-radius: 2px !important;
  color: #a0aec0 !important;
  font-weight: 700 !important;
  font-size: 11px !important;
  padding: 5px 14px !important;
  transition: all 0.15s ease !important;
  letter-spacing: 0.03em;
}
.logout-btn:hover {
  background: #1a202c !important;
  border-color: #1a202c !important;
  color: #fff !important;
  transform: none !important;
}
.logout-btn:active {
  transform: scale(0.97) !important;
}

/* ── 账号下拉 ── */
.account-menu {
  position: absolute;
  bottom: 100%;
  left: 6px;
  right: 6px;
  margin-bottom: 4px;
  background: #fff;
  border: 1.5px solid #e8ecf1;
  border-radius: 4px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.06);
  overflow: hidden;
  z-index: 100;
}
.account-menu__item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 9px 12px;
  font-size: 12px;
  font-weight: 600;
  color: #1a202c;
  cursor: pointer;
  transition: background 0.1s ease;
}
.account-menu__item:hover {
  background: #f7fafc;
}
.account-menu__item.active {
  color: #1a202c;
  font-weight: 700;
}
.account-menu__check {
  font-size: 12px;
  color: #2f9e44;
}
.account-menu__item--add {
  color: #a0aec0;
  font-size: 11px;
  justify-content: center;
}
.account-menu__divider {
  height: 1px;
  background: #e8ecf1;
  margin: 0 8px;
}
</style>
