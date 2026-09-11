<script setup>
import { ref, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { animate } from 'animejs'
import { sidebarNavEnter } from '../animations'
import { NAV_CATEGORIES, MOD_COLORS } from './sidebarNavConfig'
import { useSidebarResize } from '../composables/useSidebarResize'
import { useAuthPool } from '@/shared/composables/useAuthPool'
import { logout as logoutApi } from '@/shared/api/auth'
import AnimatedMascot from './AnimatedMascot.vue'

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

const categories = NAV_CATEGORIES

// ── 可展开分组（元素定位）：父项点击展开/收起；进入子页时自动展开 ──
const expandedGroups = ref(new Set())

function isActive(path) {
  return route.path === path || route.path.startsWith(path + '/')
}

function isGroupActive(item) {
  return !!item.children?.some((sub) => isActive(sub.path))
}

function isGroupExpanded(item) {
  return expandedGroups.value.has(item.path)
}

function toggleGroup(item) {
  const next = new Set(expandedGroups.value)
  if (next.has(item.path)) {
    next.delete(item.path)
  } else {
    next.add(item.path)
  }
  expandedGroups.value = next
}

function onGroupClick(item) {
  if (collapsed.value) {
    // 折叠态无子项区：跳转到默认子页，保持可用
    router.push(item.children[0].path)
    return
  }
  toggleGroup(item)
  // 子项为点击后新增的 DOM：补渲染 lucide 图标
  nextTick(() => {
    if (window.lucide) window.lucide.createIcons()
  })
}

// 路由变化时自动展开当前分组（不覆盖用户手动收起后的再点击）
watch(
  () => route.path,
  () => {
    for (const cat of categories) {
      for (const item of cat.items) {
        if (item.children?.some((sub) => isActive(sub.path))) {
          const next = new Set(expandedGroups.value)
          if (!next.has(item.path)) {
            next.add(item.path)
            expandedGroups.value = next
          }
        }
      }
    }
  },
  { immediate: true },
)

onMounted(async () => {
  initSidebarWidth()
  window.addEventListener('mousemove', onSidebarResizeMove)
  window.addEventListener('mouseup', onSidebarResizeEnd)
  await nextTick()
  // Lucide icons render
  if (window.lucide) window.lucide.createIcons()
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
    <router-link to="/dashboard" class="sidebar__header" :title="collapsed ? 'AI 自动化测试平台' : ''">
      <div v-show="!collapsed" class="sidebar__brand">
        <span class="brand-ai">AI</span>
        <span class="brand-title">自动化测试平台</span>
      </div>
    </router-link>

    <!-- 导航菜单 -->
    <nav class="sidebar__nav">
      <div v-for="cat in categories" :key="cat.key" class="sidebar__group">
        <div
          v-if="cat.label && !collapsed"
          class="sidebar__group-label"
        >{{ cat.label }}</div>
        <div class="nav-section-items">
          <template v-for="item in cat.items" :key="item.path">
            <!-- 可展开分组：父项（展开/收起） + 子项 -->
            <template v-if="item.children">
              <button
                type="button"
                class="sidebar-menu__item sidebar-menu__item--group"
                :class="{ active: isGroupActive(item) }"
                :style="{ '--mod-color': MOD_COLORS[item.path] || 'var(--c-workflow)' }"
                :aria-expanded="isGroupExpanded(item)"
                :title="collapsed ? item.label : ''"
                @click="onGroupClick(item)"
              >
                <i :data-lucide="item.icon" class="nav-lucide-icon"></i>
                <span v-show="!collapsed" class="sidebar-menu__label">{{ item.label }}</span>
                <span v-show="!collapsed" class="sidebar-menu__chevron" :class="{ open: isGroupExpanded(item) }">▾</span>
              </button>
              <div v-show="isGroupExpanded(item) && !collapsed" class="sidebar-menu__sub">
                <router-link
                  v-for="sub in item.children"
                  :key="sub.path"
                  :to="sub.path"
                  :class="['sidebar-menu__item', 'sidebar-menu__item--sub', { active: isActive(sub.path) }]"
                  :style="{ '--mod-color': MOD_COLORS[sub.path] || MOD_COLORS[item.path] || 'var(--c-workflow)' }"
                >
                  <i :data-lucide="sub.icon" class="nav-lucide-icon nav-lucide-icon--sub"></i>
                  <span class="sidebar-menu__label">{{ sub.label }}</span>
                </router-link>
              </div>
            </template>

            <!-- 普通导航项 -->
            <router-link
              v-else
              :to="item.path"
              :class="['sidebar-menu__item', { active: isActive(item.path) }]"
              :style="{ '--mod-color': MOD_COLORS[item.path] || 'var(--c-workflow)' }"
              :title="collapsed ? item.label : ''"
            >
              <i :data-lucide="item.icon" class="nav-lucide-icon"></i>
              <span v-show="!collapsed" class="sidebar-menu__label">{{ item.label }}</span>
              <span
                v-if="(item.isDev || item.badge) && !collapsed"
                :class="['sidebar-menu__badge', item.badgeClass || 'sidebar-menu__badge--dev']"
              >{{ item.badge || '开发中' }}</span>
            </router-link>
          </template>
        </div>
      </div>
    </nav>

    <!-- 底部用户区 / 账号切换器 -->
    <div class="sidebar__footer">
      <div class="sidebar__user-card">
        <div class="sidebar__user-label">Digital Human</div>
        <button
          type="button"
          class="sidebar__user-display has-menu"
          data-testid="sidebar-account-menu"
          :title="collapsed ? activeAccount : ''"
          :aria-expanded="showAccountMenu"
          @click="showAccountMenu = !showAccountMenu"
        >
          <AnimatedMascot :size="18" />
          <span v-show="!collapsed" class="sidebar__user-name" data-testid="sidebar-active-account">{{ activeAccount }}</span>
          <span v-if="!collapsed" class="sidebar__user-arrow">▾</span>
        </button>
        <div v-show="!collapsed" class="sidebar__user-row">
          <div class="sidebar__user-status">● 在线</div>
          <el-button
            link
            size="small"
            danger
            class="logout-btn"
            data-testid="sidebar-logout"
            @click.stop="logout"
          >
            退出
          </el-button>
        </div>
      </div>

      <!-- Account dropdown -->
      <div v-if="showAccountMenu && !collapsed" class="account-menu">
        <button
          v-for="name in accountList"
          :key="name"
          type="button"
          class="account-menu__item"
          :class="{ active: name === activeAccount }"
          :data-testid="`sidebar-account-${name}`"
          @click="switchToAccount(name)"
        >
          <span>{{ name }}</span>
          <span v-if="name === activeAccount" class="account-menu__check">✓</span>
        </button>
        <div class="account-menu__divider"></div>
        <router-link
          :to="{ path: '/login', query: { add: '1' } }"
          class="account-menu__item account-menu__item--add"
          data-testid="sidebar-add-account"
          @click="showAccountMenu = false"
        >
          添加账号
        </router-link>
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

<style src="./AppSidebar.style.css" scoped></style>
