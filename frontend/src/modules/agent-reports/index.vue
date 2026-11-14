<script setup lang="ts">
/**
 * 执行报告 — 平台 UI 执行智能体每次运行产出的 HTML 报告历史。
 *
 * 只做两件事：列报告、按需取正文并用新窗口打开。报告正文是完整 HTML，
 * 以 blob URL 打开，避免把报告样式注入当前页面。
 */
import { onMounted, ref } from "vue"
import { ElMessage } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import DoodleNote from "@/shared/components/DoodleNote.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { getApiErrorMessage } from "@/shared/types/api-error"
import { fetchAgentReport, fetchAgentReports } from "./api"
import type { AgentReportRow } from "./types"
import { formatBytes, formatRunTime, runStamp, tiltFor } from "./helpers/report-meta"
import {
  REPORTS_EMPTY_HINT,
  REPORTS_EMPTY_TEXT,
  REPORTS_ERROR_TEXT,
  REPORTS_LIMIT,
  REPORTS_LOADING_LABEL,
  REPORTS_OPEN_ERROR_TEXT,
  REPORTS_OPEN_LABEL,
  REPORTS_PAGE_GRADIENT,
  REPORTS_PAGE_ICON,
  REPORTS_PAGE_SUBTITLE,
  REPORTS_PAGE_TITLE,
  REPORTS_REFRESH_LABEL,
} from "./constants"

const rows = ref<AgentReportRow[]>([])
const loading = ref(false)
const error = ref("")
const openingRun = ref("")

/** 拉最近报告；失败只置错误态，不抛给页面。 */
async function load() {
  loading.value = true
  error.value = ""
  try {
    const response = await fetchAgentReports(REPORTS_LIMIT)
    if (response.status) {
      rows.value = response.data?.reports || []
    } else {
      error.value = response.message || REPORTS_ERROR_TEXT
    }
  } catch (e) {
    error.value = getApiErrorMessage(e, REPORTS_ERROR_TEXT)
  } finally {
    loading.value = false
  }
}

/** 取正文并在新窗口打开；HTML 走 blob，不污染当前页样式。 */
async function openReport(row: AgentReportRow) {
  if (!row.report) {
    ElMessage.warning("这次运行没有 HTML 报告")
    return
  }
  openingRun.value = row.run
  try {
    const response = await fetchAgentReport(row.run, row.report)
    const content = response.data?.report?.content || ""
    if (!response.status || !content) {
      ElMessage.error(response.message || REPORTS_OPEN_ERROR_TEXT)
      return
    }
    const url = URL.createObjectURL(new Blob([content], { type: "text/html" }))
    window.open(url, "_blank", "noopener")
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
  } catch (e) {
    ElMessage.error(getApiErrorMessage(e, REPORTS_OPEN_ERROR_TEXT))
  } finally {
    openingRun.value = ""
  }
}

onMounted(load)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell agent-reports-workbench">
    <WorkbenchHeader
      :title="REPORTS_PAGE_TITLE"
      :subtitle="REPORTS_PAGE_SUBTITLE"
      :icon="REPORTS_PAGE_ICON"
      :icon-gradient="REPORTS_PAGE_GRADIENT"
    />

    <div class="doc-body">
      <section class="ar-section" data-testid="agent-reports-page">
        <div class="ar-toolbar">
          <DoodleBtn :disabled="loading" @click="load">{{ REPORTS_REFRESH_LABEL }}</DoodleBtn>
          <span class="ar-count">共 {{ rows.length }} 份报告</span>
        </div>

        <SkeletonCard v-if="loading" :lines="5" />
        <ErrorState v-else-if="error" :message="error" />
        <EmptyState
          v-else-if="!rows.length"
          icon="file-bar-chart"
          :text="REPORTS_EMPTY_TEXT"
          :hint="REPORTS_EMPTY_HINT"
        />
        <div v-else class="ar-grid">
          <DoodleNote
            v-for="(row, index) in rows"
            :key="row.run"
            variant="note"
            accent="var(--c-report)"
            :tilt="tiltFor(index)"
          >
            <div class="ar-note">
              <p class="ar-note__stamp">{{ runStamp(row.run) }}</p>
              <p class="ar-note__run">{{ row.run }}</p>
              <p class="ar-note__meta">
                {{ formatRunTime(row.modified_at) }} · {{ formatBytes(row.bytes) }}
              </p>
              <DoodleBtn :disabled="openingRun === row.run" @click="openReport(row)">
                {{ openingRun === row.run ? REPORTS_LOADING_LABEL : REPORTS_OPEN_LABEL }}
              </DoodleBtn>
            </div>
          </DoodleNote>
        </div>
      </section>
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
