<script setup lang="ts">
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import TaskBoard from "./components/TaskBoard.vue"

const PAGE_HEADER = {
  title: "任务清单",
  subtitle: "工作流任务记录：筛选、关闭、重跑与查看报告",
  icon: "clipboard-list",
  iconGradient: "linear-gradient(135deg, var(--c-ai), var(--c-element))",
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell task-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    />

    <div class="doc-body">
      <TaskBoard />
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
