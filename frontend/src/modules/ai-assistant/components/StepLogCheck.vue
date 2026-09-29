<script setup lang="ts">
/**
 * StepLogCheck — 单步尝试的**执行侧**点击证据（只读）。
 *
 * 点击前时间点 + 点击后截图路径（成对、按发生顺序）；本步被标记为需日志核对时，
 * 另嵌入与验收同源的 5 秒窗口证据。无点击且无日志时不渲染（由父组件 v-if 调用方判断）。
 */
import { computed } from "vue"
import StepLogEvidence from "./StepLogEvidence.vue"
import type { TaskLogCheck, TaskLogCheckClick } from "@/shared/types/ai"
import { attemptScreenshotUrl } from "../helpers/task-detail"
import {
  STEP_LOG_CHECK_HINT,
  STEP_LOG_CHECK_NO_SHOT_TEXT,
  STEP_LOG_CHECK_TITLE,
} from "../constants"

const props = defineProps<{ check?: TaskLogCheck }>()

const clicks = computed(() => props.check?.clicks || [])
const log = computed(() => props.check?.log || null)
const hint = computed(() => (log.value ? STEP_LOG_CHECK_HINT : ""))

/** 有落盘截图才有可查看图；无路径返回空串（不猜、不借用其它截图） */
function shotUrl(click: TaskLogCheckClick): string {
  return attemptScreenshotUrl(click.screenshot_path)
}
</script>

<template>
  <section class="slc" data-testid="step-log-check">
    <header class="slc-head">
      <h5 class="slc-title">{{ STEP_LOG_CHECK_TITLE }}</h5>
      <span v-if="hint" class="slc-hint">{{ hint }}</span>
    </header>

    <ol v-if="clicks.length" class="slc-clicks">
      <li v-for="(click, index) in clicks" :key="index" class="slc-click">
        <p class="slc-row">
          <span class="slc-label">点击前时间</span>
          <span class="slc-time">{{ click.action_time || "—" }}</span>
        </p>
        <p class="slc-row">
          <span class="slc-label">点击后截图</span>
          <span v-if="click.screenshot_path" class="slc-path">{{ click.screenshot_path }}</span>
          <span v-else class="slc-none">{{ STEP_LOG_CHECK_NO_SHOT_TEXT }}</span>
        </p>
        <el-image
          v-if="shotUrl(click)"
          :src="shotUrl(click)"
          :preview-src-list="[shotUrl(click)]"
          fit="contain"
          class="slc-img"
          preview-teleported
          data-testid="log-check-screenshot"
        />
      </li>
    </ol>

    <StepLogEvidence v-if="log" :evidence="log" />
  </section>
</template>

<style src="./StepLogCheck.style.css" scoped></style>
