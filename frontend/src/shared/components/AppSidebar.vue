<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { animate } from 'animejs'
import { sidebarNavEnter, selectPop } from '../animations.js'
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
window.addEventListener('storage', (e) => {
  if (e.key === POOL_KEY) refreshAccountState()
})

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
const SIDEBAR_DEFAULT = 220
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

const categories = [
  {
    key: 'cat-basic',
    label: '',
    items: [
      { path: '/dashboard',   icon: 'dashboard',        label: '仪表盘' },
      { path: '/devices',     icon: 'devices',          label: '设备管理' },
      { path: '/elements',    icon: 'elements',         label: '元素定位' },
      { path: '/cases',       icon: 'cases',            label: '测试用例' },
      { path: '/workflow',    icon: 'workflow',         label: '工作流', isDev: true },
      { path: '/runner',      icon: 'runner',           label: '执行引擎' },
      { path: '/reports',     icon: 'reports',          label: '测试报告' },
      { path: '/ai-assistant', icon: 'ai-assistant',    label: 'AI 助手', isDev: true },
    ],
  },
]

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function onNavClick(path, ev) {
  const item = ev?.currentTarget
  if (item) selectPop(item)
  router.push(path)
}

onMounted(async () => {
  applySidebarWidth(Number(localStorage.getItem(SIDEBAR_WIDTH_KEY)) || SIDEBAR_DEFAULT)
  window.addEventListener('mousemove', onSidebarResizeMove)
  window.addEventListener('mouseup', onSidebarResizeEnd)

  await nextTick()
  sidebarNavEnter('.sidebar-menu__item')

  // Brand entrance
  animate('.sidebar__brand', {
    opacity: [0, 1],
    translateY: [-8, 0],
    scale: [0.96, 1],
    duration: 600,
    ease: 'outCubic',
  })
  animate('.brand-ai', {
    backgroundPosition: ['0% 50%', '100% 50%'],
    duration: 3000,
    loop: true,
    direction: 'alternate',
    ease: 'linear',
  })
  animate('.brand-name', {
    backgroundPosition: ['100% 50%', '0% 50%'],
    duration: 3000,
    loop: true,
    direction: 'alternate',
    ease: 'linear',
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
      <div class="sidebar__header" @click="router.push('/dashboard')" :title="collapsed ? 'AI 测试平台' : ''">
        <AnimatedMascot :size="26" />
        <div v-show="!collapsed" class="sidebar__brand">
          <span class="brand-ai">AI</span>
          <span class="brand-name">测试平台</span>
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
        <div v-if="cat.label && !collapsed" class="sidebar__group-title">{{ cat.label }}</div>
        <div
          v-for="item in cat.items"
          :key="item.path"
          :class="['sidebar-menu__item', { active: isActive(item.path) }]"
          :title="collapsed ? item.label : ''"
          @click="onNavClick(item.path, $event)"
        >
          <AnimatedMenuIcon :name="item.icon" :size="20" :active="isActive(item.path)" />
          <span v-show="!collapsed" class="sidebar-menu__label">{{ item.label }}</span>
          <span
            v-if="item.isDev && !collapsed"
            class="sidebar-menu__badge sidebar-menu__badge--dev"
          >开发中</span>
        </div>
      </div>
    </nav>

    <!-- 底部用户区 / 账号切换器 -->
    <div class="sidebar__footer">
      <div
        class="sidebar__user"
        :class="{ 'has-menu': allAccounts.length > 1 }"
        :title="collapsed ? username : ''"
        @click="allAccounts.length > 1 ? (showAccountMenu = !showAccountMenu) : null"
      >
        <AnimatedMascot :size="20" />
        <span v-show="!collapsed" class="sidebar__user-name">{{ username }}</span>
        <span v-if="!collapsed && allAccounts.length > 1" class="sidebar__user-arrow">▾</span>
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
  background: rgba(255,255,255,0.55);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 2;
  border-right: 1px solid rgba(255,255,255,0.55);
  color: var(--app-text, #3D4A3B);
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
  border-bottom: 1px solid rgba(121, 79, 39, 0.08);
  flex-shrink: 0;
}
.sidebar__toggle {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  margin-top: 4px;
  border: 1.5px solid rgba(121, 79, 39, 0.15);
  border-radius: 8px;
  background: rgba(255, 251, 245, 0.85);
  color: #794f27;
  font-size: 16px;
  font-weight: 800;
  cursor: pointer;
  line-height: 1;
  display: grid;
  place-items: center;
}
.sidebar__toggle:hover {
  border-color: #19c8b9;
  color: #0d7a70;
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
  background: rgba(196, 184, 158, 0.45);
  transition: background 0.15s ease, width 0.15s ease;
}

.sidebar__resizer:hover::before,
.sidebar__resizer.is-dragging::before {
  width: 3px;
  background: #19c8b9;
}

.sidebar__resizer:hover,
.sidebar__resizer.is-dragging {
  background: rgba(25, 200, 185, 0.08);
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
  gap: 4px;
  font-size: 18px;
}

.brand-ai,
.brand-name,
.sidebar__user-name {
  display: inline-block;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  background-size: 200% auto;
  font-weight: 800;
}

.brand-ai {
  background-image: linear-gradient(90deg, var(--app-green), var(--app-blue), var(--app-green));
}

.brand-name {
  background-image: linear-gradient(90deg, var(--app-green-deep), var(--app-green), var(--app-green-deep));
}

.sidebar__user-name {
  background-image: linear-gradient(90deg, var(--app-blue), var(--app-green-light), var(--app-blue));
  font-size: 13px;
}

.sidebar__header:hover .brand-ai,
.sidebar__header:hover .brand-name {
  filter: brightness(1.1);
}

.sidebar__header:hover { color: var(--app-green-deep, #19c8b9); }

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
  height: 50px;
  padding: 0 18px;
  font-size: 15px;
  font-weight: 700;
  color: #7a6b58;
  background: transparent;
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
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
  background: var(--app-green, #8EC8A0);
  transition: height 0.25s ease;
}

.sidebar-menu__item:hover {
  background: rgba(142,200,160,0.12);
  color: var(--app-text, #3D4A3B);
}

.sidebar-menu__item:hover::before {
  height: 24px;
}

.sidebar-menu__item.active {
  background: rgba(142,200,160,0.22);
  color: var(--app-green-deep, #5DA870);
  box-shadow: 0 2px 12px rgba(142,200,160,0.18);
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
  color: var(--app-text, #3D4A3B);
  font-size: 15px;
  font-weight: 700;
}

.sidebar-menu__item.active .sidebar-menu__label {
  color: var(--app-green-deep, #5DA870);
  font-weight: 800;
}

.sidebar-menu__item:hover .sidebar-menu__label {
  color: var(--app-text, #3D4A3B);
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

/* Footer */
.sidebar__footer {
  position: relative;
  padding: 12px 16px;
  border-top: 1px solid var(--app-glass-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, var(--app-green), var(--app-green-deep));
}

.sidebar__user {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #fff;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0,0,0,0.15);
}

.sidebar__user-name {
  background: linear-gradient(90deg, #ffffff 0%, #e6f9f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  font-size: 14px;
  font-weight: 700;
}

.logout-btn {
  background: rgba(255,255,255,0.25) !important;
  border: 1px solid rgba(255,255,255,0.4) !important;
  border-radius: 20px !important;
  color: #fff !important;
  font-weight: 700 !important;
  padding: 5px 14px !important;
  transition: transform 0.1s ease, background 0.1s ease !important;
}
.logout-btn:hover {
  background: rgba(255,255,255,0.4) !important;
  transform: translateY(-2px) !important;
}
.logout-btn:active {
  transform: translateY(0px) !important;
}

.sidebar__user-arrow {
  font-size: 10px;
  margin-left: 2px;
  opacity: 0.6;
}
.sidebar__user.has-menu {
  cursor: pointer;
}

/* Account dropdown */
.account-menu {
  position: absolute;
  bottom: 100%;
  left: 8px;
  right: 8px;
  margin-bottom: 4px;
  background: #fffef9;
  border: 1.5px solid rgba(121, 79, 39, 0.12);
  border-radius: 14px;
  box-shadow: 0 6px 20px rgba(0,0,0,0.12);
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
  color: #794f27;
  cursor: pointer;
  transition: background 0.15s ease;
}
.account-menu__item:hover {
  background: #f5f0e6;
}
.account-menu__item.active {
  color: #19c8b9;
}
.account-menu__check {
  font-size: 14px;
  color: #19c8b9;
}
.account-menu__item--add {
  color: #9f927d;
  font-size: 12px;
  justify-content: center;
}
.account-menu__divider {
  height: 1px;
  background: rgba(121, 79, 39, 0.08);
  margin: 0 12px;
}
</style>
