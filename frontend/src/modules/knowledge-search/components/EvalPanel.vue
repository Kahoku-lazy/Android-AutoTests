<script setup lang="ts">
/** EvalPanel — 右栏评测区：触发（超管）+ 运行列表 + 报告；轮询进度。 */
import { onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import AppCard from "@/shared/components/AppCard.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { useEvalRuns } from "../composables/useEvalRuns"
import {
  KS_EVAL_DONE,
  KS_EVAL_EMPTY,
  KS_EVAL_EMPTY_HINT,
  KS_EVAL_FAILED,
  KS_EVAL_PENDING,
  KS_EVAL_RUNNING,
  KS_EVAL_TITLE,
  KS_EVAL_TRIGGER,
} from "../constants"
import type { EvalTriggerPayload, KnowledgeModuleRow } from "../types"
import EvalReport from "./EvalReport.vue"
import EvalTriggerDialog from "./EvalTriggerDialog.vue"

defineProps<{ modules: KnowledgeModuleRow[]; canManage: boolean }>()

const { runs, loading, error, detail, load, selectRun, trigger } = useEvalRuns()
const dialogOpen = ref(false)

onMounted(() => void load())

function statusText(status: string): string {
  if (status === "done") return KS_EVAL_DONE
  if (status === "failed") return KS_EVAL_FAILED
  if (status === "running") return KS_EVAL_RUNNING
  return KS_EVAL_PENDING
}

async function onTrigger(payload: EvalTriggerPayload) {
  const result = await trigger(payload)
  if (result.ok) {
    dialogOpen.value = false
    ElMessage.success("评测已发起")
  } else {
    ElMessage.error(result.message)
  }
}
</script>

<template>
  <AppCard tone="var(--c-case)" :pin="false" :tilt="-0.3" class="ks-eval-panel">
    <template #header>
      <div class="ks-eval-panel__head">
        <span class="ks-eval-panel__title">{{ KS_EVAL_TITLE }}</span>
        <DoodleBtn v-if="canManage" tone="teal" @click="dialogOpen = true">
          {{ KS_EVAL_TRIGGER }}
        </DoodleBtn>
      </div>
    </template>

    <SkeletonCard v-if="loading" variant="list" :lines="3" />
    <ErrorState v-else-if="error" :message="error" @retry="load" />
    <EmptyState
      v-else-if="runs.length === 0"
      icon="🧪"
      :text="KS_EVAL_EMPTY"
      :hint="KS_EVAL_EMPTY_HINT"
    />
    <template v-else>
      <ul class="ks-eval-panel__runs">
        <li v-for="run in runs" :key="run.id">
          <button
            type="button"
            class="ks-eval-run"
            :class="{ 'is-active': detail?.id === run.id }"
            @click="selectRun(run.id)"
          >
            <span class="ks-eval-run__module">{{ run.module_name }}</span>
            <span class="ks-eval-run__status" :class="`is-${run.status}`">
              {{ statusText(run.status) }}
            </span>
            <span class="ks-eval-run__progress">
              {{ run.progress_done }} / {{ run.progress_total }}
            </span>
          </button>
        </li>
      </ul>
      <EvalReport v-if="detail" :detail="detail" />
    </template>
  </AppCard>

  <EvalTriggerDialog v-model="dialogOpen" :modules="modules" @trigger="onTrigger" />
</template>

<style scoped>
.ks-eval-panel__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-sm);
}

.ks-eval-panel__title {
  font-size: var(--app-size-md);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.ks-eval-panel__runs {
  list-style: none;
  margin: 0 0 var(--app-space-md);
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.ks-eval-run {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  width: 100%;
  border: 1px solid color-mix(in srgb, var(--ink) 10%, transparent);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  padding: var(--app-space-sm) var(--app-space-md);
  font-family: inherit;
  font-size: var(--app-size-sm);
  color: var(--app-text-primary);
  cursor: pointer;
}

.ks-eval-run.is-active {
  border-color: var(--c-case);
}

.ks-eval-run__module {
  font-weight: var(--app-font-weight-bold);
}

.ks-eval-run__status {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ks-eval-run__status.is-failed {
  color: var(--app-status-danger-text);
}

.ks-eval-run__progress {
  margin-left: auto;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
</style>
