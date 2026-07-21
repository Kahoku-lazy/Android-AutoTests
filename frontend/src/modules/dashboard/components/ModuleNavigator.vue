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
      color: 'purple', gradient: 'linear-gradient(135deg,#C9B6F2,#a78bfa)',
      icon: 'crosshair',
      stats: { label: '元素数', value: String(s.elements?.total ?? 0), total: '' },
    },
    {
      id: 'case-manager', title: '用例管理',
      desc: '步骤编排 · 目录树 · YAML 导入导出',
      path: '/cases',
      color: 'app-teal', gradient: 'linear-gradient(135deg,#89CFF0,#60a5fa)',
      icon: 'layers',
      stats: { label: '用例数', value: String(s.cases?.total ?? 0), total: '' },
    },
    {
      id: 'test-runner', title: '执行引擎',
      desc: '任务调度 · 实时进度 · WebSocket 日志',
      path: '/runner',
      color: 'app-pink', gradient: 'linear-gradient(135deg,#FFB5A7,#f87171)',
      icon: 'play-circle',
      stats: { label: '运行中', value: String(s.runs?.active ?? 0), total: String(s.runs?.total ?? 0) },
    },
    {
      id: 'report-generator', title: '测试报告',
      desc: 'KPI 摘要 · 失败定位 · 趋势图表',
      path: '/reports',
      color: 'brown', gradient: 'linear-gradient(135deg,#9a8c98,#8b7f8f)',
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
.module-nav { width: 100%; }

/* ── V6 页面标题 ── */
.page-header { margin-bottom: 28px; }
.page-title {
  font-size: 1.8rem; font-weight: 700;
  color: var(--app-text, #4a4e69); margin: 0;
}
.page-subtitle {
  font-size: .9rem; color: var(--app-text-secondary, #9a8c98); margin-top: 4px;
}

/* ── V6 3 列模块卡片网格 ── */
.modules-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
@media (max-width: 1200px) { .modules-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 768px) { .modules-grid { grid-template-columns: 1fr; } }

/* ── V6 模块卡片 ── */
.module-card {
  background: var(--app-glass-card, rgba(255,255,255,0.65));
  backdrop-filter: blur(var(--app-glass-blur, 20px));
  -webkit-backdrop-filter: blur(var(--app-glass-blur, 20px));
  border-radius: var(--app-radius-md, 20px);
  padding: 24px;
  border: 1px solid var(--app-glass-border, rgba(255,255,255,0.85));
  box-shadow: var(--app-shadow-sm, 0 4px 15px rgba(0,0,0,.02));
  transition: all .3s;
  position: relative;
  overflow: hidden;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.module-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 4px;
  border-radius: 20px 20px 0 0;
}

.module-card:hover {
  box-shadow: var(--app-shadow-md, 0 8px 25px rgba(0,0,0,.05));
  transform: translateY(-3px);
}

/* 彩色顶条 */
.module-card--yellow::before { background: #F4D35E; }
.module-card--green::before { background: #95D5B2; }
.module-card--purple::before { background: #C9B6F2; }
.module-card--teal::before { background: #89CFF0; }
.module-card--pink::before { background: #FFB5A7; }
.module-card--brown::before { background: #9a8c98; }
.module-card--orange::before { background: #5EEAD4; }
.module-card--blue::before { background: #BDE0FE; }

/* ── 模块图标 ── */
.module-icon {
  width: 48px; height: 48px;
  border-radius: var(--app-radius-sm, 16px);
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 14px;
}
.module-icon i {
  width: 24px; height: 24px;
  color: #fff;
}

/* ── 模块内容 ── */
.module-body { flex: 1; display: flex; flex-direction: column; }
.module-name {
  font-size: 1.05rem; font-weight: 700;
  color: var(--app-text, #4a4e69); margin-bottom: 6px;
}
.module-desc {
  font-size: .82rem; color: var(--app-text-secondary, #9a8c98);
  margin-bottom: 12px; line-height: 1.5;
  flex: 1;
}
.module-meta {
  display: flex; align-items: center; justify-content: space-between;
  gap: 8px;
}
.module-stat {
  font-size: .75rem; color: var(--app-text-secondary, #9a8c98);
}
.module-stat strong {
  font-family: var(--app-font-display, Quicksand, sans-serif);
  font-size: 1.2rem; font-weight: 800; color: var(--app-text, #4a4e69);
  margin-right: 2px;
}
.module-stat small {
  display: block; font-size: .65rem; text-transform: uppercase;
  letter-spacing: 0.4px; opacity: 0.7;
}

/* ── 进入按钮 ── */
.module-enter {
  font-size: .78rem; font-weight: 600; color: #fff;
  padding: 6px 14px; border-radius: var(--app-radius-sm, 16px);
  border: none; cursor: pointer;
  transition: all .2s; font-family: inherit;
  flex-shrink: 0;
}
.module-enter:hover {
  transform: translateY(-1px); filter: brightness(1.1);
}
</style>
