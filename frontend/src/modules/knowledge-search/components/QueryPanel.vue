<script setup lang="ts">
import { computed } from "vue"
import AppCard from "@/shared/components/AppCard.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import {
  KS_INDEX_HINT,
  KS_NO_HIT_HINT,
  KS_NO_HIT_TEXT,
  KS_QUESTION_PLACEHOLDER,
  KS_SELECT_HINT,
  KS_UNAVAILABLE_TEXT,
} from "../constants"
import { sortHits } from "../helpers/hits"
import { useKnowledgeQuery } from "../composables/useKnowledgeQuery"
import HitCard from "./HitCard.vue"

const props = defineProps<{ selectedNames: string[] }>()

const { question, loading, outcome, transportError, ask } = useKnowledgeQuery()

const canAsk = computed(
  () => question.value.trim().length > 0 && props.selectedNames.length > 0 && !loading.value,
)
const hits = computed(() => (outcome.value ? sortHits(outcome.value.hits) : []))
const unavailableMessage = computed(() => {
  const errors = outcome.value?.errors ?? []
  return errors.length > 0 ? `${KS_UNAVAILABLE_TEXT}：${errors.join("；")}` : KS_UNAVAILABLE_TEXT
})

function onAsk() {
  void ask(props.selectedNames)
}
</script>

<template>
  <AppCard tone="var(--c-case)" :pin="false" :tilt="-0.3" class="ks-query-panel">
    <template #header>
      <span class="ks-query-panel__title">提问</span>
    </template>

    <div class="ks-query-panel__form">
      <el-input
        v-model="question"
        type="textarea"
        :rows="3"
        :placeholder="KS_QUESTION_PLACEHOLDER"
        maxlength="500"
        show-word-limit
        @keydown.enter.exact.prevent="onAsk"
      />
      <div class="ks-query-panel__bar">
        <span class="ks-query-panel__hint">
          {{ selectedNames.length === 0 ? KS_SELECT_HINT : KS_INDEX_HINT }}
        </span>
        <DoodleBtn tone="teal" :disabled="!canAsk" @click="onAsk">检索</DoodleBtn>
      </div>
    </div>

    <div class="ks-query-panel__result">
      <SkeletonCard v-if="loading" variant="list" :lines="3" />
      <ErrorState v-else-if="transportError" :message="transportError" @retry="onAsk" />
      <template v-else-if="outcome">
        <ErrorState
          v-if="outcome.result === 'unavailable'"
          :message="unavailableMessage"
          @retry="onAsk"
        />
        <EmptyState
          v-else-if="outcome.result === 'no_hit'"
          icon="🔍"
          :text="KS_NO_HIT_TEXT"
          :hint="KS_NO_HIT_HINT"
        />
        <template v-else>
          <p class="ks-query-panel__count">命中 {{ hits.length }} 条（原文，未改写）</p>
          <p v-if="outcome.errors.length > 0" class="ks-query-panel__errors">
            部分模块不可用：{{ outcome.errors.join("；") }}
          </p>
          <div class="ks-query-panel__hits">
            <HitCard
              v-for="hit in hits"
              :key="`${hit.document_id}:${hit.chunk_index}`"
              :hit="hit"
            />
          </div>
        </template>
      </template>
      <EmptyState v-else icon="✍️" text="输入问题开始检索" :hint="KS_INDEX_HINT" />
    </div>
  </AppCard>
</template>

<style scoped>
.ks-query-panel__title {
  font-size: var(--app-size-md);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
}

.ks-query-panel__form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.ks-query-panel__bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--app-space-md);
}

.ks-query-panel__hint {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ks-query-panel__result {
  margin-top: var(--app-space-lg);
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.ks-query-panel__count {
  margin: 0;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-primary);
}

.ks-query-panel__errors {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-status-danger-text);
}

.ks-query-panel__hits {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}
</style>
