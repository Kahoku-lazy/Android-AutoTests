<script setup lang="ts">
/** DisconnectDialog — 删除局域网设备确认弹窗 */
const props = withDefaults(defineProps<{
  visible?: boolean
  serial?: string
  model?: string
}>(), {
  visible: false,
  serial: '',
  model: '',
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

function handleConfirm() {
  emit('confirm')
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="删除设备"
    width="460px"
    :close-on-click-modal="false"
    @close="handleCancel"
  >
    <div class="disconnect-body">
      <p>
        确定要删除局域网设备
        <strong>{{ serial }}</strong>
        <template v-if="model">({{ model }})</template>
        吗？
      </p>
      <p class="disconnect-warning">删除后该设备将从设备池移除。</p>
    </div>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="danger" @click="handleConfirm">删除</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.disconnect-body { margin-bottom: var(--app-space-md); }
.disconnect-warning {
  background: var(--el-color-warning-light-9);
  padding: 10px; border-radius: 6px; margin-top: var(--app-space-sm);
}
</style>
