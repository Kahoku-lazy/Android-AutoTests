<script setup lang="ts">
import { computed } from "vue"
import { AGENT_AVATAR_SRC, agentDuty, agentWorkflow } from "../constants"

const props = defineProps<{
  form: Record<string, any>
  taskKind?: string
}>()

const duty = computed(() => agentDuty(props.taskKind))
const workflow = computed(() => agentWorkflow(props.taskKind))
</script>

<template>
  <div class="doc-section step-panel">
    <div class="section-title"><span class="section-num">📋</span>基本信息</div>
    <el-form label-width="100px" class="agent-form">
      <el-form-item label="名称">
        <el-input v-model="form.name" placeholder="例如：平台小助手" />
      </el-form-item>
      <el-form-item label="头像">
        <div class="avatar-row">
          <div class="avatar-preview">
            <img class="avatar-img" :src="AGENT_AVATAR_SRC" alt="智能体头像" />
          </div>
          <span class="avatar-note">系统内置头像，不可修改</span>
        </div>
      </el-form-item>
      <el-form-item label="标签">
        <el-input v-model="form.tags" placeholder="测试,用例,自动化" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          placeholder="智能体职责描述"
        />
      </el-form-item>
      <el-form-item label="职责">
        <el-input :model-value="duty" readonly />
      </el-form-item>
      <el-form-item label="工作流">
        <el-input :model-value="workflow" readonly />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.agent-form :deep(.el-form-item__label) {
  font-size: var(--app-size-md);
  font-weight: 600;
  color: var(--ai-ink-subtle);
}
.agent-form :deep(.el-input__wrapper),
.agent-form :deep(.el-textarea__inner) {
  border-radius: var(--app-radius-md);
  font-size: var(--app-size-md);
}
.avatar-row {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}
.avatar-preview {
  width: 64px;
  height: 64px;
  flex-shrink: 0;
}
.avatar-img {
  display: block;
  width: 100%;
  height: 100%;
}
.avatar-note {
  font-size: var(--app-size-sm);
  color: var(--ai-ink-muted);
}
</style>
