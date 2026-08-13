<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { sidebarNavEnter } from '../animations'
import { NAV_CATEGORIES } from './sidebarNavConfig'
import { useSidebarResize } from '../composables/useSidebarResize'
import { useAuthPool } from '@/shared/composables/useAuthPool'
import { logout as logoutApi } from '@/shared/api/auth'
import AnimatedMascot from './AnimatedMascot.vue'
import AnimatedMenuIcon from './AnimatedMenuIcon.vue'

const router = useRouter()
const route = useRoute()

// ── Multi-account auth ──
const { activeAccount, accountList, switchAccount, logoutAccount } = useAuthPool()

const showAccountMenu = ref(false)

function switchToAccount(name) {
  if (switchAccount(name)) {
    showAccountMenu.value = false
    window.location.reload()
  }
}

function finishLocalLogout() {
  const hasRemaining = logoutAccount()
  if (!hasRemaining) {
    router.push('/login')
  } else {
    window.location.reload()
  }
}

async function logout() {
  try {
    await logoutApi()
  } catch (e) {
    const data = e?.response?.data
    // Redis 不可用：保留本地登录态，提示稍后重试
    if (e?.response?.status === 503 && data?.retry) {
      ElMessage.warning(data.message || '服务暂时异常，请稍后重试')
      return
    }
    // 其它失败（网络/已失效）：仍清本地，避免用户卡在已失效会话
  }
  finishLocalLogout()
}

const {
  sidebarWidth, isResizing, collapsed,
  applySidebarWidth, toggleCollapsed,
  onSidebarResizeStart, onSidebarResizeMove, onSidebarResizeEnd,
  resetSidebarWidth, initSidebarWidth,
} = useSidebarResize();

// ── 导航分组（V6 原型结构）──
const expandedSections = ref({})

function toggleSection(key) {
  expandedSections.value[key] = !expandedSections.value[key]
}

const categories = NAV_CATEGORIES

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function onNavClick(path, ev) {
  router.push(path)
}

onMounted(async () => {
  initSidebarWidth()
  window.addEventListener('mousemove', onSidebarResizeMove)
  window.addEventListener('mouseup', onSidebarResizeEnd)
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
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
})
</script>

<template>
  <aside
    class="sidebar"
    data-testid="app-sidebar"
    :class="{ 'sidebar--resizing': isResizing, 'sidebar--collapsed': collapsed }"
  >
    <!-- 头部品牌（高度与主区 wb-header 底边对齐） -->
    <div class="sidebar__header" @click="router.push('/dashboard')" :title="collapsed ? 'AI 自动化测试平台' : ''">
      <AnimatedMascot :size="36" />
      <div v-show="!collapsed" class="sidebar__brand">
        <span class="brand-ai">AI</span>
        <span class="brand-title">自动化测试平台</span>
      </div>
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
        <div
          class="sidebar__user-display has-menu"
          data-testid="sidebar-account-menu"
          :title="collapsed ? activeAccount : ''"
          @click="showAccountMenu = !showAccountMenu"
        >
          <AnimatedMascot :size="18" />
          <span v-show="!collapsed" class="sidebar__user-name" data-testid="sidebar-active-account">{{ activeAccount }}</span>
          <span v-if="!collapsed" class="sidebar__user-arrow">▾</span>
        </div>
        <div v-show="!collapsed" class="sidebar__user-status">● 在线</div>
      </div>

      <!-- Account dropdown -->
      <div v-if="showAccountMenu && !collapsed" class="account-menu">
        <div
          v-for="name in accountList"
          :key="name"
          class="account-menu__item"
          :class="{ active: name === activeAccount }"
          :data-testid="`sidebar-account-${name}`"
          @click="switchToAccount(name)"
        >
          <span>{{ name }}</span>
          <span v-if="name === activeAccount" class="account-menu__check">✓</span>
        </div>
        <div class="account-menu__divider"></div>
        <div
          class="account-menu__item account-menu__item--add"
          data-testid="sidebar-add-account"
          @click="showAccountMenu = false; router.push('/login?add=1')"
        >
          添加账号
        </div>
      </div>

      <div v-show="!collapsed" data-testid="sidebar-logout">
        <el-button
          link
          size="small"
          danger
          class="logout-btn"
          @click.stop="logout"
        >
          退出
        </el-button>
      </div>
      <button
        v-show="collapsed"
        type="button"
        class="sidebar__icon-logout"
        title="退出登录"
        @click.stop="logout"
      >
        ⎋
      </button>

      <button
        type="button"
        class="sidebar__toggle"
        :title="collapsed ? '展开侧边栏' : '收起侧边栏'"
        @click.stop="toggleCollapsed"
      >
        {{ collapsed ? '›' : '‹' }}
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
   Doodle Craft — 侧边栏
   ═══════════════════════════════════════════ */

