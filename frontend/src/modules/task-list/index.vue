<script setup lang="ts">
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import TaskBoard from "./components/TaskBoard.vue"

const PAGE_HEADER = {
  title: "任务清单",
  subtitle: "AI 任务卡片：新建、筛选、重跑与查看详情",
  icon: "clipboard-list",
  iconGradient: "linear-gradient(135deg, var(--ai-teal), var(--ai-teal-hover))",
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
