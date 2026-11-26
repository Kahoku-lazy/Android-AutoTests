<script setup lang="ts">
import { computed } from "vue"
import TaskCountBars from "./TaskCountBars.vue"
import { resultBarCards } from "../helpers/task-stats"
import type { TaskStats } from "@/shared/types/ai"

const props = defineProps<{
  stats: TaskStats | null
}>()

const cards = computed(() => resultBarCards(props.stats))

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
