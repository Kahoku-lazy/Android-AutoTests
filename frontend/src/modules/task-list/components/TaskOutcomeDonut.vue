<script setup lang="ts">
import { computed } from "vue"
import AppCard from "@/shared/components/AppCard.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import { useECharts } from "@/shared/composables/useECharts"
import { hasOutcomeData, outcomeSlices } from "../helpers/task-stats"
import type { TaskStats } from "@/shared/types/ai"

const props = defineProps<{
  stats: TaskStats | null
}>()

const slices = computed(() => outcomeSlices(props.stats))
const drawable = computed(() => hasOutcomeData(props.stats))

interface PieLabelParams {
  marker?: string
  name?: string
  value?: number
  percent?: number
}

function percentText(value: number): string {
  return Number.isInteger(value) ? `${value.toFixed(0)}%` : `${value.toFixed(1)}%`
}

function buildOption() {
  return {
    animation: true,
    animationDuration: 700,
    animationEasing: "cubicOut",
    tooltip: {
      trigger: "item",
      textStyle: { color: "#1e1e24" },
      formatter: (params: PieLabelParams) =>
        `${params.marker ?? ""}${params.name ?? ""}：${params.value ?? 0} 条（${percentText(
          params.percent ?? 0,
        )}）`,
    },
    series: [
      {
        type: "pie",
        radius: ["44%", "64%"],
        center: ["50%", "50%"],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: "#fffef5", borderWidth: 2 },

        label: {
          show: true,
          formatter: (params: PieLabelParams) => percentText(params.percent ?? 0),
          color: "#1e1e24",
          fontWeight: 700,
        },
        labelLine: {
          show: true,
          length: 8,
          length2: 8,
          lineStyle: { color: "#1e1e24" },
        },
        data: slices.value
          .filter((item) => item.value > 0)
          .map((item) => ({
            name: item.label,
            value: item.value,
            itemStyle: { color: item.color },
          })),
      },
    ],
  }
}

const { container } = useECharts(buildOption, () => [props.stats])
</script>

<template>
  <AppCard class="task-outcome" tone="var(--c-ai)" :tilt="-0.4">
    <div class="task-outcome__body">
      <ul class="task-outcome__legend">
        <li v-for="item in slices" :key="item.key" class="task-outcome__legend-row">
          <span class="task-outcome__dot" :style="{ background: item.color }" aria-hidden="true" />
          <span class="task-outcome__label">{{ item.label }}</span>
        </li>
      </ul>

      <div class="task-outcome__chart-wrap">
        <div v-show="drawable" ref="container" class="task-outcome__chart"></div>
        <EmptyState
          v-if="!drawable"
          icon="📊"
          text="还没有任务结果"
          hint="任务跑完后这里显示成功 / 失败 / 中断 / 取消的占比"
        />
      </div>
    </div>
  </AppCard>
</template>

<style scoped>
.task-outcome {
  width: 100%;
  height: 100%;
}
.task-outcome__body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  height: 100%;
  min-height: 0;
}

.task-outcome__legend {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--app-space-xs) var(--app-space-md);
}
.task-outcome__legend-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--app-size-sm);
  color: var(--app-text-primary);
}
.task-outcome__dot {
  width: 12px;
  height: 12px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 1.5px solid var(--ink);
}
.task-outcome__label {
  font-weight: var(--app-font-weight-bold);
}
.task-outcome__chart-wrap {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 190px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.task-outcome__chart {
  width: 100%;
  height: 100%;
  min-height: 190px;
}
</style>
