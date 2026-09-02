<script setup lang="ts">
import { useDashboardView, toMillions, toK } from './DashboardView.logic'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import StatsAppCard from './components/StatsCard.vue'
import TrendBarChart from './components/TrendBarChart.vue'
import SeriesBarChart from './components/SeriesBarChart.vue'
import TaskResultPanel from './components/TaskResultPanel.vue'
import ActivityTimeline from './components/ActivityTimeline.vue'
import {
  IconDevice,
  IconPlay,
  IconBrain,
  IconClock,
  IconAlertCircle,
  IconLayers,
  IconMonitor,
  IconClipboardCheck,
  IconTarget,
  IconTrendingUp,
  IconActivity,
  IconZap,
} from '@/shared/icons/index'

const {
  loading,
  refreshing,
  error,
  PAGE_HEADER,
  stats,
  executionChart,
  executionSummary,
  aiTokenChart,
  deepseekCostChart,
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
  tokenSeries,
  costSeries,
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
      <!-- 统计概览：平台运营 -->
      <section class="doc-section">
        <h3 class="doc-section__title"><IconMonitor :size="19" />平台运营<span class="doc-tag">Platform</span></h3>
        <div class="doc-section__label">
          设备 {{ stats.devices.total }}
          · 智能体 {{ stats.agents.total }}
          · 任务 {{ stats.runs.total }}
          · 工作流 {{ stats.workflow.total }}
        </div>
        <div class="dashboard__stats-grid">
          <StatsAppCard
            label="在线设备"
            :value="stats.devices.online"
            color="sage"
            path="/devices"
            :loading="loading"
          >
            <template #icon><IconDevice :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="活跃智能体"
            :value="stats.agents.active"
            color="gray"
            path="/ai-assistant"
            :loading="loading"
          >
            <template #icon><IconBrain :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="运行中任务"
            :value="stats.runs.active"
            color="rose"
            path="/runner"
            :loading="loading"
            :live="stats.runs.active > 0"
          >
            <template #icon><IconPlay :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="工作流"
            :value="stats.workflow.total"
            color="pale"
            path="/workflow"
            :loading="loading"
          >
            <template #icon><IconLayers :size="15" /></template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 统计概览：AI 用量 -->
      <section class="doc-section">
        <h3 class="doc-section__title"><IconBrain :size="19" />AI 用量<span class="doc-tag">AI</span></h3>
        <div class="doc-section__label">
          累计 Token {{ (stats.aiUsage.totalTokens.total / 1000000).toFixed(2) }}M
          · 任务 {{ stats.aiUsage.taskCount.total }}
          · DeepSeek 费用 {{ stats.aiUsage.deepseekCost.total.toFixed(2) }} 元
        </div>
        <div class="dashboard__stats-grid">
          <StatsAppCard
            label="任务数量"
            :value="stats.aiUsage.taskCount.total"
            color="gray"
            path="/ai-assistant"
            :loading="loading"
            :desc="`今日 ${stats.aiUsage.taskCount.today.toLocaleString()}`"
          >
            <template #icon><IconBrain :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="累计 Token"
            :value="toMillions(stats.aiUsage.totalTokens.total)"
            suffix="M"
            :decimals="2"
            color="sage"
            path="/ai-assistant"
            :loading="loading"
            :desc="`今日 ${(stats.aiUsage.totalTokens.today / 1000000).toFixed(2)}M`"
          >
            <template #icon><IconTrendingUp :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="缓存命中率"
            :value="stats.aiUsage.cacheHitRate.total"
            suffix="%"
            :decimals="1"
            color="deep"
            path="/ai-assistant"
            :loading="loading"
            :desc="`今日 ${stats.aiUsage.cacheHitRate.today}%`"
          >
            <template #icon><IconTarget :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="平均每任务 Token"
            :value="toK(stats.aiUsage.avgTokensPerTask.total)"
            suffix="K"
            :decimals="1"
            color="cream"
            path="/ai-assistant"
            :loading="loading"
            :desc="`今日 ${(stats.aiUsage.avgTokensPerTask.today / 1000).toFixed(1)}K`"
          >
            <template #icon><IconLayers :size="15" /></template>
          </StatsAppCard>
          <StatsAppCard
            label="DeepSeek 费用"
            :value="stats.aiUsage.deepseekCost.total"
            suffix=" 元"
            :decimals="2"
            color="dust"
            path="/ai-assistant"
            :loading="loading"
            :desc="`今日 ${stats.aiUsage.deepseekCost.today.toFixed(2)} 元`"
          >
            <template #icon><IconZap :size="15" /></template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 统计概览：测试用例 -->
      <section class="doc-section">
        <h3 class="doc-section__title"><IconClipboardCheck :size="19" />测试用例<span class="doc-tag">Cases</span></h3>
        <div class="doc-section__label">
          共 {{ stats.cases.total }} 个
        </div>
        <div class="dashboard__stats-grid">
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
              <component :is="item.icon" :size="15" />
            </template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 统计概览：元素定位 -->
      <section class="doc-section">
        <h3 class="doc-section__title"><IconTarget :size="19" />元素定位<span class="doc-tag">Elements</span></h3>
        <div class="doc-section__label">
          共 {{ stats.elements.total }} 个 · {{ stats.elements.pages }} 个页面
        </div>
        <div class="dashboard__stats-grid">
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
              <component :is="item.icon" :size="15" />
            </template>
          </StatsAppCard>
        </div>
      </section>

      <!-- 趋势图表 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          <IconTrendingUp :size="19" />
          趋势数据
          <span class="doc-tag">Trends</span>
        </h3>
        <div class="doc-section__label">
          近 12 期执行、AI Token 与费用趋势
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
        <div class="dashboard__trends dashboard__trends--ai">
          <el-card class="trends-chart-card">
            <div class="trends-tasks-card__title">每日 Token 用量</div>
            <SeriesBarChart :labels="aiTokenChart.labels" :series="tokenSeries" />
          </el-card>
          <el-card class="trends-chart-card">
            <div class="trends-tasks-card__title">每日 DeepSeek 费用（元）</div>
            <SeriesBarChart :labels="deepseekCostChart.labels" :series="costSeries" />
          </el-card>
        </div>
      </section>

      <!-- 最近动态 -->
      <section class="doc-section">
        <h3 class="doc-section__title">
          <IconActivity :size="19" />
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
