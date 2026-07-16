<script setup>
/** LockDialog — 锁定设备弹窗 per PRD §7.2 */
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
import { Modal, Input, Button as AnimalButton } from "animal-island-vue";
import { useRawStorage } from "@/shared/composables/useStorage.js";

const props = defineProps({
  visible: { type: Boolean, default: false },
  serial: { type: String, default: "" },
  model: { type: String, default: "" },
});

const emit = defineEmits(["confirm", "cancel"]);

const savedUserId = useRawStorage("dp_user_id", "");
const userId = ref("");
const timeout = ref(300);

watch(
  () => props.visible,
  (v) => {
    if (v) {
      userId.value = savedUserId.value || "";
      timeout.value = 300;
    }
  },
);

function handleConfirm() {
  if (!userId.value.trim()) {
    ElMessage.warning("请输入锁定用户 ID（用于标识是谁占用了设备）");
    return;
  }
  emit("confirm", {
    userId: userId.value.trim(),
    timeout: timeout.value,
  });
}

function handleCancel() {
  emit("cancel");
}
</script>

<template>
  <Modal
    :open="visible"
    :title="`锁定设备 ${serial}`"
    width="420px"
    :mask-closable="false"
    @close="handleCancel"
  >
    <div class="lock-form">
      <div class="lock-form-item">
        <label class="lock-label">锁定用户 ID *</label>
        <Input
          v-model="userId"
          placeholder="输入用户标识（如 admin、张三）"
          :maxlength="100"
          :shadow="true"
          size="middle"
        />
        <p class="lock-hint">
          此 ID 用于标识设备当前被谁占用，其他用户将看到占用信息
        </p>
      </div>

      <div class="lock-form-item">
        <label class="lock-label">锁定时长</label>
        <div class="lock-timeout-row">
          <select v-model="timeout" class="lock-select">
            <option :value="60">1 分钟</option>
            <option :value="300">5 分钟</option>
            <option :value="600">10 分钟</option>
            <option :value="1800">30 分钟</option>
            <option :value="3600">1 小时</option>
          </select>
        </div>
      </div>

      <div v-if="model" class="lock-form-item">
        <label class="lock-label">设备型号</label>
        <span class="lock-model-text">{{ model }}</span>
      </div>
    </div>

    <template #footer>
      <AnimalButton @click="handleCancel">取消</AnimalButton>
      <AnimalButton type="primary" @click="handleConfirm"
        >确认锁定</AnimalButton
      >
    </template>
  </Modal>
</template>

<style scoped>
.lock-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 8px 0;
}

.lock-form-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lock-label {
  font-size: 14px;
  font-weight: 700;
  color: #794f27;
}

.lock-hint {
  font-size: 12px;
  color: #9f927d;
  margin: 0;
  line-height: 1.4;
}

.lock-select {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  border: 1.5px solid #e8dcc8;
  border-radius: 10px;
  background: #fffaf5;
  color: #794f27;
  font-family: inherit;
  cursor: pointer;
  appearance: auto;
}

.lock-select:focus {
  outline: none;
  border-color: #889df0;
  box-shadow: 0 0 0 3px rgba(136, 157, 240, 0.12);
}

.lock-model-text {
  font-size: 13px;
  color: #9f927d;
}
</style>
