<template>
  <div class="sl-cat-head">
    <div>
      <h3 class="sl-cat-title">{{ KEYWORDS_PANEL_TITLE }}</h3>
      <p class="sl-cat-sub">{{ KEYWORDS_PANEL_DESC }} · 判定与只读日志查询共用这张表</p>
    </div>
    <div class="sl-cat-actions">
      <button type="button" class="sl-btn" :disabled="loading" @click="load">
        {{ loading ? "刷新中…" : "刷新" }}
      </button>
    </div>
  </div>

  <div class="sl-cat-body sketch-kit" data-testid="log-keyword-panel">
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
        <el-input
          v-model="query"
          class="lk-search"
          :placeholder="LOG_KEYWORD_SEARCH_PLACEHOLDER"
          clearable
          data-testid="log-keyword-search"
        />
        <span class="lk-count" data-testid="log-keyword-count">
          {{ counts.keywords }} 个关键词 · {{ counts.features }} 个功能点 · {{ rows.length }} 行
        </span>
      </div>

      <AppTable
        :columns="COLUMNS"
        :data-source="filteredRows"
        row-key="key"
        accent="var(--c-device)"
        table-layout="fixed"
        :empty-text="LOG_KEYWORD_NO_MATCH_TEXT"
        data-testid="log-keyword-table"
      >
        <template
          v-for="col in COLUMNS"
          :key="`h-${col.dataIndex}`"
          v-slot:[`header-${col.dataIndex}`]
        >
          <span class="th-ico" aria-hidden="true">{{ col.icon }}</span
          >{{ col.title }}
        </template>
        <template #cell-keyword="{ record }">
          <div class="lk-id">
            <span class="lk-badge" :style="{ '--mod-color': moduleColorToken(record.module) }"
              >🔑</span
            >
            <strong
              class="lk-keyword"
              :style="{ '--mod-color': moduleColorToken(record.module) }"
              >{{ record.keyword }}</strong
            >
          </div>
        </template>
        <template #cell-module="{ record }">
          <span class="lk-module" :style="{ '--mod-color': moduleColorToken(record.module) }">{{
            record.module
          }}</span>
        </template>
        <template #cell-feature="{ record }">
          <span v-if="record.featureId !== undefined" class="lk-feature-id"
            >#{{ record.featureId }}</span
          >
          <span class="lk-feature-name">{{ record.featureName }}</span>
        </template>
      </AppTable>

      <div class="lk-hintbar" data-testid="log-keyword-origin">
        <span aria-hidden="true">ℹ️</span>
        <span>
          取值来源：{{ originText }}
          <span v-if="catalog?.updated_at" class="lk-origin-dim"
            >· 表文件更新于 {{ catalog.updated_at }}</span
          >
          <span class="lk-origin-dim">· {{ LOG_KEYWORD_RESTART_HINT }}</span>
        </span>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
/** LogKeywordPanel — 串口日志页「日志关键词」Tab：只读表格 + 手稿搜索框 */
import { computed, onMounted } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { useLogKeywords } from "../composables/useLogKeywords"
import { buildModuleColorMap, moduleColorOf } from "../helpers/log-keyword-colors"
import {
  KEYWORDS_PANEL_DESC,
  KEYWORDS_PANEL_TITLE,
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

/** 三列：一行一个「关键词 × 功能点」（一个关键词对应多个功能点就是多行）；功能点在左、关键词在右 */
const COLUMNS = [
  { dataIndex: "feature", title: LOG_KEYWORD_COL_FEATURE, icon: "◈", minWidth: 240 },
  { dataIndex: "module", title: LOG_KEYWORD_COL_MODULE, icon: "▣", width: 180 },
  { dataIndex: "keyword", title: LOG_KEYWORD_COL_KEYWORD, icon: "🔑", minWidth: 300 },
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

/** 模块配色按「全量行」的首次出现顺序分配：搜索过滤时已有配色不漂移 */
const moduleColors = computed(() => buildModuleColorMap(rows.value.map((row) => row.module)))
const moduleColorToken = (module: string): string => moduleColorOf(moduleColors.value, module)

const originText = computed(
  () =>
    LOG_KEYWORD_ORIGIN_LABELS[catalog.value?.origin || "none"] || LOG_KEYWORD_ORIGIN_LABELS.none,
)

onMounted(() => {
  void ensureLoaded()
})
</script>

<style src="./LogKeywordPanel.style.css" scoped></style>