/* ── 容器 ── */
.sidebar {
  flex: 0 0 var(--side-w, 228px); width: var(--side-w, 228px);
  min-width: var(--side-w, 228px); max-width: var(--side-w, 228px);
  height: 100%; background: var(--paper); display: flex; flex-direction: column;
  overflow: hidden; position: relative; z-index: 2;
  border-right: 3px solid var(--ink); box-shadow: 3px 0 0 rgba(0,0,0,0.03);
  color: var(--ink); font-family: var(--app-font);
  transition: width 0.2s ease, min-width 0.2s ease, max-width 0.2s ease, flex-basis 0.2s ease;
  border-radius: 0;
}

.sidebar--collapsed {
  flex: 0 0 64px;
  width: 64px;
  min-width: 64px;
  max-width: 64px;
}

/* ── 折叠按钮（底部） ── */
.sidebar__toggle {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  margin: 4px 10px 10px;
  align-self: flex-start;
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

.sidebar--collapsed .sidebar__header {
  justify-content: center;
  padding: 0;
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
.sidebar--collapsed .sidebar__toggle {
  align-self: center;
  margin: 4px auto 8px;
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

/* ── 品牌（与 wb-header 同高，底边对齐） ── */
.sidebar__header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  height: var(--app-topbar-h, 96px);
  box-sizing: border-box;
  min-width: 0;
  padding: 0 16px;
  border-bottom: 1.5px solid #e8ecf1;
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
  align-items: baseline;
  gap: 6px;
  min-width: 0;
  line-height: 1;
}
.brand-ai {
  flex-shrink: 0;
  font-family: var(--app-font-display);
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.02em;
  background: linear-gradient(
    90deg,
    var(--c-dashboard),
    var(--c-device),
    var(--c-workflow),
    var(--c-element),
    var(--c-ai),
    var(--c-runner),
    var(--c-dashboard)
  );
  background-size: 300% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  -webkit-text-fill-color: transparent;
  animation: brand-ai-flow 4s linear infinite;
}
@keyframes brand-ai-flow {
  0% { background-position: 0% 50%; }
  100% { background-position: 100% 50%; }
}
.brand-title {
  display: inline-block;
  font-family: var(--app-font-display);
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  color: var(--ink);
  background: none;
  -webkit-text-fill-color: currentColor;
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
  font-size: 12px;
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
  font-size: 9px;
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
  height: 42px;
  padding: 0 12px;
  font-size: 14px;
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
  width: 20px;
  height: 20px;
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
  background: var(--c-workflow);
  border: 1px solid #1a202c;
}

/* 重置旧主题的 ::before */
.sidebar-menu__item::before { display: none; }
.sidebar-menu__item.active::after {
  content: '✦'; position: absolute; right: 8px; font-size: 8px; color: var(--ink);
  animation: dc-twinkle 2.4s ease-in-out infinite;
}
@keyframes dc-twinkle { 0%,100%{opacity:0.3} 50%{opacity:1} }

/* ── 标签 ── */
.sidebar-menu__label {
  flex: 1;
  min-width: 0;
  line-height: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #718096;
  font-size: 14px;
  font-weight: 500;
}
.sidebar-menu__item:hover .sidebar-menu__label {
  color: #1a202c;
}

/* ── Badge ── */
.sidebar-menu__badge {
  flex-shrink: 0;
  padding: 2px 7px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  color: #718096;
  background: #f7fafc;
  border-radius: 2px;
  line-height: 16px;
  margin-left: auto;
  animation: none;
  border: 3px solid var(--doodle-ink, #2d2d2d);
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
  border: 3px solid var(--doodle-ink, #2d2d2d);
}
.sidebar__user-label {
  font-size: 11px;
  color: #a0aec0;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.sidebar__user-display {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 700;
  color: #1a202c;
  margin: 3px 0;
}
.sidebar__user-display.has-menu {
  cursor: pointer;
}
.sidebar__user-arrow {
  font-size: 11px;
  margin-left: auto;
  color: #a0aec0;
}
.sidebar__user-status {
  font-size: 11px;
  color: #2f9e44;
  font-weight: 600;
}
.sidebar__user-name {
  display: inline-block;
  color: #1a202c;
  font-size: 14px;
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
  font-size: 12px !important;
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
  font-size: 13px;
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
  font-size: 13px;
  color: #2f9e44;
}
.account-menu__item--add {
  color: #a0aec0;
  font-size: 12px;
  justify-content: center;
}
.account-menu__divider {
  height: 1px;
  background: #e8ecf1;
  margin: 0 8px;
}
</style>
