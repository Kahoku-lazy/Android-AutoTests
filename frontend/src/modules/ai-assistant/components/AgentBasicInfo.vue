<script setup lang="ts">
import { DATA_IMAGE_PREFIX } from '../constants'

defineProps<{
  form: Record<string, any>
  isNew?: boolean
  uploading?: boolean
  /** 线路级：仅名称/头像；平台级：标签/描述 */
  routeMode?: boolean
}>()
const emit = defineEmits<{ 'trigger-upload': [] }>()
</script>

<template>
  <div class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">{{ routeMode ? '👤' : '📋' }}</span>
      {{ routeMode ? '基本信息' : '平台信息' }}
    </div>
    <el-form label-width="100px" class="agent-form">
      <template v-if="routeMode">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="例如：控制设备助手" />
        </el-form-item>
        <el-form-item label="头像">
          <div class="avatar-row">
            <div
              class="avatar-preview"
              :style="
                form.avatar?.startsWith(DATA_IMAGE_PREFIX)
                  ? { backgroundImage: `url(${form.avatar})` }
                  : {}
              "
            >
              <span v-if="!form.avatar?.startsWith(DATA_IMAGE_PREFIX)">{{
                form.avatar || '🤖'
              }}</span>
            </div>
            <el-button :loading="uploading" size="default" @click="emit('trigger-upload')">
              {{ uploading ? '上传中...' : '上传图片' }}
            </el-button>
            <el-input v-model="form.avatar" placeholder="Emoji 或留空用默认" style="max-width:160px" />
          </div>
        </el-form-item>
      </template>
      <template v-else>
        <el-form-item label="标签">
          <el-input v-model="form.tags" placeholder="测试,用例,自动化" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="智能体职责描述" />
        </el-form-item>
      </template>
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
</style>
