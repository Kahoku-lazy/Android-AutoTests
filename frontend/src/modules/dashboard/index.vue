<script setup>
import { onMounted } from "vue";
import { useDashboardStats } from "./composables/useDashboardStats.js";

// Card, Divider → el-card, el-divider (Element Plus auto-import)
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue";
import {
  IconDevice,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
  IconTarget,
  IconZap,
  IconLayers,
} from "@/shared/icons/index.js";

import StatsAppCard from "./components/StatsCard.vue";
import TrendBarChart from "./components/TrendBarChart.vue";
import TaskResultPanel from "./components/TaskResultPanel.vue";
import ModuleNavigator from "./components/ModuleNavigator.vue";
import ActivityTimeline from "./components/ActivityTimeline.vue";
import ErrorState from "@/shared/components/patterns/ErrorState.vue";

const {
  loading,
  refreshing,
  error,
  stats,
  executionChart,
  executionSummary,
  recentTasks,
  lastUpdated,
  systemStatus,
  activities,
  loadData,
  refreshData,
} = useDashboardStats();

const CASE_BREAKDOWN = [
  { type: "ui_automation",  label: "Android用例",  color: "app-green",  icon: IconDevice },
  { type: "web_automation", label: "Web用例",      color: "app-teal",   icon: IconTarget },
  { type: "api_testing",    label: "API用例",       color: "app-yellow", icon: IconZap },
  { type: "storage",        label: "功能业务",       color: "app-pink",   icon: IconLayers },
]

function getBreakdownItem(type) {
  return stats.value.cases.breakdown?.find(b => b.type === type) || { total: 0, enabled: 0 }
}

const ELEMENT_BREAKDOWN = [
  { type: "android", label: "Android元素", color: "app-green",  icon: IconDevice },
  { type: "web",     label: "Web元素",     color: "app-teal",   icon: IconTarget },
  { type: "api",     label: "API接口",     color: "app-yellow", icon: IconZap },
]

function getElementItem(type) {
  return stats.value.elements.typeBreakdown?.find(b => b.type === type) || { total: 0 }
}

