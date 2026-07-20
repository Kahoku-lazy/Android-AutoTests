<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { staggerReveal } from '@/shared/animations.js'
// AppCard → el-card (Element Plus auto-import)

const props = defineProps({
  stats: { type: Object, default: () => ({}) },
})

const router = useRouter()

const modules = computed(() => {
  const s = props.stats
  return [
    {
      id: 'device-pool', title: '设备管理',
      subtitle: '设备池 · 连接 · 锁管理',
      path: '/devices', cardColor: 'app-blue', pattern: 'app-blue',
      stats: { label: '在线设备', value: String(s.devices?.online ?? 0), total: String(s.devices?.total ?? 0) },
      features: ['USB + Wi-Fi', '队列管理', '批量操作'], size: 'tall',
    },
    {
      id: 'element-locator', title: '元素定位',
      subtitle: '截图 · XPath · 验证',
      path: '/elements', cardColor: 'purple', pattern: 'purple',
      stats: { label: '已定位', value: String(s.elements?.total ?? 0), total: '' },
      features: ['实时截图', '智能选择器', '多候选列表'], size: 'wide',
    },
    {
      id: 'test-runner', title: '执行引擎',
      subtitle: '任务调度 · WebSocket 日志',
      path: '/runner', cardColor: 'app-pink', pattern: 'app-pink',
      stats: { label: '运行中', value: String(s.runs?.active ?? 0), total: String(s.runs?.total ?? 0) },
      features: ['并发执行', '实时日志', '状态追踪'], size: 'normal',
    },
    {
      id: 'case-manager', title: '测试用例',
      subtitle: 'YAML DSL · 步骤编排',
      path: '/cases', cardColor: 'app-teal', pattern: 'app-teal',
      stats: { label: '用例数', value: String(s.cases?.total ?? 0), total: '' },
      features: ['可视化编辑', '参数化', '分组管理'], size: 'normal',
    },
    {
      id: 'workflow', title: '工作流',
      subtitle: '页面关系图 · Scratch 积木',
      path: '/workflow', cardColor: 'app-orange', pattern: 'app-orange',
      stats: { label: '工作台', value: 'Demo', total: '' },
      features: ['起点/终点', 'Vue Flow', 'Blockly'], size: 'normal',
    },
    {
      id: 'report-generator', title: '测试报告',
      subtitle: 'Allure · 趋势分析',
      path: '/reports', cardColor: 'app-green', pattern: 'app-green',
      stats: { label: '报告数', value: String(s.reports?.total ?? 0), total: '' },
      features: ['图表分析', '失败溯源', '导出 PDF'], size: 'normal',
    },
    {
      id: 'ai-assistant', title: 'AI 助手',
      subtitle: 'Agent · 对话 · 编排',
      path: '/ai-assistant', cardColor: 'app-orange', pattern: 'app-orange',
      stats: { label: '智能体', value: String(s.agents?.total ?? 0), total: '' },
      features: ['SSE 流式', '多 Agent', '知识库'], size: 'tall',
    },
    {
      id: 'element-manager', title: '元素管理',
      subtitle: '页面 · 元素库 · 复用',
      path: '/element-mgr', cardColor: 'brown', pattern: 'brown',
      stats: { label: '页面数', value: String(s.elements?.pages ?? 0), total: '' },
      features: ['分类标签', '快速检索', '用例关联'], size: 'normal',
    },
  ]
})

const cardRefs = ref([])

onMounted(() => {
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
    <div class="module-nav__header">
      <h2 class="module-nav__title">功能模块</h2>
      <span class="module-nav__subtitle">{{ modules.length }} 个核心模块</span>
    </div>

    <div class="module-nav__grid">
      <div
        v-for="(mod, idx) in modules"
        :key="mod.id"
        :class="'module-cell module-cell--' + mod.size"
      >
        <el-card
          :ref="(el) => setCardRef(el, idx)"
          class="module-card"
          @click="navigate(mod.path)"
        >
          <div class="module-card__inner">
            <div class="module-card__top">
              <div class="module-card__stats" v-if="mod.stats.value">
                <span class="module-card__stats-value">{{ mod.stats.value }}</span>
                <span v-if="mod.stats.total" class="module-card__stats-sep">/</span>
                <span v-if="mod.stats.total" class="module-card__stats-total">{{ mod.stats.total }}</span>
                <span class="module-card__stats-label">{{ mod.stats.label }}</span>
              </div>
            </div>
            <div class="module-card__info">
              <h3 class="module-card__title">{{ mod.title }}</h3>
              <p class="module-card__subtitle">{{ mod.subtitle }}</p>
            </div>
            <div class="module-card__features">
              <span v-for="(feat, fi) in mod.features" :key="fi" class="module-card__tag">{{ feat }}</span>
            </div>
            <div class="module-card__arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </div>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<style scoped>
.module-nav { width: 100%; }
.module-nav__header {
  display: flex; align-items: baseline; gap: 12px; margin-bottom: 20px;
}
.module-nav__title {
  font-family: var(--font-display, Nunito, sans-serif);
  font-size: 20px; font-weight: 700;
  color: var(--animal-text-color, #794f27); margin: 0;
}
.module-nav__subtitle {
  font-size: 13px; color: var(--app-text-secondary, #9f927d); font-weight: 500;
}

/* Bento Grid */
.module-nav__grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  grid-auto-rows: 160px;
  gap: 14px;
}
@media (max-width: 1200px) { .module-nav__grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 768px) { .module-nav__grid { grid-template-columns: repeat(2, 1fr); grid-auto-rows: 140px; } }
@media (max-width: 480px) { .module-nav__grid { grid-template-columns: 1fr; grid-auto-rows: 130px; } }

.module-cell--tall { grid-row: span 2; }
.module-cell--wide { grid-column: span 2; }

/* AppCard within cell */
.module-card {
  height: 100%;
  cursor: pointer;
  transition: transform 0.35s cubic-bezier(0.4,0,0.2,1);
}
.module-card:hover {
  transform: translateY(-3px);
}
.module-card :deep(.el-card__body) {
  height: 100%;
  padding: 18px 20px;
}

.module-card__inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
}

.module-card__top {
  display: flex;
  justify-content: flex-end;
}

.module-card__stats {
  display: flex; align-items: baseline; gap: 2px; flex-wrap: wrap; justify-content: flex-end;
}
.module-card__stats-value {
  font-family: Nunito, sans-serif;
  font-size: 26px; font-weight: 800; line-height: 1;
}
.module-card__stats-sep,
.module-card__stats-total {
  font-size: 14px; opacity: 0.6;
}
.module-card__stats-label {
  font-size: 10px; opacity: 0.6;
  text-transform: uppercase; letter-spacing: 0.5px; width: 100%; text-align: right;
}

.module-card__info { flex: 1; }
.module-card__title {
  font-family: var(--font-display, Nunito, sans-serif);
  font-size: 16px; font-weight: 700;
  margin: 0 0 2px;
}
.module-card__subtitle {
  font-size: 12px; opacity: 0.65; margin: 0; line-height: 1.4;
}

.module-card__features {
  display: flex; flex-wrap: wrap; gap: 6px;
}
.module-card__tag {
  font-size: 10px; padding: 3px 8px; border-radius: 20px;
  background: rgba(255,255,255,0.5); font-weight: 500;
  backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px);
}

.module-card__arrow {
  position: absolute; right: 4px; bottom: 4px;
  opacity: 0.4; transition: all 0.3s ease;
}
.module-card:hover .module-card__arrow { opacity: 0.8; }
</style>
