<script setup>
/** LockDialog — 锁定设备弹窗 per PRD §7.2 */
import { ref, watch } from "vue";
import { ElMessage } from "element-plus";
// el-dialog → el-dialog, Input → el-input, Button → el-button (Element Plus auto-import)
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
  <el-dialog
    :model-value="visible"
    :title="`锁定设备 ${serial}`"
    width="420px"
    :close-on-click-modal="false"
    @close="handleCancel"
  >
    <div class="lock-form">
      <div class="lock-form-item">
        <label class="lock-label">锁定用户 ID *</label>
        <el-input
          v-model="userId"
          placeholder="输入用户标识（如 admin、张三）"
          :maxlength="100"
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
      <el-button @click="handleCancel">取消</el-button>
      <el-button type="primary" @click="handleConfirm"
        >确认锁定</el-button
      >
    </template>
  </el-dialog>
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
  color: var(--app-text);
}

.lock-hint {
  font-size: 12px;
  color: #999;
  margin: 0;
  line-height: 1.4;
}

.lock-select {
  width: 100%;
  padding: 10px 14px;
  font-size: 14px;
  border: 2px solid #A78BFA;
  border-radius: 4px 8px 4px 8px;
  background: #fff;
  color: #2d2d2d;
  font-family: inherit;
  cursor: pointer;
  appearance: auto;
  box-shadow: none;
}
.lock-select:focus {
  outline: none;
  border-color: #A78BFA;
  box-shadow: 0 0 0 3px rgba(167,139,250,0.15);
}

.lock-model-text {
  font-size: 13px;
  color: #999;
}
</style>
