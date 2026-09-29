<template>
  <div class="tb-cat-head">
    <div>
      <h3 class="tb-cat-title">{{ source.name }}</h3>
      <p class="tb-cat-sub">{{ source.desc }} · 判定与只读日志查询共用这张表</p>
    </div>
    <div class="tb-cat-actions">
      <button type="button" class="tb-btn" :disabled="loading" @click="load">
        {{ loading ? "刷新中…" : "刷新" }}
      </button>
    </div>
  </div>

  <div class="tb-cat-body" data-testid="log-keyword-panel">
    <ErrorState v-if="loadError" :message="loadError" @retry="load" />
    <SkeletonCard v-else-if="loading && !catalog" variant="list" :lines="4" />
    <EmptyState
      v-else-if="!rows.length"
      icon="🔑"
      :text="LOG_KEYWORD_EMPTY_TEXT"
      :hint="emptyNote || LOG_KEYWORD_EMPTY_HINT"
    />
    <template v-else>
      <div class="lk-bar">
        <input
          v-model="query"
          type="search"
          class="lk-search"
          :placeholder="LOG_KEYWORD_SEARCH_PLACEHOLDER"
          data-testid="log-keyword-search"
        />
        <span class="lk-count" data-testid="log-keyword-count">
          {{ counts.keywords }} 个关键词 · {{ counts.features }} 个功能点 · {{ rows.length }} 行
        </span>
      </div>

      <p class="lk-origin" data-testid="log-keyword-origin">
        取值来源：{{ originText }}
        <span v-if="catalog?.updated_at" class="lk-origin-dim">
          · 表文件更新于 {{ catalog.updated_at }}
        </span>
        <span class="lk-origin-dim">· {{ LOG_KEYWORD_RESTART_HINT }}</span>
      </p>

      <AppTable
        :columns="COLUMNS"
        :data-source="filteredRows"
        row-key="key"
        accent="var(--c-ai)"
        :empty-text="LOG_KEYWORD_NO_MATCH_TEXT"
        data-testid="log-keyword-table"
      >
        <template #cell-keyword="{ record }">
          <span class="lk-keyword">{{ record.keyword }}</span>
        </template>
        <template #cell-module="{ record }">
          <span class="lk-module">{{ record.module }}</span>
        </template>
        <template #cell-feature="{ record }">
          <span v-if="record.featureId !== undefined" class="lk-feature-id"
            >#{{ record.featureId }}</span
          >
          <span class="lk-feature-name">{{ record.featureName }}</span>
        </template>
      </AppTable>
    </template>
  </div>
</template>

<script setup lang="ts">
/** LogKeywordPanel — 工具箱「日志关键词」来源区：只读表格（关键词 / 功能模块 / 功能点）+ 搜索 */
import { computed, onMounted } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { useLogKeywords } from "../composables/useLogKeywords"
import { sourceDef } from "../helpers/toolbox-assembly"
import {
  LOG_KEYWORD_COL_FEATURE,
  LOG_KEYWORD_COL_KEYWORD,
  LOG_KEYWORD_COL_MODULE,
  LOG_KEYWORD_EMPTY_HINT,
  LOG_KEYWORD_EMPTY_TEXT,
  LOG_KEYWORD_NO_MATCH_TEXT,
  LOG_KEYWORD_ORIGIN_LABELS,
  LOG_KEYWORD_RESTART_HINT,
  LOG_KEYWORD_SEARCH_PLACEHOLDER,
} from "../constants"

const source = sourceDef("keywords")

/** 三列：一行一个「关键词 × 功能点」（一个关键词对应多个功能点就是多行） */
const COLUMNS = [
  { dataIndex: "keyword", label: LOG_KEYWORD_COL_KEYWORD, width: 300 },
  { dataIndex: "module", label: LOG_KEYWORD_COL_MODULE, width: 160 },
  { dataIndex: "feature", label: LOG_KEYWORD_COL_FEATURE, minWidth: 240 },
]

const {
  catalog,
  loading,
  loadError,
  query,
  rows,
  filteredRows,
  counts,
  emptyNote,
  load,
  ensureLoaded,
} = useLogKeywords()

const originText = computed(
  () =>
    LOG_KEYWORD_ORIGIN_LABELS[catalog.value?.origin || "none"] || LOG_KEYWORD_ORIGIN_LABELS.none,
)

onMounted(() => {
  void ensureLoaded()
})
</script>

<style src="./LogKeywordPanel.style.css" scoped></style>
