<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { staggerReveal } from '@/shared/animations.js'

const props = defineProps({
  stats: { type: Object, default: () => ({}) },
})

const router = useRouter()

// ── PRD 8 模块 → V6 配色 + Lucide 图标 ──
const modules = computed(() => {
  const s = props.stats
  return [
    {
      id: 'dashboard', title: '仪表盘',
      desc: '平台首页 · KPI 概览 · 全局导航',
      path: '/dashboard',
      color: 'app-yellow', gradient: 'linear-gradient(135deg,#F4D35E,#f0c06a)',
      icon: 'layout-dashboard',
      stats: { label: '快捷入口', value: '8', total: '' },
    },
    {
      id: 'device-pool', title: '设备管理',
      desc: 'ADB 扫描 · 连接锁定 · 排队调度',
      path: '/devices',
      color: 'app-green', gradient: 'linear-gradient(135deg,#95D5B2,#52b788)',
      icon: 'smartphone',
      stats: { label: '在线设备', value: String(s.devices?.online ?? 0), total: String(s.devices?.total ?? 0) },
    },
    {
      id: 'element-locator', title: '元素定位',
      desc: '实时截图 · Dump UI · XPath 生成',
      path: '/elements',
      color: 'purple', gradient: 'linear-gradient(135deg,var(--app-status-purple),#a78bfa)',
      icon: 'crosshair',
      stats: { label: '元素数', value: String(s.elements?.total ?? 0), total: '' },
    },
    {
      id: 'case-manager', title: '用例管理',
      desc: '步骤编排 · 目录树 · YAML 导入导出',
      path: '/cases',
      color: 'app-teal', gradient: 'linear-gradient(135deg,var(--c-workflow),#60a5fa)',
      icon: 'layers',
      stats: { label: '用例数', value: String(s.cases?.total ?? 0), total: '' },
    },
    {
      id: 'test-runner', title: '执行引擎',
      desc: '任务调度 · 实时进度 · WebSocket 日志',
      path: '/runner',
      color: 'app-pink', gradient: 'linear-gradient(135deg,var(--app-status-danger),var(--app-live))',
      icon: 'play-circle',
      stats: { label: '运行中', value: String(s.runs?.active ?? 0), total: String(s.runs?.total ?? 0) },
    },
    {
      id: 'report-generator', title: '测试报告',
      desc: 'KPI 摘要 · 失败定位 · 趋势图表',
      path: '/reports',
      color: 'brown', gradient: 'linear-gradient(135deg,var(--app-text-secondary),#8b7f8f)',
      icon: 'file-bar-chart',
      stats: { label: '报告数', value: String(s.reports?.total ?? 0), total: '' },
    },
    {
      id: 'ai-assistant', title: 'AI 助手',
      desc: '自然语言驱动 · SSE 流式 · 知识库',
      path: '/ai-assistant',
      color: 'app-orange', gradient: 'linear-gradient(135deg,#5EEAD4,#14b8a6)',
      icon: 'bot',
      stats: { label: '智能体', value: String(s.agents?.total ?? 0), total: '' },
    },
    {
      id: 'workflow', title: '工作流工作台',
      desc: 'Blockly 积木 · VueFlow 画图 · 同步用例库',
      path: '/workflow',
      color: 'app-blue', gradient: 'linear-gradient(135deg,#BDE0FE,#93c5fd)',
      icon: 'git-branch',
      stats: { label: 'Demo', value: '', total: '' },
    },
  ]
})

const cardRefs = ref([])

onMounted(async () => {
  await nextTick()
  if (window.lucide) window.lucide.createIcons()
  if (cardRefs.value.length) {
    staggerReveal(cardRefs.value, 70, 0.9)
  }
})

function navigate(path) {
  router.push(path)
}

function setCardRef(el, idx) {
  if (el) cardRefs.value[idx] = el.$el || el
}
</script>