onMounted(() => {
  loadData();
});
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      title="仪表盘"
      subtitle="自动化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告"
      icon="layout-dashboard"
      icon-gradient="linear-gradient(135deg,#F4D35E,#f0c06a)"
    >
      <template #actions>
        <el-button class="wb-btn wb-btn--sunset" size="small" :loading="refreshing" @click="refreshData">
          刷新
        </el-button>
      </template>
    </WorkbenchHeader>

    <ErrorState v-if="error" :message="error" @retry="loadData" />

    <!-- 内容区 -->
    <div class="doc-body">
      <!-- 欢迎导航 -->
      <section class="doc-section">
        <ModuleNavigator :stats="stats" />
      </section>

      <!-- 统计概览：平台运营 -->
      <section class="doc-section">
        <h3 class="doc-section__title">平台运营<span class="doc-tag">Platform</span></h3>
        <div class="doc-section__label">
          设备 {{ stats.devices.online }}/{{ stats.devices.total }}
          · 智能体 {{ stats.agents.active }}/{{ stats.agents.total }}
          · 任务 {{ stats.runs.active }}/{{ stats.runs.total }}
          · 工作流 {{ stats.workflow.total }}
        </div>
        <div class="dashboard__stats-grid dashboard__stats-grid--compact">
          <StatsAppCard
            label="在线设备"
            :value="stats.devices.online"
            :suffix="` / ${stats.devices.total}`"
            color="app-green"
            :trend="stats.devices.trend"
            trend-label="活跃"
            path="/devices"
            :loading="loading"
          >
            <template #icon><IconDevice :size="18" color="#fff" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="活跃智能体"
            :value="stats.agents.active"
            :suffix="` / ${stats.agents.total}`"
            color="app-blue"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon><IconBrain :size="18" color="#fff" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="运行中任务"
            :value="stats.runs.active"
            :suffix="` / ${stats.runs.total}`"
            color="app-pink"
            path="/runner"
            :loading="loading"
          >
            <template #icon>
              <IconPlay :size="18" color="#fff" />
              <span class="dashboard__live-dot" v-if="stats.runs.active > 0"></span>
            </template>
          </StatsAppCard>
          <StatsAppCard
            label="工作流"
            :value="stats.workflow.total"
            :suffix="`${stats.workflow.page_flows} 流 / ${stats.workflow.test_cases} 用例`"
            color="purple"
            path="/workflow"
            :loading="loading"
          >
            <template #icon><IconLayers :size="18" color="#fff" /></template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 统计概览：测试用例 -->
      <section class="doc-section">
        <h3 class="doc-section__title">测试用例<span class="doc-tag">Cases</span></h3>
        <div class="doc-section__label">
          共 {{ stats.cases.total }} 个 · 已启用 {{ stats.cases.enabled }} · 本周新增 {{ stats.cases.trend }}
        </div>
        <div class="dashboard__stats-grid dashboard__stats-grid--compact">
          <StatsAppCard
            v-for="item in CASE_BREAKDOWN"
            :key="item.type"
            :label="item.label"
            :value="getBreakdownItem(item.type).total"
            :suffix="`${getBreakdownItem(item.type).enabled} 启用`"
            :color="item.color"
            path="/cases"
            :loading="loading"
          >
            <template #icon>
              <component :is="item.icon" :size="18" color="#fff" />
            </template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 统计概览：元素定位 -->
      <section class="doc-section">
        <h3 class="doc-section__title">元素定位<span class="doc-tag">Elements</span></h3>
        <div class="doc-section__label">
          共 {{ stats.elements.total }} 个 · {{ stats.elements.pages }} 个页面
        </div>
        <div class="dashboard__stats-grid dashboard__stats-grid--compact">
          <StatsAppCard
            v-for="item in ELEMENT_BREAKDOWN"
            :key="'el-' + item.type"
            :label="item.label"
            :value="getElementItem(item.type).total"
            :color="item.color"
            path="/elements"
            :loading="loading"
          >
            <template #icon>
              <component :is="item.icon" :size="18" color="#fff" />
            </template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 趋势图表 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          趋势数据
          <span class="doc-tag">Trends</span>
        </h3>
        <div class="doc-section__label">
          近 12 期执行成功、失败与新建用例统计
        </div>
        <div class="dashboard__trends">
          <el-card class="trends-chart-card">
            <TrendBarChart :chart="executionChart" />
          </el-card>
          <el-card class="trends-tasks-card">
            <div class="trends-tasks-card__title">任务执行结果</div>
            <TaskResultPanel :tasks="recentTasks" :summary="executionSummary" />
          </el-card>
        </div>
      </section>

      <!-- 最近动态 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          最近动态
          <span class="doc-tag">Activity</span>
        </h3>
        <ActivityTimeline :items="activities" />
      </section>

      <!-- 页脚信息 -->
      <footer class="dashboard__footer">
        <div class="dashboard__footer-item">
          <IconClock :size="14" />
          <span>最近更新: {{ lastUpdated || "暂无数据" }}</span>
        </div>
        <div class="dashboard__footer-item">
          <IconAlertCircle :size="14" />
          <span
            >系统状态:
            {{ systemStatus === "normal" ? "正常运行" : "无设备连接" }}</span
          >
        </div>
      </footer>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════
   Paper × Polaroid — 仪表盘布局
   ═══════════════════════════════════════════ */

