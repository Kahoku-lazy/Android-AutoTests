<script setup>
import { computed } from "vue"
import { useECharts } from "@/shared/composables/useECharts"
import { buildDistributionOption } from "../helpers/bugDistribution"

const props = defineProps({
  summary: { type: Object, required: true },
})

const option = computed(() => buildDistributionOption(props.summary))
const { container } = useECharts(
  () => option.value,
  () => props.summary,
)
</script>

<template>
  <div
    ref="container"
    class="bug-distribution-chart"
    role="img"
    aria-label="BUG 状态与类型分布图"
  ></div>
</template>

<style scoped>
.bug-distribution-chart {
  width: 100%;
  height: 260px;
}
</style>
