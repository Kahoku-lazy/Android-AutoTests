<script setup lang="ts">
import { ref } from "vue"
import { ElMessage } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import FilterTabs from "@/shared/components/FilterTabs.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import BugDetailDrawer from "./components/BugDetailDrawer.vue"
import { getBug, updateBugStatus } from "./api"
import { useBugList } from "./composables/useBugList"
import {
  BUG_EMPTY_TEXT,
  BUG_KEYWORD_PLACEHOLDER,
  BUG_PAGE_HEADER,
  BUG_STATUS_OPTIONS,
  BUG_STATUS_PLACEHOLDER,
  BUG_SYNC,
  BUG_TABLE_COLUMNS,
  bugCategoryClass,
  bugStatusClass,
  bugTaskRoute,
  formatBugTime,
} from "./constants"
import type { BugStatus, BugTicket } from "./types"

const {
  summary,
  total,
  loading,
  syncing,
  error,
  category,
  status,
  keyword,
  categoryTabs,
  PAGE_SIZE_OPTIONS,
  pageSize,
  currentPage,
  totalPages,
  pagedItems,
  setPageSize,
  goPage,
  load,
  sync,
} = useBugList()

const columns = BUG_TABLE_COLUMNS
const drawerOpen = ref(false)
const selected = ref<BugTicket | null>(null)
const detailLoading = ref(false)
const updating = ref(false)

async function openDetail(row: BugTicket) {
  selected.value = row
  drawerOpen.value = true
  detailLoading.value = true
  try {
    const { data } = await getBug(row.id)
    if (data.status && data.data) selected.value = data.data
    else ElMessage.error(data.message || "加载 BUG 详情失败")
  } catch (e) {
    ElMessage.error(errorMessage(e, "加载 BUG 详情失败"))
  } finally {
    detailLoading.value = false
  }
}

async function changeStatus(next: BugStatus) {
  if (!selected.value) return
  updating.value = true
  try {
    const { data } = await updateBugStatus(selected.value.id, next)
    if (!data.status || !data.data) throw new Error(data.message || "更新 BUG 状态失败")
    selected.value = data.data
    await load()
    ElMessage.success(`已更新为「${data.data.status_label}」`)
  } catch (e) {
    ElMessage.error(errorMessage(e, "更新 BUG 状态失败"))
  } finally {
    updating.value = false
  }
}

