<script setup lang="ts">
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import FilterTabs from "@/shared/components/FilterTabs.vue"
import KpiCard from "@/shared/components/KpiCard.vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import { useReportInventory } from "./composables/useReportInventory"
import { useOpenReport } from "./composables/useOpenReport"
import {
  EMPTY_TEXT,
  KEYWORD_PLACEHOLDER,
  PAGE_HEADER,
  TABLE_COLUMNS,
  sopStatusClass,
  sopStatusLabel,
  sourceClass,
  sourceLabel,
} from "./constants"
import {
  formatReportTime,
  identitySub,
  identityTitle,
  outcomeText,
  relationLabel,
  reportMoment,
  reportRowKey,
} from "./helpers/report-row"
import type { ReportRow } from "./types"

const {
  total,
  summary,
  loading,
  error,
  source,
  keyword,
  dateRange,
  sourceTabs,
  PAGE_SIZE_OPTIONS,
  pageSize,
  currentPage,
  totalPages,
  pagedItems,
  setPageSize,
  goPage,
  load,
} = useReportInventory()

const { openReport } = useOpenReport()
const columns = TABLE_COLUMNS

function onRowClick(row: ReportRow) {
  openReport(row)
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell report-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    />

    <div class="doc-body">
      <section class="doc-section report-stats">
        <div class="doc-section__header">
          <h3 class="doc-section__title">报告概览 <span class="doc-tag">Overview</span></h3>
          <span class="doc-section__label">统计已生成的报告数量，执行完成后自动入列</span>
        </div>
        <div class="kpi-row">
          <KpiCard
            :value="summary.total_reports"
            label="报告总数"
            color="var(--c-report)"
            shape="diamond"
            :clickable="false"
          />
          <KpiCard
            :value="summary.sop_reports"
            label="SOP 报告"
            color="var(--c-ai)"
            shape="square"
            :clickable="false"
          />
          <KpiCard
            :value="summary.agent_reports"
            label="智能体报告"
            color="var(--c-case)"
            shape="triangle"
            :clickable="false"
          />
        </div>
      </section>

      <section class="doc-section report-table-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">测试报告 <span class="doc-tag">Reports</span></h3>
          <span class="doc-section__label"
            >SOP 报告带用例与任务编号；智能体报告带助手编号与名称</span
          >
        </div>

        <div class="filter-bar sketch-kit">
          <FilterTabs class="report-source-tabs" :tabs="sourceTabs" v-model="source" />
          <div class="sketch-field report-field">
            <el-input
              v-model="keyword"
              :placeholder="KEYWORD_PLACEHOLDER"
              clearable
              class="report-filter-input"
            />
          </div>
          <div class="sketch-field report-field report-field--date">
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              value-format="YYYY-MM-DD"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              class="report-filter-date"
            />
          </div>
        </div>

        <ErrorState v-if="error && !loading" :message="error" @retry="load" />

        <div class="table-toolbar sketch-kit">
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
          <span class="page-info">
            第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ total }} 条
          </span>
          <div class="page-nav report-page-nav">
            <DoodleBtn tone="paper" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">
              上一页
            </DoodleBtn>
            <DoodleBtn
              tone="paper"
              :disabled="currentPage >= totalPages"
              @click="goPage(currentPage + 1)"
            >
              下一页
            </DoodleBtn>
          </div>
        </div>

        <AppTable
          :columns="columns"
          :data-source="pagedItems"
          :row-key="reportRowKey"
          :loading="loading"
          table-layout="fixed"
          :empty-text="EMPTY_TEXT.noData"
          accent="var(--c-report)"
          class="report-table"
          @row-click="onRowClick"
        >
          <template
            v-for="col in columns"
            :key="`head-${col.dataIndex}`"
            v-slot:[`header-${col.dataIndex}`]
          >
            <span class="th-ico" aria-hidden="true">{{ col.icon }}</span
            >{{ col.title }}
          </template>

          <template #cell-source="{ record }">
            <span class="report-source" :class="sourceClass(record.source)">
              {{ sourceLabel(record.source) }}
            </span>
          </template>

          <template #cell-identity="{ record }">
            <span class="report-identity">
              <span class="report-identity__title">{{ identityTitle(record) }}</span>
              <span class="report-identity__sub">{{ identitySub(record) }}</span>
            </span>
          </template>

          <template #cell-relation="{ record }">
            <span class="report-relation">{{ relationLabel(record) }}</span>
          </template>

          <template #cell-outcome="{ record }">
            <span
              v-if="record.source === 'sop'"
              class="report-status"
              :class="sopStatusClass(record.status)"
            >
              {{ sopStatusLabel(record.status) }}
            </span>
            <span class="report-outcome">{{ outcomeText(record) }}</span>
          </template>

          <template #cell-moment="{ record }">
            <span class="report-moment">{{ formatReportTime(reportMoment(record)) }}</span>
          </template>

          <template #cell-actions="{ record }">
            <DoodleBtn tone="paper" @click.stop="openReport(record)">查看报告</DoodleBtn>
          </template>

          <template #empty>
            <EmptyState icon="📈" :text="EMPTY_TEXT.noData" :hint="EMPTY_TEXT.hint" />
          </template>
        </AppTable>
      </section>
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