<template>
  <div class="module-nav">
    <div class="page-header">
      <h1 class="page-title">欢迎使用 AI 自动化测试平台</h1>
      <p class="page-subtitle">V6 · 8 模块全栈平台 · AI 驱动的 Android UI 自动化测试</p>
    </div>

    <div class="modules-grid">
      <div
        v-for="(mod, idx) in modules"
        :key="mod.id"
        :ref="(el) => setCardRef(el, idx)"
        :class="['module-card', 'module-card--' + mod.color.replace('app-','')]"
        @click="navigate(mod.path)"
      >
        <div class="module-icon" :style="{ background: mod.gradient }">
          <i :data-lucide="mod.icon"></i>
        </div>
        <div class="module-body">
          <div class="module-name">{{ mod.title }}</div>
          <div class="module-desc">{{ mod.desc }}</div>
          <div class="module-meta">
            <span v-if="mod.stats.value" class="module-stat">
              <strong>{{ mod.stats.value }}</strong><template v-if="mod.stats.total">/{{ mod.stats.total }}</template>
              <small>{{ mod.stats.label }}</small>
            </span>
            <span v-else class="module-stat">
              <small>{{ mod.stats.label }}</small>
            </span>
            <button class="module-enter" :style="{ background: mod.gradient }">进入 →</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════
   Paper × Polaroid — 模块导航卡片
   ═══════════════════════════════════════════ */
.module-nav { width: 100%; }

/* ── 页面标题 ── */
.page-header { margin-bottom: 22px; }
.page-title {
  font-family: var(--app-font-display);
  font-size: var(--app-size-xl); font-weight: 700;
  color: var(--ink); margin: 0;
}
.page-subtitle {
  font-size: var(--app-size-xs); color: var(--app-ink-muted); margin-top: 2px; font-weight: 600;
}

/* ── 网格 ── */
.modules-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
@media (max-width: 1100px) { .modules-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 520px) { .modules-grid { grid-template-columns: 1fr; } }

/* ── 纸艺卡片 ── */
.module-card {
  background: #fff;
  border-radius: 6px 10px 6px 10px;
  padding: 18px 16px;
  border: 2.5px solid var(--ink);
  box-shadow: 2px 2px 0 rgba(0,0,0,0.04);
  transition: all .15s;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0;
}
.module-card:hover {
  transform: translate(1px, 1px);
  box-shadow: 1px 1px 0 rgba(0,0,0,0.06);
}
.module-card::before { display: none; }

/* ── 模块图标 ── */
.module-icon {
  width: 42px; height: 42px;
  border-radius: 4px 8px 4px 8px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 12px;
  border: 2px solid var(--ink);
}
.module-icon i {
  width: 20px; height: 20px;
  color: #fff;
}

/* ── 模块内容 ── */
.module-body { flex: 1; display: flex; flex-direction: column; }
.module-name {
  font-size: var(--app-size-sm); font-weight: 800;
  color: var(--ink); margin-bottom: 4px;
}
.module-desc {
  font-size: var(--app-size-xs); color: var(--app-ink-muted);
  margin-bottom: 10px; line-height: 1.4;
  flex: 1;
}
.module-meta {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
}
.module-stat {
  font-size: var(--app-size-xs); color: var(--app-ink-muted); font-weight: 600;
}
.module-stat strong {
  font-family: 'Nunito', sans-serif;
  font-size: var(--app-size-lg); font-weight: 800; color: var(--ink);
  margin-right: 2px;
}
.module-stat small {
  display: block; font-size: var(--app-size-xs); text-transform: uppercase;
  letter-spacing: 0.4px; opacity: 0.6;
}

/* ── 进入按钮 ── */
.module-enter {
  font-size: var(--app-size-xs); font-weight: 800; color: #fff;
  padding: 5px 12px; border-radius: 4px 8px 4px 8px;
  border: 2px solid transparent; cursor: pointer;
  transition: all .15s; font-family: inherit;
  flex-shrink: 0;
}
.module-enter:hover {
  transform: translateY(-1px);
}
</style>
