<script setup>
/** NetworkConnectDialog — 局域网（网络）连接设备弹窗 per PRD §3.7 F-07
 * 用户输入 IP 地址 + 端口（默认 5555）→ 前端强校验 → emit confirm({ target })
 * 父组件负责调用 store.doScan(target) 并回填 loading。
 */
import { ref, watch } from "vue";
import { Modal, Input, Button as AnimalButton } from "animal-island-vue";

const props = defineProps({
  visible: { type: Boolean, default: false },
  // 提交中：由父组件在调用 store.doScan 期间置 true，防止重复点击
  loading: { type: Boolean, default: false },
});

const emit = defineEmits(["confirm", "cancel"]);

const ip = ref("");
const port = ref("5555");
const ipError = ref("");
const portError = ref("");

// 每字段 wrapper 引用，用于聚焦第一个非法字段（AC-7）
const ipWrap = ref(null);
const portWrap = ref(null);

// IPv4 点分十进制，每段 0-255（PRD §3.7 校验规则）
const IPV4_RE =
  /^((25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(25[0-5]|2[0-4]\d|[01]?\d?\d)$/;

watch(
  () => props.visible,
  (v) => {
    if (v) {
      ip.value = "";
      port.value = "5555";
      ipError.value = "";
      portError.value = "";
    }
  },
);

function validateIp() {
  const val = ip.value.trim();
  if (!val) {
    ipError.value = "请输入 IP 地址";
    return false;
  }
  if (!IPV4_RE.test(val)) {
    ipError.value = "请输入合法的 IPv4 地址（如 192.168.1.100）";
    return false;
  }
  ipError.value = "";
  return true;
}

function validatePort() {
  const val = String(port.value).trim();
  if (!val) {
    portError.value = "请输入端口";
    return false;
  }
  if (!/^\d+$/.test(val)) {
    portError.value = "端口需为 1-65535 之间的整数";
    return false;
  }
  const num = Number(val);
  if (num < 1 || num > 65535) {
    portError.value = "端口需为 1-65535 之间的整数";
    return false;
  }
  portError.value = "";
  return true;
}

function focusField(wrap) {
  // animal-island Input 未暴露 focus 方法，直接定位内部原生 input
  wrap?.querySelector?.("input")?.focus?.();
}

function handleConfirm() {
  if (props.loading) return; // 提交中防重复（AC-9）
  const ipOk = validateIp();
  const portOk = validatePort();
  // 任一不通过则不发请求，聚焦第一个非法字段（AC-5/6/7）
  if (!ipOk) {
    focusField(ipWrap.value);
    return;
  }
  if (!portOk) {
    focusField(portWrap.value);
    return;
  }
  emit("confirm", {
    target: `${ip.value.trim()}:${String(port.value).trim()}`,
  });
}

function handleCancel() {
  if (props.loading) return;
  emit("cancel");
}
</script>

<template>
  <Modal
    :open="visible"
    title="局域网连接设备"
    width="440px"
    :mask-closable="false"
    @close="handleCancel"
  >
    <div class="net-form">
      <div class="net-form-item">
        <label class="net-label">IP 地址 *</label>
        <div
          ref="ipWrap"
          class="net-field"
          :class="{ 'has-error': ipError }"
          @focusout="validateIp"
        >
          <Input
            v-model="ip"
            placeholder="如 192.168.1.100"
            :maxlength="15"
            :shadow="true"
            size="middle"
            @keyup.enter="handleConfirm"
          />
        </div>
        <p v-if="ipError" class="net-error">{{ ipError }}</p>
      </div>

      <div class="net-form-item">
        <label class="net-label">端口 *</label>
        <div
          ref="portWrap"
          class="net-field"
          :class="{ 'has-error': portError }"
          @focusout="validatePort"
        >
          <Input
            v-model="port"
            placeholder="默认 5555"
            :maxlength="5"
            :shadow="true"
            size="middle"
            @keyup.enter="handleConfirm"
          />
        </div>
        <p v-if="portError" class="net-error">{{ portError }}</p>
      </div>

      <p class="net-hint">请确保设备已开启无线调试，且与本机处于同一局域网。</p>
    </div>

    <template #footer>
      <AnimalButton :disabled="loading" @click="handleCancel"
        >取消</AnimalButton
      >
      <AnimalButton type="primary" :loading="loading" @click="handleConfirm"
        >连接</AnimalButton
      >
    </template>
  </Modal>
</template>

<style scoped>
.net-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 8px 0;
}

.net-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.net-label {
  font-size: 14px;
  font-weight: 700;
  color: #794f27;
}

.net-field.has-error :deep(input) {
  border-color: #e05a5a;
  box-shadow: 0 0 0 3px rgba(224, 90, 90, 0.12);
}

.net-error {
  font-size: 12px;
  color: #e05a5a;
  margin: 0;
  line-height: 1.4;
}

.net-hint {
  font-size: 12px;
  color: #9f927d;
  margin: 4px 0 0;
  line-height: 1.5;
}
</style>
