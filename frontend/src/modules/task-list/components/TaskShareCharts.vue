<script setup lang="ts">
/**
 * TaskShareCharts — 任务结果占比右侧的柱状图组。
 *
 * 第一张是总体「结果数量」，之后每个可见智能体一张（来自统计接口的 agents）。
 * 新增智能体后自动多一张，不需要改这个组件。
 */
import { computed } from "vue"
import TaskCountBars from "./TaskCountBars.vue"
import { resultBarCards } from "../helpers/task-stats"
import type { TaskStats } from "@/shared/types/ai"

const props = defineProps<{
  stats: TaskStats | null
}>()

const cards = computed(() => resultBarCards(props.stats))

/** 卡片微倾按序号轮转，悬停回正由 AppCard 自己处理 */
const TILTS = [0.5, -0.6, 0.4]
</script>

<template>
  <div class="share-charts">
    <TaskCountBars
      v-for="(card, index) in cards"
      :key="card.key"
      :title="card.title"
      :caption="card.caption"
      :items="card.items"
      :tilt="TILTS[index % TILTS.length]"
    />
  </div>
</template>

<style scoped>
.share-charts {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(176px, 1fr));
  gap: var(--app-space-md);
  align-items: stretch;
}
</style>
