<script setup>
defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
  uploading: { type: Boolean, default: false },
})

const emit = defineEmits(['trigger-upload', 'avatar-upload'])
</script>

<template>
  <div v-if="!isNew || step === 1" class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">1</span>
      <span>基本信息</span>
    </div>
    <el-form label-width="100px" class="agent-form">
      <el-form-item label="名称" required>
        <el-input v-model="form.name" placeholder="测试用例编写助手" />
      </el-form-item>
      <el-form-item label="头像">
        <div class="avatar-row">
          <div
            class="avatar-preview"
            :style="
              form.avatar?.startsWith('/api/ai/avatars/')
                ? { backgroundImage: `url(${form.avatar})` }
                : {}
            "
          >
            <span v-if="!form.avatar?.startsWith('/api/ai/avatars/')">{{
              form.avatar || '🤖'
            }}</span>
          </div>
          <el-button :loading="uploading" size="default" @click="emit('trigger-upload')">
            {{ uploading ? '上传中...' : '上传图片' }}
          </el-button>
          <span class="avatar-hint">或直接输入 Emoji 作为头像</span>
        </div>
      </el-form-item>
      <el-form-item label="标签">
        <el-input v-model="form.tags" placeholder="测试,用例,自动化" />
      </el-form-item>
      <el-form-item label="描述">
        <el-input v-model="form.description" type="textarea" :rows="3" placeholder="智能体职责描述" />
      </el-form-item>
    </el-form>
  </div>
</template>

<style scoped>
.avatar-row { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.avatar-preview {
  width: 64px; height: 64px; border-radius: 14px; background-size: cover;
  background-position: center; background-color: var(--ai-warm-bg);
  display: flex; align-items: center; justify-content: center;
  font-size: var(--app-size-2xl); border: 2px solid var(--ai-warm-border); flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(61,52,40,0.08);
}
.avatar-hint { font-size: var(--app-size-sm); color: var(--ai-ink-muted); }
</style>
