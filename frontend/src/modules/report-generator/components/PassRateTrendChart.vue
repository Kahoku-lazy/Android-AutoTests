<script setup>
import { ref, watch, onMounted, onUnmounted, nextTick, computed } from "vue";
import * as echarts from "echarts";
import { CHART_COLORS, CHART_VISIBLE_DAYS } from "../constants.js";

const props = defineProps({
  labels: { type: Array, default: () => [] },
  rate: { type: Array, default: () => [] },
  visibleDays: { type: Number, default: CHART_VISIBLE_DAYS },
  group: { type: String, default: "report-trend" },
});

const container = ref(null);
let instance = null;
let resizeObserver = null;

const zoomStart = computed(() => {
  const n = props.labels.length;
  if (n <= props.visibleDays) return 0;
  return ((n - props.visibleDays) / n) * 100;
});

function buildOption() {
  const colors = CHART_COLORS.passRate;
  return {
    animation: true,
    animationDuration: 700,
    animationEasing: "cubicOut",
    animationDurationUpdate: 400,
    tooltip: {
      trigger: "axis",
      valueFormatter: (v) => `${v}%`,
      textStyle: { fontSize: 12 },
    },
    grid: { top: 16, right: 12, bottom: 52, left: 40 },
    dataZoom: [
      {
        type: "slider",
        start: zoomStart.value,
        end: 100,
        height: 16,
        bottom: 4,
        borderColor: "rgba(121,79,39,0.15)",
        fillerColor: "rgba(25,200,185,0.18)",
        handleStyle: { color: "#19c8b9" },
        textStyle: { fontSize: 10, color: "#9f927d" },
      },
      { type: "inside", start: zoomStart.value, end: 100 },
    ],
    xAxis: {
      type: "category",
      data: props.labels,
      boundaryGap: false,
      axisLine: { lineStyle: { color: "rgba(121,79,39,0.15)" } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: "#9f927d", fontWeight: 600 },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: {
        fontSize: 10,
        color: "#9f927d",
        formatter: "{value}%",
      },
      splitLine: { lineStyle: { color: "rgba(121,79,39,0.08)" } },
    },
    series: [
      {
        name: "通过率",
        type: "line",
        data: props.rate,
        smooth: 0.3,
        symbol: "circle",
        symbolSize: 8,
        showSymbol: true,
        lineStyle: { width: 2.5, color: colors.line },
        itemStyle: {
          color: colors.point,
          borderColor: colors.pointBorder,
          borderWidth: 2,
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(25,200,185,0.28)" },
            { offset: 1, color: "rgba(25,200,185,0.02)" },
          ]),
        },
      },
    ],
  };
}

function renderChart() {
  if (!instance) return;
  instance.setOption(buildOption());
}

function initChart() {
  if (!container.value) return;
  instance = echarts.init(container.value);
  instance.group = props.group;
  echarts.connect(props.group);
  renderChart();
  resizeObserver = new ResizeObserver(() => instance?.resize());
  resizeObserver.observe(container.value);
}

onMounted(() => nextTick(initChart));
watch(
  () => [props.labels, props.rate, props.visibleDays],
  () => nextTick(renderChart),
  { deep: true },
);
onUnmounted(() => {
  resizeObserver?.disconnect();
  instance?.dispose();
  instance = null;
});
</script>

<template>
  <div ref="container" class="echart-host" />
</template>

<style scoped>
.echart-host {
  width: 100%;
  height: 220px;
}
</style>
