<script setup lang="ts">
/**
 * TaskCountBars — 一张小柱状图卡（四根柱：成功 / 失败 / 中断 / 取消）。
 *
 * 只负责渲染：标题、副标题与四类数据由父级按「总体」或「某个智能体」给出，
 * 新增智能体时父级多渲染一张，本组件不需要知道有多少智能体。
 */
import AppCard from "@/shared/components/AppCard.vue"
import { useECharts } from "@/shared/composables/useECharts"
import type { OutcomeSlice } from "../helpers/task-stats"

const props = defineProps<{
  title: string
  caption: string
  items: OutcomeSlice[]
  tilt: number
}>()

interface BarLabelParams {
  value?: number
}

// ⚠️ ECharts 渲染在 Canvas 上，不支持 CSS 变量，此处保留色值字面量。
//    token 对照：#1e1e24=--ink · #e8ecf1=--app-border-light · #f0ede8=--app-border-lighter
//    #999=--app-text-secondary；柱色由 helpers/task-stats 按令牌同值给出。
function buildOption() {
  return {
    animation: true,
    animationDuration: 700,
    animationEasing: "cubicOut",
    grid: { top: 28, right: 8, bottom: 4, left: 4, containLabel: true },
    xAxis: {
      type: "category",
      data: props.items.map((item) => item.label),
      axisLine: { lineStyle: { color: "#e8ecf1" } },
      axisTick: { show: false },
      axisLabel: { color: "#999", fontWeight: 600, interval: 0 },
    },
    yAxis: {
      type: "value",
      minInterval: 1,
      splitLine: { lineStyle: { color: "#f0ede8" } },
      axisLabel: { color: "#999" },
    },
    series: [
      {
        type: "bar",
        barMaxWidth: 22,
        data: props.items.map((item) => ({
          value: item.value,
          itemStyle: { color: item.color, borderRadius: [4, 4, 0, 0] },
        })),
        label: {
          show: true,
          position: "top",
          color: "#1e1e24",
          fontWeight: 700,
          formatter: (params: BarLabelParams) => String(params.value ?? 0),
        },
      },
    ],
  }
}

const { container } = useECharts(buildOption, () => [props.items])
</script>

<template>
  <AppCard class="count-bars" tone="var(--c-ai)" :tilt="tilt">
    <h4 class="count-bars__title">{{ title }}</h4>
    <p class="count-bars__caption">{{ caption }}</p>
    <div ref="container" class="count-bars__chart"></div>
  </AppCard>
</template>

<style scoped>
.count-bars {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.count-bars__title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}
.count-bars__caption {
  margin: 2px 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  line-height: var(--app-line-height-tight);
  color: var(--app-text-secondary);
}
.count-bars__chart {
  width: 100%;
  flex: 1 1 auto;
  min-height: 120px;
}
</style>
