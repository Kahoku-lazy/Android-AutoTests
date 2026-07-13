<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { animate } from 'animejs'
import { sidebarNavEnter } from '../animations.js'
import { Icon, Button, Title, Divider, Card } from 'animal-island-vue'
import AnimatedMascot from './AnimatedMascot.vue'
import AnimatedMenuIcon from './AnimatedMenuIcon.vue'

const router = useRouter()
const route = useRoute()
const username = ref(localStorage.getItem('username') || 'admin')

const SIDEBAR_WIDTH_KEY = 'app-sidebar-width'
const SIDEBAR_MIN = 180
const SIDEBAR_MAX = 360
const SIDEBAR_DEFAULT = 220

function clampSidebarWidth(width) {
  return Math.min(SIDEBAR_MAX, Math.max(SIDEBAR_MIN, width))
}

const sidebarWidth = ref(SIDEBAR_DEFAULT)
const isResizing = ref(false)

function applySidebarWidth(width) {
  const w = clampSidebarWidth(width)
  sidebarWidth.value = w
  document.documentElement.style.setProperty('--side-w', `${w}px`)
}

function onSidebarResizeStart(e) {
  if (e.button !== 0) return
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

function logout() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('username')
  router.push('/login')
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
      { path: '/runner',      icon: 'runner',           label: '执行引擎' },
      { path: '/reports',     icon: 'reports',          label: '测试报告' },
      { path: '/ai-assistant', icon: 'ai-assistant',    label: 'AI 助手', isDev: true },
    ],
  },
]

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function onNavClick(path) {
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
  <aside class="sidebar" :class="{ 'sidebar--resizing': isResizing }">
    <!-- 头部品牌 -->
    <div class="sidebar__header" @click="router.push('/dashboard')">
      <AnimatedMascot :size="26" />
      <div class="sidebar__brand">
        <span class="brand-ai">AI</span>
        <span class="brand-name">测试平台</span>
      </div>
    </div>

    <!-- 导航菜单 -->
    <nav class="sidebar__nav">
      <div v-for="cat in categories" :key="cat.key" class="sidebar__group">
        <div v-if="cat.label" class="sidebar__group-title">{{ cat.label }}</div>
        <div
          v-for="item in cat.items"
          :key="item.path"
          :class="['sidebar-menu__item', { active: isActive(item.path) }]"
          @click="onNavClick(item.path)"
        >
          <AnimatedMenuIcon :name="item.icon" :size="20" :active="isActive(item.path)" />
          <span class="sidebar-menu__label">{{ item.label }}</span>
          <span v-if="item.isDev" class="sidebar-menu__badge sidebar-menu__badge--dev">开发中</span>
        </div>
      </div>
    </nav>

    <!-- 底部用户区 -->
    <div class="sidebar__footer">
      <div class="sidebar__user">
        <AnimatedMascot :size="20" />
        <span class="sidebar__user-name">{{ username }}</span>
      </div>
      <Button type="text" size="small" danger class="logout-btn" @click.stop="logout">
        退出
      </Button>
    </div>

    <div
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
  background: url('/animal-assets/menu_bg.svg') center/cover no-repeat;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  position: relative;
  z-index: 2;
  color: var(--animal-text-color, #794f27);
  font-family: var(--animal-font-family, Nunito, 'Noto Sans SC', sans-serif);
}

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
  padding: 20px 16px 12px;
  border-bottom: 1px solid #e8e2d6;
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
  background-image: linear-gradient(90deg, #19c8b9, #4facfe, #19c8b9);
}

.brand-name {
  background-image: linear-gradient(90deg, #f6a85f, #f78fb3, #f6a85f);
}

.sidebar__user-name {
  background-image: linear-gradient(90deg, #a18cd1, #fbc2eb, #a18cd1);
  font-size: 13px;
}

.sidebar__header:hover .brand-ai,
.sidebar__header:hover .brand-name {
  filter: brightness(1.1);
}

.sidebar__header:hover { color: var(--animal-primary-color, #19c8b9); }

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
  background: var(--animal-primary-color, #19c8b9);
  transition: height 0.25s ease;
}

.sidebar-menu__item:hover {
  background: #e9f4ef;
  color: #5c4b38;
}

.sidebar-menu__item:hover::before {
  height: 24px;
}

.sidebar-menu__item.active {
  background: #b7c6e5;
  color: #fff;
  box-shadow: 0 4px 12px rgba(119, 141, 190, 0.35);
}

.sidebar-menu__item.active::before {
  height: 0;
}

.sidebar-menu__label {
  flex: 1;
  min-width: 0;
  line-height: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: linear-gradient(90deg, #7a6b58 0%, #9a8568 50%, #c4a06a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  color: transparent;
  font-size: 15px;
  font-weight: 700;
}

.sidebar-menu__item.active .sidebar-menu__label {
  background: linear-gradient(90deg, #ffffff 0%, #e6f9f6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-menu__item:hover .sidebar-menu__label {
  background: linear-gradient(90deg, #5c4b38 0%, #8a7355 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  padding: 12px 16px;
  border-top: 1px solid #e8e2d6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #19c8b9;
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
  background: #fc736d !important;
  border: none !important;
  border-radius: 20px !important;
  color: #fff !important;
  font-weight: 700 !important;
  padding: 5px 14px !important;
  box-shadow: 0 4px 0 #e85a54 !important;
  transition: transform 0.1s ease, box-shadow 0.1s ease !important;
}
.logout-btn:hover {
  background: #ff8781 !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 0 #e85a54 !important;
}
.logout-btn:active {
  transform: translateY(2px) !important;
  box-shadow: 0 2px 0 #e85a54 !important;
}
</style>