/* ── 底纹 + 全局 ── */
.doc-page {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background:
    radial-gradient(circle, var(--app-paper-dot) 0.8px, transparent 0.8px);
  background-size: 14px 14px;
  background-color: var(--doodle-bg, #faf5ee);
}
.doc-body {
  flex: 1;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
  padding: 0 20px 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

/* ── Stats Grid — 分层拍立得卡片 ── */
.dashboard__stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  padding-top: 8px;
}
.dashboard__stats-grid > :nth-child(odd)  { transform: rotate(-0.5deg); }
.dashboard__stats-grid > :nth-child(even) { transform: rotate(0.5deg); }
.dashboard__stats-grid > :hover { transform: rotate(0deg) scale(1.03) !important; z-index: 10; }

/* ── Compact card overrides ── */
.dashboard__stats-grid--compact :deep(.stats-card) {
  min-height: 110px;
  padding: 5px 5px 20px 5px;
}
.dashboard__stats-grid--compact :deep(.stats-card__icon) {
  height: 36px;
  margin-bottom: 4px;
}
.dashboard__stats-grid--compact :deep(.stats-card__icon svg) {
  width: 18px !important;
  height: 18px !important;
}
.dashboard__stats-grid--compact :deep(.stats-card__title) {
  font-size: 11px;
}
.dashboard__stats-grid--compact :deep(.stats-card__stat strong) {
  font-size: 18px;
}
.dashboard__stats-grid--compact :deep(.stats-card__stat small) {
  font-size: 10px;
}
.dashboard__stats-grid--compact :deep(.stats-card__enter) {
  font-size: 10px;
  padding: 2px 8px;
}

@media (max-width: 520px) {
  .dashboard__stats-grid { grid-template-columns: 1fr; gap: 8px; }
}

/* ── Section 区 ── */
.doc-section {
  background: transparent;
  border: none;
  border-radius: 0;
  box-shadow: none;
  padding: 0;
}
.doc-section__header {
  margin-bottom: 0;
}
.doc-section__title {
  font-family: var(--app-font-display);
  font-size: var(--app-size-lg);
  font-weight: 700;
  color: var(--ink);
  display: inline-block;
  position: relative;
  margin-bottom: 8px;
}
.doc-section__title::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 3px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 80 3'%3E%3Cpath d='M0,1.5 Q20,0 40,2 Q60,3 80,1.5' stroke='%232d2d2d' stroke-width='2' fill='none'/%3E%3C/svg%3E") repeat-x;
  background-size: 40px 3px;
}
.doc-section__label {
  font-size: var(--app-size-xs);
  color: var(--app-ink-muted);
  font-weight: 600;
  margin: 0 0 12px;
}
.doc-tag {
  font-size: var(--app-size-xs);
  padding: 1px 8px;
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  color: var(--app-ink-muted);
  border: 1.5px solid var(--app-border-light);
  font-weight: 700;
  margin-left: 8px;
}

/* ── Trends — 拍立得横排卡片 ── */
.dashboard__trends {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 14px;
  align-items: stretch;
}
@media (max-width: 960px) {
  .dashboard__trends { grid-template-columns: 1fr; }
}
.trends-chart-card,
.trends-tasks-card {
  display: flex;
  flex-direction: column;
}
.trends-chart-card :deep(.el-card__body),
.trends-tasks-card :deep(.el-card__body) {
  padding: 12px 12px 30px 12px;
  border-radius: 6px 10px 6px 10px;
  background: #fff;
  border: 2.5px solid var(--ink);
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  box-shadow: 2px 3px 0 rgba(0, 0, 0, 0.05);
  position: relative;
}
/* 图钉 */
.trends-chart-card :deep(.el-card__body)::before,
.trends-tasks-card :deep(.el-card__body)::before {
  content: '';
  position: absolute;
  top: 4px;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  background: radial-gradient(circle, #e8e0d5 30%, #a09080 100%);
  border-radius: 50%;
  box-shadow: 0 1px 1px rgba(0, 0, 0, 0.08);
  z-index: 2;
}
.trends-chart-card { transform: rotate(-0.3deg); }
.trends-tasks-card { transform: rotate(0.4deg); }
.trends-chart-card :deep(.el-card) {
  background: transparent; border: none; box-shadow: none;
}
.trends-tasks-card :deep(.el-card) {
  background: transparent; border: none; box-shadow: none;
}
.trends-tasks-card__title {
  font-size: var(--app-size-sm);
  font-weight: 800;
  color: var(--ink);
  margin-bottom: 10px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* ── Live dot ── */
.dashboard__live-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--app-live);
  top: -2px;
  right: -2px;
  animation: livePulse 1.5s ease-in-out infinite;
}
@keyframes livePulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.5); }
  50% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
}

/* ── Footer ── */
.dashboard__footer {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 14px 20px;
  background: #FFE066;
  border: 2.5px solid var(--ink);
  border-radius: 6px 10px 6px 10px;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--app-footer-yellow-text);
  font-family: var(--app-font-display);
}
.dashboard__footer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: var(--app-size-sm);
}
.dashboard__footer-item :deep(svg) {
  color: var(--app-footer-yellow-text);
  stroke: var(--app-footer-yellow-text);
}

/* ── Module Nav 覆盖 ── */
:deep(.module-nav-card) {
  background: #fff !important;
  border: 2.5px solid var(--ink) !important;
  border-radius: 6px 10px 6px 10px !important;
  box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.04) !important;
}
:deep(.module-nav-card:hover) {
  transform: translate(1px, 1px) !important;
  box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.06) !important;
}

/* ── Activity Timeline 覆盖 ── */
:deep(.activity-item) {
  border-bottom: 1.5px dashed var(--app-border-light) !important;
}
</style>
