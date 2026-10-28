<script setup>
/** 用例编写任务：入库结果卡（成功给跳转，失败/跳过给原因）。 */
defineProps({
  caseImport: { type: Object, default: null },
  isRunning: { type: Boolean, default: false },
})
</script>

<template>
  <section class="flow-import" aria-label="用例入库结果">
    <h2 class="flow-section-title">用例入库结果</h2>
    <template v-if="caseImport?.status === 'imported'">
      <p class="flow-import__summary">
        已写入用例管理，共
        <strong>{{ caseImport.case_count }}</strong>
        条用例
        <span v-if="caseImport.skipped_count">，跳过 {{ caseImport.skipped_count }} 条</span>
      </p>
      <router-link v-if="caseImport.path" class="flow-import__link" :to="caseImport.path">
        打开用例文件
      </router-link>
      <code v-if="caseImport.path" class="flow-import__path">{{ caseImport.path }}</code>
    </template>
    <p v-else-if="caseImport" class="flow-import__message">
      {{ caseImport.message || "未写入用例库" }}
    </p>
    <p v-else-if="isRunning" class="flow-import__message">
      模型正在编写测试用例，完成后自动写入用例管理…
    </p>
    <p v-else class="flow-import__message">这次任务没有写入用例库。</p>
  </section>
</template>

<style scoped>
.flow-import {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  padding: var(--app-space-md) var(--app-space-lg);
  background: var(--paper);
  border: 2.5px dashed var(--ink);
  border-radius: 2px;
  box-shadow: 4px 4px 0 0 var(--c-report);
}

.flow-import__summary,
.flow-import__message {
  margin: 0;
  color: var(--ink);
  font-size: var(--app-size-sm);
  line-height: 1.6;
}

.flow-import__link {
  align-self: flex-start;
  padding: 4px var(--app-space-md);
  color: var(--paper);
  font-size: var(--app-size-sm);
  font-weight: 700;
  text-decoration: none;
  background: var(--ink);
  border: 2px solid var(--ink);
  border-radius: 2px;
}

.flow-import__link:hover {
  color: var(--ink);
  background: var(--paper);
}

.flow-import__path {
  color: var(--app-text-secondary);
  font-family: inherit;
  font-size: var(--app-size-xs);
  overflow-wrap: anywhere;
}
</style>
