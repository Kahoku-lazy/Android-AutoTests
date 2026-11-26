<script setup lang="ts">
import { computed, ref } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import { KS_EVAL_EXPLAINER, KS_EVAL_PHASE_TEXT, KS_EVAL_SYNTHETIC_LABEL } from "../constants"
import { formatPercent } from "../helpers/estimate"
import type { EvalQuery, EvalRunDetail } from "../types"
import HitCard from "./HitCard.vue"

const props = defineProps<{ detail: EvalRunDetail }>()

const selected = ref<EvalQuery | null>(null)
const showExplainer = ref(false)

const isRunning = computed(
  () => props.detail.status === "pending" || props.detail.status === "running",
)
const phaseText = computed(() => {
  const base = KS_EVAL_PHASE_TEXT[props.detail.phase] ?? KS_EVAL_PHASE_TEXT.retrieving
  if (props.detail.phase === "retrieving" || !KS_EVAL_PHASE_TEXT[props.detail.phase]) {
    return `${base} ${props.detail.progress_done} / ${props.detail.progress_total}`
  }
  return base
})
const progressPercent = computed(() => {
  const total = props.detail.progress_total
  return total > 0 ? Math.round((props.detail.progress_done / total) * 100) : 0
})

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
  { key: "question", label: "问题（点击查看命中）", minWidth: 220 },
  { key: "gold_source", label: "正确文档", width: 150 },
  { key: "rank", label: "排名", width: 70 },
  { key: "is_hit", label: "命中", width: 70 },
]

function onSelect(row: EvalQuery) {
  selected.value = row
}
</script>

<template>
  <div class="ks-report">
    <ErrorState v-if="detail.status === 'failed'" :message="detail.error || '评测失败'" />
    <template v-else>
      <div v-if="isRunning" class="ks-report__progress">
        <span class="ks-report__phase">{{ phaseText }}</span>
        <div class="ks-report__bar">
          <div class="ks-report__bar-fill" :style="{ width: `${progressPercent}%` }" />
        </div>
      </div>

      <template v-if="detail.status === 'done'">
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
      </template>

      <AppTable
        v-if="detail.queries.length > 0"
        :columns="columns"
        :data-source="detail.queries"
        row-key="id"
        accent="var(--c-case)"
        @row-click="onSelect"
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
      <p v-else-if="isRunning" class="ks-report__waiting">题目生成后逐题出现在这里。</p>

      <div v-if="selected" class="ks-report__detail">
        <div class="ks-report__detail-head">
          <span class="ks-report__detail-question">{{ selected.question }}</span>
          <DoodleBtn @click="selected = null">收起</DoodleBtn>
        </div>
        <p class="ks-report__detail-meta">
          {{ selected.kind === "positive" ? "正题" : "负样本" }}
          <template v-if="selected.gold_source"> · 正确文档：{{ selected.gold_source }}</template>
          · 排名：{{ selected.rank ?? "未命中" }}
        </p>
        <p v-if="selected.source_text" class="ks-report__chunk">
          来源片段：{{ selected.source_text }}
        </p>
        <div v-if="selected.hits.length > 0" class="ks-report__hits">
          <HitCard
            v-for="hit in selected.hits"
            :key="`${hit.document_id}:${hit.chunk_index}`"
            :hit="hit"
          />
        </div>
        <EmptyState v-else icon="🔍" text="该题没有命中" />
      </div>

      <div class="ks-report__explainer">
        <DoodleBtn @click="showExplainer = !showExplainer">评测原理与判断依据</DoodleBtn>
        <div v-if="showExplainer" class="ks-report__explainer-body">
          <section v-for="item in KS_EVAL_EXPLAINER" :key="item.title">
            <h4 class="ks-report__explainer-title">{{ item.title }}</h4>
            <p class="ks-report__explainer-text">{{ item.body }}</p>
          </section>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ks-report {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.ks-report__progress {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-xs);
}

.ks-report__phase {
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-primary);
}

.ks-report__bar {
  height: 8px;
  border: 1px solid color-mix(in srgb, var(--ink) 24%, transparent);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  overflow: hidden;
}

.ks-report__bar-fill {
  height: 100%;
  background: var(--c-case);
  transition: width var(--app-duration-fast) var(--app-ease);
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

.ks-report__waiting {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ks-report__detail {
  border: 1px solid var(--c-case);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  padding: var(--app-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.ks-report__detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-md);
}

.ks-report__detail-question {
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
}

.ks-report__detail-meta {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ks-report__chunk {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  border-left: 2px solid var(--c-case);
  padding-left: var(--app-space-sm);
}

.ks-report__hits {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.ks-report__explainer {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  align-items: flex-start;
}

.ks-report__explainer-body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.ks-report__explainer-title {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
}

.ks-report__explainer-text {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

@media (prefers-reduced-motion: reduce) {
  .ks-report__bar-fill {
    transition: none;
  }
}
</style>
