<script setup>
/** DisconnectDialog — 强制断开确认弹窗 per PRD §7.2 */
import { ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Modal, Button as AnimalButton } from 'animal-island-vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  serial: { type: String, default: '' },
  model: { type: String, default: '' },
  status: { type: String, default: '' },
  lockedBy: { type: String, default: '' },
  isBusyOthers: { type: Boolean, default: false },
})

const emit = defineEmits(['confirm', 'cancel'])

const reason = ref('')

const title = computed(() => {
  if (props.isBusyOthers) return '⚠️ 强制断开设备（管理员操作）'
  return '⚠️ 断开设备'
})

watch(() => props.visible, (v) => {
  if (v) reason.value = ''
})

function handleConfirm() {
  if (props.isBusyOthers && !reason.value.trim()) {
    ElMessage.warning('强制断开他人设备时必须填写原因')
    return
  }
  emit('confirm', { reason: reason.value.trim() })
}

function handleCancel() {
  emit('cancel')
}
</script>

<template>
  <Modal
    :open="visible"
    :title="title"
    width="460px"
    :mask-closable="false"
    @close="handleCancel"
  >
    <div style="margin-bottom:16px">
      <p>
        确定要断开
        <strong>{{ serial }}</strong>
        <template v-if="model">({{ model }})</template>
        吗？
      </p>
      <p v-if="isBusyOthers" style="background:var(--el-color-warning-light-9);padding:10px;border-radius:6px;margin-top:8px">
        该设备状态：<el-tag type="warning" size="small">BUSY</el-tag>
        锁定者：<strong>{{ lockedBy }}</strong><br />
        断开后该设备所有锁将被<strong>强制释放</strong>。
      </p>
    </div>

    <el-form label-width="80px">
      <el-form-item
        :label="isBusyOthers ? '断开原因*' : '断开原因'"
        :required="isBusyOthers"
      >
        <el-input
          v-model="reason"
          type="textarea"
          :rows="2"
          :placeholder="isBusyOthers ? '请填写强制断开的原因' : '可选填写断开原因'"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <AnimalButton @click="handleCancel">取消</AnimalButton>
      <AnimalButton type="primary" danger @click="handleConfirm">
        {{ isBusyOthers ? '强制断开' : '确认断开' }}
      </AnimalButton>
    </template>
  </Modal>
</template>
