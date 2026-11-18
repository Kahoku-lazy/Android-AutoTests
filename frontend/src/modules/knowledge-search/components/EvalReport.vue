<script setup lang="ts">
/** EvalReport — 评测报告：指标卡 + 逐题明细表 + 合成集偏差标注。 */
import { computed } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import { KS_EVAL_SYNTHETIC_LABEL } from "../constants"
import { formatPercent } from "../helpers/estimate"
import type { EvalRunDetail } from "../types"

const props = defineProps<{ detail: EvalRunDetail }>()

const metrics = computed(() => props.detail.metrics)
const cards = computed(() => [
  {
    label: "Recall@1",
    value: formatPercent(metrics.value.recall_at_1 ?? 0),
    shape: "diamond" as const,
  },
  {
    label: "Recall@3",
    value: formatPercent(metrics.value.recall_at_3 ?? 0),
    shape: "triangle" as const,
  },
  {
    label: "Recall@5",
    value: formatPercent(metrics.value.recall_at_5 ?? 0),
    shape: "square" as const,
  },
  { label: "MRR", value: (metrics.value.mrr ?? 0).toFixed(3), shape: "circle" as const },
  {
    label: "误命中率",
    value: formatPercent(metrics.value.false_hit_rate ?? 0),
    shape: "diamond" as const,
  },
])

const columns = [
  { key: "kind", label: "类型", width: 80 },
  { key: "question", label: "问题", minWidth: 220 },
  { key: "gold_source", label: "正确文档", width: 150 },
  { key: "rank", label: "排名", width: 70 },
  { key: "is_hit", label: "命中", width: 70 },
]
</script>

<template>
  <div class="ks-report">
    <ErrorState v-if="detail.status === 'failed'" :message="detail.error || '评测失败'" />
    <template v-else-if="detail.status === 'done'">
      <p class="ks-report__label">
        {{ KS_EVAL_SYNTHETIC_LABEL }} · 正题 {{ metrics.n_pos ?? 0 }} 条 / 负样本
        {{ metrics.n_neg ?? 0 }} 条 · 模型 {{ detail.model_snapshot.model_name }}
      </p>
      <div class="ks-report__cards">
        <KpiCard
          v-for="card in cards"
          :key="card.label"
          :label="card.label"
          :value="card.value"
          :shape="card.shape"
          color="var(--c-case)"
          :clickable="false"
          deco="none"
        />
      </div>
      <AppTable
        :columns="columns"
        :data-source="detail.queries"
        row-key="id"
        accent="var(--c-case)"
      >
        <template #cell-kind="{ record }">
          {{ record.kind === "positive" ? "正题" : "负样本" }}
        </template>
        <template #cell-gold_source="{ record }">
          {{ record.gold_source || "—" }}
        </template>
        <template #cell-rank="{ record }">
          {{ record.rank ?? "—" }}
        </template>
        <template #cell-is_hit="{ record }">
          {{ record.is_hit ? "是" : "否" }}
        </template>
      </AppTable>
    </template>
    <p v-else class="ks-report__progress">
      评测进行中：{{ detail.progress_done }} / {{ detail.progress_total }} 题
    </p>
  </div>
</template>

<style scoped>
.ks-report {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.ks-report__label {
  margin: 0;
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-secondary);
}

.ks-report__cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: var(--app-space-md);
}

.ks-report__progress {
  margin: 0;
  font-size: var(--app-size-sm);
  color: var(--app-text-primary);
}
</style>
