<script setup lang="ts">
/**
 * TaskStatsStrip — 任务清单页的三项统计（总任务 / 成功率 / 执行中）。
 *
 * 数据来自后端统计接口（列表只返回最近 100 条，前端不能自行求和）；
 * 加载中且没有旧值时用共享骨架，不渲染 0 值假数据。
 */
import KpiCard from "@/shared/components/KpiCard.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { successRateText } from "../helpers/task-stats"
import type { TaskStats } from "@/shared/types/ai"

defineProps<{
  stats: TaskStats | null
  loading: boolean
}>()

/** 三张卡的微倾角：按序号轮转，悬停回正 */
const TILTS = [-0.8, 0.6, -0.5]
</script>

<template>
  <div class="task-stats">
    <template v-if="loading && !stats">
      <SkeletonCard v-for="index in 3" :key="index" />
    </template>
    <template v-else>
      <KpiCard
        label="总任务"
        :value="stats?.total ?? 0"
        shape="square"
        color="var(--c-ai)"
        :tilt="TILTS[0]"
        :clickable="false"
      >
        <p class="task-stats__note">含执行中与待执行</p>
      </KpiCard>
      <KpiCard
        label="成功率"
        :value="successRateText(stats)"
        shape="circle"
        color="var(--c-device)"
        :tilt="TILTS[1]"
        :clickable="false"
      >
        <p class="task-stats__note">
          成功 {{ stats?.success ?? 0 }} / 已结束 {{ stats?.finished ?? 0 }}
        </p>
      </KpiCard>
      <KpiCard
        label="执行中"
        :value="stats?.running ?? 0"
        shape="triangle"
        color="var(--c-workflow)"
        :tilt="TILTS[2]"
        :clickable="false"
      >
        <p class="task-stats__note">待执行 {{ stats?.pending ?? 0 }} 条</p>
      </KpiCard>
    </template>
  </div>
</template>

<style scoped>
.task-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: var(--app-space-lg);
  padding: var(--app-space-sm) var(--app-space-xs) var(--app-space-md);
  align-items: stretch;
}
.task-stats__note {
  margin: var(--app-space-xs) 0 0;
  font-size: var(--app-size-xs);
  line-height: var(--app-line-height-tight);
  color: var(--app-text-secondary);
}
</style>
