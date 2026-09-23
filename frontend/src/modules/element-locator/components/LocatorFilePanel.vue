<script setup lang="ts">
/**
 * 文件详情面板（只被文件详情页使用）。
 * 元素定位收敛为单一 Android 项目后，叶子类型只有「页面」：直接渲染页面元素工作台。
 */
import { ElMessageBox } from "element-plus"
import type { LocatorFileNode } from "../types"
import PageElementsWorkbench from "./PageElementsWorkbench.vue"

const props = defineProps<{
  file: LocatorFileNode
}>()

const emit = defineEmits<{
  deleteFile: [payload: { fileId: number }]
}>()

async function confirmDelete() {
  try {
    await ElMessageBox.confirm(`确认删除「${props.file.name}」？`, "确认删除", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    })
  } catch {
    return
  }
  emit("deleteFile", { fileId: props.file.id })
}
</script>

<template>
  <section class="file-panel">
    <header class="file-panel__head">
      <div class="file-panel__spacer" />
      <el-button type="danger" @click="confirmDelete">删除</el-button>
    </header>

    <div class="file-panel__body file-panel__body--page">
      <PageElementsWorkbench :page-id="file.id" />
    </div>
  </section>
</template>

<style scoped>
.file-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: var(--app-space-lg);
}
.file-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--app-space-md);
  margin-bottom: var(--app-space-md);
  flex-shrink: 0;
}
.file-panel__spacer {
  flex: 1;
}
.file-panel__body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}
.file-panel__body--page {
  overflow: hidden;
}
</style>
