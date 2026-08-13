<script setup lang="ts">
import { useDashboardView } from './DashboardView.logic'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import StatsAppCard from './components/StatsCard.vue'
import TrendBarChart from './components/TrendBarChart.vue'
import TaskResultPanel from './components/TaskResultPanel.vue'
import ModuleNavigator from './components/ModuleNavigator.vue'
import ActivityTimeline from './components/ActivityTimeline.vue'
import {
  IconDevice,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
  IconLayers,
} from '@/shared/icons/index'

const {
  loading,
  refreshing,
  error,
  PAGE_HEADER,
  stats,
  executionChart,
  executionSummary,
  recentTasks,
  lastUpdated,
  systemStatus,
  activities,
  loadData,
  refreshData,
  caseBreakdown,
  elementBreakdown,
  getBreakdownItem,
  getElementItem,
} = useDashboardView()
</script>

<template>
  <div class="doc-page wb-shell">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
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
          设备 {{ stats.devices.total }}
          · 智能体 {{ stats.agents.total }}
          · 任务 {{ stats.runs.total }}
          · 工作流 {{ stats.workflow.total }}
        </div>
        <div class="dashboard__stats-grid dashboard__stats-grid--compact">
          <StatsAppCard
            label="在线设备"
            :value="stats.devices.online"
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
            color="app-blue"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon><IconBrain :size="18" color="#fff" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="运行中任务"
            :value="stats.runs.active"
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
          共 {{ stats.cases.total }} 个 · 本周新增 {{ stats.cases.trend }}
        </div>
        <div class="dashboard__stats-grid dashboard__stats-grid--compact">
          <StatsAppCard
            v-for="item in caseBreakdown"
            :key="item.type"
            :label="item.label"
            :value="getBreakdownItem(item.type).total"
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
            v-for="item in elementBreakdown"
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

<style src="./DashboardView.style.css" scoped></style>