function errorMessage(error: unknown, fallback: string): string {
  if (error && typeof error === "object") {
    const response = (error as { response?: { data?: { message?: string } } }).response
    if (response?.data?.message) return response.data.message
    const message = (error as { message?: string }).message
    if (message) return message
  }
  return fallback
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell bug-workbench">
    <WorkbenchHeader
      :title="BUG_PAGE_HEADER.title"
      :subtitle="BUG_PAGE_HEADER.subtitle"
      :icon="BUG_PAGE_HEADER.icon"
      :icon-gradient="BUG_PAGE_HEADER.iconGradient"
    />

    <div class="doc-body">
      <section class="doc-section bug-stats">
        <div class="doc-section__header">
          <h3 class="doc-section__title">BUG 概览 <span class="doc-tag">Overview</span></h3>
          <span class="doc-section__label">按任务类型分开统计，处理状态实时更新</span>
        </div>
        <div class="kpi-row">
          <KpiCard
            :value="summary.total"
            label="全部 BUG"
            color="var(--c-report)"
            shape="diamond"
            :clickable="false"
          />
          <KpiCard
            :value="summary.ui_automation"
            label="UI 自动化"
            color="var(--c-ai)"
            shape="square"
            :clickable="false"
          />
          <KpiCard
            :value="summary.case_authoring"
            label="测试用例编写"
            color="var(--c-case)"
            shape="triangle"
            :clickable="false"
          />
          <KpiCard
            :value="summary.open"
            label="待处理"
            color="var(--c-runner)"
            shape="circle"
            :clickable="false"
          />
        </div>
      </section>

      <section class="doc-section bug-table-section">
        <div class="doc-section__header bug-table-section__header">
          <h3 class="doc-section__title">BUG 单 <span class="doc-tag">Tickets</span></h3>
          <FilterTabs :tabs="categoryTabs" v-model="category" />
        </div>

        <div class="filter-bar">
          <el-input
            v-model="keyword"
            :placeholder="BUG_KEYWORD_PLACEHOLDER"
            clearable
            class="bug-filter-input"
          />
          <el-select
            v-model="status"
            :placeholder="BUG_STATUS_PLACEHOLDER"
            clearable
            class="bug-filter-status"
          >
            <el-option
              v-for="option in BUG_STATUS_OPTIONS"
              :key="option.value"
              :label="option.label"
              :value="option.value"
            />
          </el-select>
          <DoodleBtn tone="yellow" :disabled="syncing" @click="sync">
            {{ syncing ? BUG_SYNC.running : "同步历史错误" }}
          </DoodleBtn>
          <span class="filter-hint">共 {{ total }} 张 BUG 单</span>
        </div>

        <ErrorState v-if="error && !loading" :message="error" @retry="load" />

        <div class="table-toolbar">
          <span class="toolbar-label">显示行数</span>
          <div class="page-size-btns">
            <button
              v-for="size in PAGE_SIZE_OPTIONS"
              :key="size"
              type="button"
              class="page-size-btn"
              :class="{ active: pageSize === size }"
              @click="setPageSize(size)"
            >
              {{ size }}
            </button>
          </div>
          <span v-if="pagedItems.length" class="page-info">
            第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ total }} 条
          </span>
          <div v-if="totalPages > 1" class="page-nav">
            <button
              type="button"
              class="page-nav-btn"
              :disabled="currentPage <= 1"
              @click="goPage(currentPage - 1)"
            >
              上一页
            </button>
            <button
              type="button"
              class="page-nav-btn"
              :disabled="currentPage >= totalPages"
              @click="goPage(currentPage + 1)"
            >
              下一页
            </button>
          </div>
        </div>

        <AppTable
          :columns="columns"
          :data-source="pagedItems"
          row-key="id"
          :border="true"
          :loading="loading"
          :empty-text="BUG_EMPTY_TEXT.noData"
          accent="var(--c-runner)"
          class="bug-table"
          @row-click="openDetail"
        >
          <template #cell-bug_no="{ record }">
            <code class="bug-no">{{ record.bug_no }}</code>
          </template>

          <template #cell-category="{ record }">
            <span class="bug-badge" :class="bugCategoryClass(record.category)">
              {{ record.category_label }}
            </span>
          </template>

          <template #cell-title="{ record }">
            <span class="bug-title">{{ record.title || "—" }}</span>
          </template>

          <template #cell-task_id="{ record }">
            <router-link :to="bugTaskRoute(record.task_id)" class="bug-task-link" @click.stop>
              #{{ record.task_id }}
            </router-link>
          </template>

          <template #cell-status="{ record }">
            <span class="bug-status" :class="bugStatusClass(record.status)">
              {{ record.status_label }}
            </span>
          </template>

          <template #cell-created_at="{ value }">
            <span class="bug-time">{{ formatBugTime(value) }}</span>
          </template>

          <template #cell-actions="{ record }">
            <DoodleBtn tone="paper" @click.stop="openDetail(record)">查看</DoodleBtn>
          </template>

          <template #empty>
            <EmptyState icon="🐞" :text="BUG_EMPTY_TEXT.noData" :hint="BUG_EMPTY_TEXT.hint" />
          </template>
        </AppTable>
      </section>
    </div>

    <BugDetailDrawer
      v-model="drawerOpen"
      :bug="selected"
      :loading="detailLoading"
      :updating="updating"
      @status-change="changeStatus"
    />
  </div>
</template>

<style src="./index.style.css" scoped></style>
