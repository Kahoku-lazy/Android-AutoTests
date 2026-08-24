<script setup lang="ts">
defineProps<{ form: Record<string, any>; isNew?: boolean }>()
</script>

<template>
  <div class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">3</span>
      <span>提示词</span>
    </div>
    <el-form label-width="120px" class="agent-form">
      <el-form-item>
        <template #label>
          <span class="label-with-help">系统提示词 <el-tooltip content="定义 AI 的角色和行为。模型每次对话都会先读取这段指令。越具体越好，建议包含角色、能力边界、输出格式。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <div style="display:flex;flex-direction:column;gap:8px;width:100%">
          <el-input v-model="form.system_prompt" type="textarea" :rows="10"
            placeholder="你是一个专业的测试用例编写助手，擅长..." />
        </div>
      </el-form-item>
      <el-form-item>
        <template #label>
          <span class="label-with-help">最大迭代次数 <el-tooltip content="Agent 单次推理的最大轮次（思考→工具调用→思考 算一轮）。值太小可能未完成任务就被截断，值太大可能陷入死循环。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
        </template>
        <el-input-number v-model="form.max_iters" :min="1" :max="100" />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.form-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-left: 10px; }
.label-with-help { display: inline-flex; align-items: center; gap: 4px; }
.help-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--ai-ink-muted); color: var(--app-bg-card);
  font-size:var(--app-size-xs); font-weight: 700; cursor: help;
  opacity: 0.5; transition: opacity 0.15s;
}
.help-icon:hover { opacity: 1; background: var(--app-accent-purple, #b39ef3); }
</style>
