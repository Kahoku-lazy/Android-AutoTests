<script setup>
defineProps({ element: { type: Object, default: null } })
</script>

<template>
  <div class="panel">
    <template v-if="element">
      <h3>XPath 筛选</h3>
      <div class="meta">
        <p><strong>Class:</strong> {{ element.class_name }}</p>
        <p v-if="element.text"><strong>Text:</strong> {{ element.text }}</p>
        <p v-if="element.resource_id"><strong>ID:</strong> {{ element.resource_id }}</p>
        <p v-if="element.content_desc"><strong>Desc:</strong> {{ element.content_desc }}</p>
        <p><strong>Bounds:</strong> {{ element.bounds }}</p>
        <p v-if="element.clickable != null">
          <strong>Clickable:</strong> {{ element.clickable ? '是' : '否' }}
        </p>
      </div>
    </template>
    <template v-else>
      <h3>待定页面</h3>
      <div class="placeholder">
        <span class="placeholder-label">待定页面</span>
        <p class="hint">选中元素后，此处显示 XPath 筛选信息</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.panel {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  background: var(--glass-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  padding: 16px;
  box-shadow: var(--shadow);
  overflow-y: auto;
}
h3 {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 12px;
  flex-shrink: 0;
}
.meta {
  font-size: 12px;
  line-height: 1.6;
}
.meta p {
  margin-bottom: 6px;
  color: var(--text-secondary);
  word-break: break-all;
}
.meta strong {
  color: var(--text-primary);
}
.placeholder {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
.placeholder-label {
  font-size: 15px;
  color: var(--text-secondary);
  opacity: 0.6;
}
.hint {
  margin-top: 8px;
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.5;
}
</style>
